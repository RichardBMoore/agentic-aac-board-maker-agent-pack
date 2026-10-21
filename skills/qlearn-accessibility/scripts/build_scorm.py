#!/usr/bin/env python3
"""Package an existing, validated standalone HTML activity as a SCORM 1.2 ZIP.

The activity itself is not changed. The launch page is the original file with
one extra line before ``</body>`` that loads ``scorm/scorm12-bridge.js``; the
bridge only tells the LMS the activity opened and closed. ``validate_scorm.py
--source`` proves this byte-for-byte.

Layouts:

- ``inline`` (default): the original single file, unchanged apart from the
  bridge line. Closest to the tested standalone file.
- ``split``: moves inline ``<style>`` blocks and executable inline
  ``<script>`` blocks into files under ``assets/`` (JSON data blocks stay
  inline). Behaviour is identical; use it only if the LMS player's Content
  Security Policy blocks inline scripts (the activity shows a blank or
  unstyled page inside QLearn).

The ZIP is deterministic: the same input always produces the same bytes.

Examples:

    python3 build_scorm.py generated/gaze-choice-2x2/gaze-choice-class-activity.html dist/gaze-choice.scorm12.zip
    python3 build_scorm.py board.html board.split.scorm12.zip --layout split
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import string
import sys
import tempfile
import zipfile
from html import unescape
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

try:
    import validate_scorm
except ModuleNotFoundError:  # Supports importlib-based unit tests.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import validate_scorm

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SKILLS_DIR = SKILL_DIR.parent
BRIDGE_SOURCE = SKILL_DIR / "assets" / "scorm12-bridge.js"
MANIFEST_TEMPLATE = SKILL_DIR / "templates" / "scorm12_manifest.xml"
HOUSE_SYMBOL_LICENCE = SKILLS_DIR / "agentic-aac-board-maker" / "assets" / "house-symbols" / "LICENCE.md"

LAUNCH = "index.html"
BRIDGE_PATH = "scorm/scorm12-bridge.js"
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_MODE = 0o100644 << 16
PACKAGE_FORMAT = "agentic-aac-scorm-package"
PACKAGE_FORMAT_VERSION = 1

BLOCK_RE = re.compile(
    r"(?P<script><script\b(?P<script_attrs>[^>]*)>(?P<script_body>.*?)(?P<script_close></script\s*>))"
    r"|(?P<style><style\b(?P<style_attrs>[^>]*)>(?P<style_body>.*?)(?P<style_close></style\s*>))",
    re.IGNORECASE | re.DOTALL,
)
TYPE_ATTR = re.compile(r"\btype\s*=\s*([\"'])(?P<type>[^\"']*)\1", re.IGNORECASE)
MEDIA_ATTR = re.compile(r"\bmedia\s*=\s*([\"'])(?P<media>[^\"']*)\1", re.IGNORECASE)
JS_TYPES = {"", "text/javascript", "application/javascript", "module", "text/ecmascript", "application/ecmascript"}
BODY_CLOSE = re.compile(r"</body\s*>", re.IGNORECASE)
TITLE_RE = re.compile(r"<title[^>]*>(?P<title>.*?)</title\s*>", re.IGNORECASE | re.DOTALL)
RUNTIME_SHA = re.compile(r"data-runtime-sha256=\"(?P<sha>[0-9a-f]{64})\"")


class PackagingError(RuntimeError):
    """Raised when a source activity is not safe or not suitable to package."""


def bridge_tag(report_completion: bool) -> str:
    flag = "true" if report_completion else "false"
    return f'<script src="{BRIDGE_PATH}" data-report-completion="{flag}"></script>\n'


def insert_bridge(text: str, report_completion: bool) -> str:
    matches = list(BODY_CLOSE.finditer(text))
    tag = bridge_tag(report_completion)
    if not matches:
        raise PackagingError("the activity has no </body> tag to place the SCORM bridge before")
    position = matches[-1].start()
    return text[:position] + tag + text[position:]


def split_inline_assets(text: str) -> tuple[str, dict[str, bytes], list[dict[str, str]]]:
    """Move inline CSS and executable JS into files; return new text, files and the reversal map."""
    files: dict[str, bytes] = {}
    split_map: list[dict[str, str]] = []
    pieces: list[str] = []
    cursor = 0
    style_count = 0
    script_count = 0
    for match in BLOCK_RE.finditer(text):
        pieces.append(text[cursor:match.start()])
        cursor = match.end()
        if match.group("script"):
            attrs = match.group("script_attrs")
            type_match = TYPE_ATTR.search(attrs)
            script_type = (type_match.group("type") if type_match else "").strip().lower()
            if re.search(r"\bsrc\s*=", attrs, re.IGNORECASE) or script_type not in JS_TYPES or not match.group("script_body").strip():
                pieces.append(match.group(0))
                continue
            script_count += 1
            path = f"assets/inline-script-{script_count}.js"
            open_tag = f"<script{attrs}>"
            replacement = f'<script{attrs} src="{path}"></script>'
            files[path] = match.group("script_body").encode("utf-8")
            split_map.append({"file": path, "openTag": open_tag, "closeTag": match.group("script_close"), "replacement": replacement})
            pieces.append(replacement)
        else:
            attrs = match.group("style_attrs")
            style_count += 1
            path = f"assets/inline-style-{style_count}.css"
            media = MEDIA_ATTR.search(attrs)
            media_attr = f' media="{media.group("media")}"' if media else ""
            replacement = f'<link rel="stylesheet" href="{path}"{media_attr} data-aac-split="style-{style_count}">'
            files[path] = match.group("style_body").encode("utf-8")
            split_map.append({"file": path, "openTag": f"<style{attrs}>", "closeTag": match.group("style_close"), "replacement": replacement})
            pieces.append(replacement)
    pieces.append(text[cursor:])
    return "".join(pieces), files, split_map


def slug_identifier(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "activity"
    if not re.match(r"[a-z_]", slug):
        slug = f"aac-{slug}"
    return slug[:60].rstrip("-")


def activity_title(text: str, fallback: str) -> str:
    match = TITLE_RE.search(text)
    title = unescape(re.sub(r"\s+", " ", match.group("title"))).strip() if match else ""
    return title or fallback


def render_manifest(identifier: str, title: str, file_names: list[str], schemas: bool) -> bytes:
    template = string.Template(MANIFEST_TEMPLATE.read_text(encoding="utf-8"))
    schema_location = ""
    if schemas:
        schema_location = (
            '\n  xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd'
            " http://www.imsglobal.org/xsd/imsmd_rootv1p2p1 imsmd_rootv1p2p1.xsd"
            ' http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd"'
        )
    entries = "\n".join(f"      <file href={quoteattr(name)}/>" for name in file_names)
    manifest = template.substitute(
        manifest_id=f"{identifier}-manifest",
        organization_id=f"{identifier}-org",
        item_id=f"{identifier}-item",
        resource_id=f"{identifier}-sco",
        title=escape(title),
        launch_href=LAUNCH,
        schema_location=schema_location,
        file_entries=entries,
    )
    return manifest.encode("utf-8")


def write_deterministic_zip(path: Path, entries: dict[str, bytes]) -> None:
    names = ["imsmanifest.xml"] + sorted(name for name in entries if name != "imsmanifest.xml")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".zip.tmp", delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        with zipfile.ZipFile(temp_path, "w") as archive:
            for name in names:
                info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = FILE_MODE
                archive.writestr(info, entries[name], compresslevel=9)
        os.chmod(temp_path, 0o644)  # Temp files start owner-only; a package is meant to be shared.
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def collect_includes(source: Path, includes: list[str]) -> dict[str, bytes]:
    base = source.parent.resolve()
    files: dict[str, bytes] = {}
    for include in includes:
        candidate = (base / include).resolve()
        if base not in candidate.parents and candidate != base:
            raise PackagingError(f"--include {include} is outside the activity's folder")
        paths = sorted(p for p in candidate.rglob("*") if p.is_file()) if candidate.is_dir() else [candidate]
        for item in paths:
            if not item.exists():
                raise PackagingError(f"--include {include} does not exist")
            relative = item.relative_to(base).as_posix()
            if validate_scorm.is_junk(relative):
                continue
            files[relative] = item.read_bytes()
    return files


def build_package(
    source: Path,
    output: Path,
    *,
    title: str | None = None,
    identifier: str | None = None,
    layout: str = "inline",
    report_completion: bool = False,
    schemas_dir: Path | None = None,
    includes: list[str] | None = None,
) -> dict:
    """Build the SCORM ZIP and return package-info metadata. Raises PackagingError on unsafe input."""
    raw = source.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PackagingError(f"{source.name} is not UTF-8 text: {error}") from None

    preflight = validate_scorm.Report()
    validate_scorm.scan_source_text(text, preflight, source.name)
    external = validate_scorm.html_external_assets(text)
    if external:
        preflight.fail(f"{source.name} loads from the internet ({external[:3]}); make it self-contained first")
    if preflight.failures:
        raise PackagingError("; ".join(preflight.failures))

    identifier = slug_identifier(identifier or source.stem.removesuffix(".html"))
    title = title or activity_title(text, source.stem)
    entries: dict[str, bytes] = {}
    split_map: list[dict[str, str]] = []
    launch_text = text
    if layout == "split":
        launch_text, split_files, split_map = split_inline_assets(text)
        entries.update(split_files)
    elif layout != "inline":
        raise PackagingError(f"unknown layout '{layout}' (use inline or split)")
    launch_text = insert_bridge(launch_text, report_completion)
    entries[LAUNCH] = launch_text.encode("utf-8")
    entries[BRIDGE_PATH] = BRIDGE_SOURCE.read_bytes()

    for name, data in collect_includes(source, includes or []).items():
        if name in entries:
            raise PackagingError(f"--include {name} clashes with a generated package file")
        entries[name] = data

    if "ARASAAC" in text and HOUSE_SYMBOL_LICENCE.exists():
        entries["licences/ARASAAC-symbols-LICENCE.md"] = HOUSE_SYMBOL_LICENCE.read_bytes()

    schemas = False
    if schemas_dir is not None:
        for schema_name in validate_scorm.SCHEMA_FILES:
            schema_path = schemas_dir / schema_name
            if not schema_path.is_file():
                raise PackagingError(f"--schemas-dir is missing {schema_name}")
            entries[schema_name] = schema_path.read_bytes()
        schemas = True

    runtime = RUNTIME_SHA.search(text)
    info = {
        "format": PACKAGE_FORMAT,
        "formatVersion": PACKAGE_FORMAT_VERSION,
        "scormVersion": "1.2",
        "title": title,
        "identifier": identifier,
        "launch": LAUNCH,
        "layout": layout,
        "source": {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "aacRuntimeSha256": runtime.group("sha") if runtime else None,
        },
        "bridge": {"file": BRIDGE_PATH, "reportCompletion": report_completion, "sendsStudentData": False},
        "split": split_map,
        "verify": "python3 validate_scorm.py <package.zip> --source <original.html>",
        "builtBy": "skills/qlearn-accessibility/scripts/build_scorm.py",
    }
    entries["package-info.json"] = (json.dumps(info, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    listed = [LAUNCH] + sorted(name for name in entries if name not in (LAUNCH,) and name not in validate_scorm.SCHEMA_FILES)
    entries["imsmanifest.xml"] = render_manifest(identifier, title, listed, schemas)
    write_deterministic_zip(output, entries)

    report = validate_scorm.validate_package(output, source)
    if not report.success:
        output.unlink(missing_ok=True)
        raise PackagingError("built package failed validation: " + "; ".join(report.failures))
    info["zipSha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    info["validation"] = report.as_dict()
    return info


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package a standalone HTML activity as a SCORM 1.2 ZIP for QLearn/Canvas.")
    parser.add_argument("source", type=Path, help="validated standalone HTML activity (for example a render_html.py board)")
    parser.add_argument("output", type=Path, help="ZIP to write, for example dist/activity.scorm12.zip")
    parser.add_argument("--title", help="title shown in the LMS (default: the page <title>)")
    parser.add_argument("--identifier", help="anonymous slug for manifest identifiers (default: from the file name)")
    parser.add_argument("--layout", choices=("inline", "split"), default="inline", help="inline (default) or split for strict player CSPs")
    parser.add_argument("--report-completion", action="store_true", help="tell the LMS the activity is 'completed' when it opens (off by default)")
    parser.add_argument("--schemas-dir", type=Path, help="folder holding the four official SCORM 1.2 .xsd files to bundle")
    parser.add_argument("--include", action="append", default=[], help="extra file/folder (relative to the activity) the page needs")
    args = parser.parse_args(argv)
    try:
        info = build_package(
            args.source,
            args.output,
            title=args.title,
            identifier=args.identifier,
            layout=args.layout,
            report_completion=args.report_completion,
            schemas_dir=args.schemas_dir,
            includes=args.include,
        )
    except PackagingError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    validation = info["validation"]
    for message in validation["passes"]:
        print(f"PASS: {message}")
    for message in validation["notes"]:
        print(f"NOTE: {message}")
    for message in validation["warnings"]:
        print(f"WARN: {message}")
    print(f"Built {args.output} ({args.output.stat().st_size:,} bytes, layout={args.layout}, sha256={info['zipSha256'][:16]}…)")
    print(f"Title in QLearn: {info['title']}")
    print("Next: upload it through the course's SCORM tool as a page (see references/teacher-scorm-upload-guide.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

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
  inline), keeping every attribute. Use it only if the LMS player's Content
  Security Policy blocks inline scripts (the activity shows a blank or
  unstyled page inside QLearn). To keep behaviour the same, the builder
  refuses split layout for inline scripts marked ``async``/``defer`` and for
  ``<style>``/``<script>`` inside ``<svg>``, ``<math>``, ``<textarea>``,
  ``<template>``, ``<noscript>`` or ``<title>``; use the inline layout then.

The ZIP is deterministic for a given input and Python/zlib build.

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
from html.parser import HTMLParser
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

JS_TYPES = {"", "text/javascript", "application/javascript", "module", "text/ecmascript", "application/ecmascript"}
BODY_CLOSE = re.compile(r"</body\s*>", re.IGNORECASE)
FOREIGN_OR_TEXT_CONTAINERS = {"svg", "math", "textarea", "template", "noscript", "title", "xmp", "iframe", "noembed", "noframes"}
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


class _BlockFinder(HTMLParser):
    """Locate <style>/<script> elements exactly (offsets, raw tags, context) with a real HTML tokenizer."""

    def __init__(self, text: str) -> None:
        super().__init__(convert_charrefs=False)
        self.text = text
        self.line_starts = [0] + [index + 1 for index, character in enumerate(text) if character == "\n"]
        self.blocks: list[dict] = []
        self.containers: list[str] = []
        self.current: dict | None = None

    def position(self) -> int:
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            start = self.position()
            raw = self.get_starttag_text() or ""
            if self.text[start:start + len(raw)] != raw:
                raise PackagingError("could not locate a <script>/<style> tag exactly; use the inline layout")
            self.current = {
                "kind": tag, "start": start, "open_end": start + len(raw), "open_tag": raw,
                "attrs": {name.lower(): value for name, value in attrs}, "contained": list(self.containers),
            }
        elif tag in FOREIGN_OR_TEXT_CONTAINERS:
            self.containers.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            raise PackagingError(f"self-closing <{tag}/> found; use the inline layout")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self.current and self.current["kind"] == tag:
            close_start = self.position()
            close_end = self.text.index(">", close_start) + 1
            self.current.update({"close_start": close_start, "close_end": close_end})
            self.blocks.append(self.current)
            self.current = None
        elif tag in self.containers:
            while self.containers and self.containers.pop() != tag:
                pass


def split_inline_assets(text: str) -> tuple[str, dict[str, bytes], list[dict[str, str]]]:
    """Move inline CSS and executable JS into files; return new text, files and the reversal map."""
    finder = _BlockFinder(text)
    finder.feed(text)
    finder.close()
    files: dict[str, bytes] = {}
    split_map: list[dict[str, str]] = []
    pieces: list[str] = []
    cursor = 0
    counts = {"script": 0, "style": 0}
    for block in finder.blocks:
        kind, attrs = block["kind"], block["attrs"]
        body = text[block["open_end"]:block["close_start"]]
        if kind == "script":
            script_type = (attrs.get("type") or "").strip().lower()
            if "src" in attrs or script_type not in JS_TYPES or not body.strip():
                continue  # already external, or a data block (e.g. the board's JSON IR): leave untouched
            if "async" in attrs or "defer" in attrs:
                raise PackagingError("an inline <script> is marked async/defer, which would start working once moved; use the inline layout")
        if block["contained"]:
            raise PackagingError(f"a <{kind}> sits inside <{block['contained'][-1]}>, where moving it would change behaviour; use the inline layout")
        counts[kind] += 1
        open_tag = block["open_tag"]
        attribute_text = open_tag[len(kind) + 1:-1]  # everything between "<script"/"<style" and ">", verbatim
        if kind == "script":
            path = f"assets/inline-script-{counts[kind]}.js"
            replacement = f'<script{attribute_text} src="{path}"></script>'
        else:
            path = f"assets/inline-style-{counts[kind]}.css"
            replacement = f'<link rel="stylesheet" href="{path}"{attribute_text} data-aac-split="style-{counts[kind]}">'
        pieces.append(text[cursor:block["start"]])
        pieces.append(replacement)
        cursor = block["close_end"]
        files[path] = body.encode("utf-8")
        split_map.append({"file": path, "openTag": open_tag, "closeTag": text[block["close_start"]:block["close_end"]], "replacement": replacement})
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
    notes: list[str] = []
    if layout == "split":
        launch_text, split_files, split_map = split_inline_assets(text)
        entries.update(split_files)
        collector = validate_scorm.AssetCollector()
        collector.feed(text)
        if collector.inline_style_attributes:
            notes.append(f"{collector.inline_style_attributes} inline style=\"…\" attribute(s) remain; a player that also forbids inline styles would ignore them (layout still usable in the strict-CSP browser test)")
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
        "notes": notes,
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
    report.notes.extend(notes)
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

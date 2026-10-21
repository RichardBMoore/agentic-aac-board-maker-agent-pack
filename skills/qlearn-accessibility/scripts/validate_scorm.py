#!/usr/bin/env python3
"""Validate a SCORM 1.2 package (ZIP) before a teacher uploads it to QLearn/Canvas.

Checks the things that make an LMS reject or half-load a package, plus the
pack's own safety rules:

- ZIP hygiene: imsmanifest.xml at the root, no absolute or ``..`` paths, no
  symlinks, duplicates, encrypted entries or junk (``__MACOSX``, ``.DS_Store``,
  ``.env``, ``.git``).
- Manifest: SCORM 1.2 namespaces and schemaversion, unique XML identifiers, a
  default organisation whose items point at real resources, a launchable SCO,
  every ``<file>`` present and every packaged file listed.
- Launch page: every local asset resolves inside the package and nothing loads
  from the internet (school filters and offline devices break those).
- Safety: no access tokens, bearer credentials or private keys; no calls to
  LMS/Canvas API endpoints; network calls are flagged; embedded AAC Board IR
  must not be marked as containing sensitive data.
- Optional ``--source``: prove the packaged activity is the original file plus
  only the SCORM bridge (byte-for-byte), so packaging cannot change behaviour.

Exit status is 0 when there are no FAIL lines.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import stat
import sys
import zipfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree

CP_NS = "http://www.imsproject.org/xsd/imscp_rootv1p1p2"
ADLCP_NS = "http://www.adlnet.org/xsd/adlcp_rootv1p2"
CP2004_NS = "http://www.imsglobal.org/xsd/imscp_v1p1"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_FILES = ("imscp_rootv1p1p2.xsd", "adlcp_rootv1p2.xsd", "ims_xml.xsd", "imsmd_rootv1p2p1.xsd")

TEXT_SUFFIXES = {".html", ".htm", ".js", ".mjs", ".css", ".json", ".xml", ".txt", ".md", ".svg", ".csv"}
SCRIPT_SUFFIXES = {".html", ".htm", ".js", ".mjs"}
JUNK_PARTS = {"__MACOSX", ".git", "node_modules", ".venv", "__pycache__"}
JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini", ".env", ".npmrc", ".netrc"}
NCNAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*$")
MAX_TOTAL_BYTES_WARN = 100 * 1024 * 1024

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("a Canvas/QLearn access token", re.compile(r"(?<![A-Za-z0-9])\d{1,8}~[A-Za-z0-9]{40,}")),
    ("a bearer credential", re.compile(r"Bearer\s+[A-Za-z0-9~._\-]{20,}")),
    ("an access_token parameter", re.compile(r"access_token=[A-Za-z0-9~._\-]{10,}")),
    ("a private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("an AWS access key", re.compile(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])")),
    ("a GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}")),
)
API_ENDPOINT = re.compile(r"/api/v1/|instructure\.com/api|/login/oauth2", re.IGNORECASE)
NETWORK_CALLS = re.compile(r"\bfetch\s*\(|XMLHttpRequest|navigator\.sendBeacon|new\s+WebSocket|new\s+EventSource")
CSS_URL = re.compile(r"url\(\s*(['\"]?)(?P<url>[^)'\"]+)\1\s*\)", re.IGNORECASE)
CSS_IMPORT = re.compile(r"@import\s+(['\"])(?P<url>[^'\"]+)\1", re.IGNORECASE)
# Any absolute internet address in CSS/JS text (image-set('https…'), import('https…'), new Image().src…),
# except XML namespace identifiers, which are names rather than downloads.
INTERNET_ADDRESS = re.compile(r"(?:https?:)?//(?!www\.w3\.org/)[A-Za-z0-9.-]+\.[A-Za-z]{2,}[^\s'\"`)<>]*", re.IGNORECASE)
JS_URL_LITERAL = re.compile(r"['\"`](?P<url>https?://(?!www\.w3\.org/)[^'\"`\s]+)['\"`]", re.IGNORECASE)
JS_REMOTE_IMPORT = re.compile(r"\bimport\s*\(\s*['\"`]https?://|\bimport\s+[^;]*?\bfrom\s*['\"]https?://|importScripts\s*\(", re.IGNORECASE)
META_REFRESH_URL = re.compile(r"url\s*=\s*['\"]?(?P<url>[^'\";\s]+)", re.IGNORECASE)
EMBEDDED_IR = re.compile(r"<script\b[^>]*\bid=[\"']aac-board-ir[\"'][^>]*>(?P<json>.*?)</script\s*>", re.IGNORECASE | re.DOTALL)
BRIDGE_TAG_RE = re.compile(
    r"<script src=\"(?:\.\./)*scorm/scorm12-bridge\.js\" data-report-completion=\"(?:true|false)\"(?: data-multi-page=\"true\")?></script>\n"
    # Optional Full screen / Exit full screen button (build_scorm.py --fullscreen-toggle), always straight after the bridge.
    r"(?:<script src=\"(?:\.\./)*scorm/fullscreen-toggle\.js\" data-position=\"(?:top-left|top-center|top-right|middle-left|middle-right|bottom-left|bottom-center|bottom-right)\"></script>\n)?"
)

# Attributes that load something into the page (as opposed to <a href>, which is navigation).
ASSET_ATTRIBUTES = {
    "script": ("src",),
    "link": ("href",),
    "img": ("src", "srcset"),
    "source": ("src", "srcset"),
    "video": ("src", "poster"),
    "audio": ("src",),
    "track": ("src",),
    "iframe": ("src",),
    "frame": ("src",),
    "embed": ("src",),
    "object": ("data",),
    "input": ("src",),
    "base": ("href",),
    "image": ("href", "xlink:href"),  # SVG
    "use": ("href", "xlink:href"),    # SVG
    "feimage": ("href", "xlink:href"),
}
JS_TYPES = {"", "text/javascript", "application/javascript", "module", "text/ecmascript", "application/ecmascript"}


def srcset_urls(value: str) -> list[str]:
    """URLs in a srcset, keeping data: URIs whole (they contain commas but no spaces)."""
    urls: list[str] = []
    expecting_url = True
    for token in value.split():
        if expecting_url:
            urls.append(token.rstrip(","))
            expecting_url = token.endswith(",")
        else:
            expecting_url = token.endswith(",")
    return [url for url in urls if url]


@dataclass
class Report:
    passes: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def ok(self, message: str) -> None:
        self.passes.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def fail(self, message: str) -> None:
        self.failures.append(message)

    @property
    def success(self) -> bool:
        return not self.failures

    def print(self, stream=sys.stdout) -> None:
        for message in self.passes:
            print(f"PASS: {message}", file=stream)
        for message in self.notes:
            print(f"NOTE: {message}", file=stream)
        for message in self.warnings:
            print(f"WARN: {message}", file=stream)
        for message in self.failures:
            print(f"FAIL: {message}", file=stream)

    def as_dict(self) -> dict[str, list[str] | bool]:
        return {
            "success": self.success,
            "passes": self.passes,
            "notes": self.notes,
            "warnings": self.warnings,
            "failures": self.failures,
        }


# --------------------------------------------------------------------------- text scanning


def is_external(value: str) -> bool:
    value = value.strip()
    if not value or value.startswith(("#", "data:", "blob:", "about:", "javascript:", "mailto:", "tel:")):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "ftp"} or value.startswith("//")


def is_local_reference(value: str) -> bool:
    value = value.strip()
    if not value or value.startswith(("#", "data:", "blob:", "about:", "javascript:", "mailto:", "tel:")):
        return False
    return not is_external(value) and not urlparse(value).scheme


class AssetCollector(HTMLParser):
    """Collect asset references, inline CSS and inline script text from HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.assets: list[tuple[str, str, str]] = []  # (tag, attribute, value)
        self.navigation: list[str] = []
        self.css_chunks: list[str] = []
        self.html_attrs: dict[str, str] = {}
        self.has_viewport = False
        self.inline_event_handlers = 0
        self.inline_style_attributes = 0
        self.script_chunks: list[str] = []
        self._in_style = False
        self._in_script = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = {name.lower(): value or "" for name, value in attrs}
        if tag == "html":
            self.html_attrs = values
        if tag == "meta" and values.get("name", "").lower() == "viewport":
            self.has_viewport = True
        if tag == "style":
            self._in_style = True
        if tag == "script" and "src" not in values and values.get("type", "").strip().lower() in JS_TYPES:
            self._in_script = True
        if tag == "meta" and values.get("http-equiv", "").lower() == "refresh":
            match = META_REFRESH_URL.search(values.get("content", ""))
            if match:
                self.assets.append(("meta", "refresh", match.group("url")))
        if tag == "a" and values.get("href"):
            self.navigation.append(values["href"])
        for attribute in ASSET_ATTRIBUTES.get(tag, ()):
            raw = values.get(attribute, "")
            if not raw:
                continue
            if attribute == "srcset":
                for url in srcset_urls(raw):
                    self.assets.append((tag, attribute, url))
            elif tag in {"use", "image", "feimage"} and raw.startswith("#"):
                continue  # reference to something on the same page
            else:
                self.assets.append((tag, attribute, raw))
        if values.get("style"):
            self.inline_style_attributes += 1
            self.css_chunks.append(values["style"])
        self.inline_event_handlers += sum(1 for name in values if name.startswith("on"))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "style":
            self._in_style = False
        if tag.lower() == "script":
            self._in_script = False

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self.css_chunks.append(data)
        if self._in_script:
            self.script_chunks.append(data)


def css_references(css: str) -> list[str]:
    refs = [match.group("url").strip() for match in CSS_URL.finditer(css)]
    refs += [match.group("url").strip() for match in CSS_IMPORT.finditer(css)]
    # image-set("https://…"), bare addresses in other functions: anything absolute counts as an internet load.
    without_data = re.sub(r"data:[^)'\"]*", "", css)
    refs += [match.group(0) for match in INTERNET_ADDRESS.finditer(without_data) if match.group(0) not in refs]
    return refs


def script_findings(script: str) -> tuple[list[str], list[str]]:
    """(definite remote loads, internet addresses mentioned) in JavaScript text."""
    remote = [match.group(0)[:60] for match in JS_REMOTE_IMPORT.finditer(script)]
    mentioned = sorted({match.group("url")[:80] for match in JS_URL_LITERAL.finditer(script)})
    return remote, mentioned


def find_secrets(text: str) -> list[str]:
    return [label for label, pattern in SECRET_PATTERNS if pattern.search(text)]


def embedded_ir_privacy(text: str) -> list[tuple[str, str]]:
    """Return (level, message) findings for embedded AAC Board IR privacy metadata."""
    findings: list[tuple[str, str]] = []
    for match in EMBEDDED_IR.finditer(text):
        try:
            data = json.loads(match.group("json"))
        except json.JSONDecodeError:
            findings.append(("warn", "embedded AAC Board IR could not be parsed for its privacy metadata"))
            continue
        privacy = data.get("privacy") or {}
        if privacy.get("containsSensitiveData") is True:
            findings.append(("fail", "embedded AAC Board IR is marked containsSensitiveData: true; do not upload it"))
        elif privacy.get("level") not in (None, "anonymous"):
            findings.append(("warn", f"embedded AAC Board IR privacy level is '{privacy.get('level')}'; confirm team approval before uploading"))
        else:
            findings.append(("ok", "embedded AAC Board IR is anonymous with no sensitive data"))
    return findings


def scan_source_text(text: str, report: Report, label: str) -> None:
    """Safety scan shared by the builder (pre-flight) and the package validator."""
    for secret in find_secrets(text):
        report.fail(f"{label} contains what looks like {secret}; remove it before packaging")
    if API_ENDPOINT.search(text):
        report.fail(f"{label} refers to an LMS/Canvas API endpoint; packaged activities must not call QLearn's API")
    for level, message in embedded_ir_privacy(text):
        getattr(report, {"fail": "fail", "warn": "warn", "ok": "ok"}[level])(f"{label}: {message}")


def html_external_assets(text: str) -> list[str]:
    collector = AssetCollector()
    collector.feed(text)
    external = [f"<{tag} {attr}={value}>" for tag, attr, value in collector.assets if is_external(value)]
    external += [f"CSS {ref}" for chunk in collector.css_chunks for ref in css_references(chunk) if is_external(ref)]
    external += [f"script loads {load}" for chunk in collector.script_chunks for load in script_findings(chunk)[0]]
    return external


# --------------------------------------------------------------------------- ZIP checks


def entry_name_problem(name: str) -> str | None:
    if not name:
        return "empty entry name"
    if "\\" in name:
        return "uses a backslash path separator"
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        return "is an absolute path"
    if "\x00" in name:
        return "contains a NUL byte"
    parts = [part for part in name.split("/") if part]
    if any(part == ".." for part in parts):
        return "escapes the package root with '..'"
    return None


def is_junk(name: str) -> bool:
    parts = [part for part in name.split("/") if part]
    if any(part in JUNK_PARTS for part in parts):
        return True
    base = parts[-1] if parts else ""
    return base in JUNK_NAMES or base.endswith(".pyc") or base.startswith("._")


def resolve_local(base_dir: str, reference: str) -> str | None:
    """Resolve a relative URL against a package directory; None if it escapes the root."""
    path = unquote(urlparse(reference).path)
    if not path:
        return None
    joined = posixpath.normpath(posixpath.join(base_dir, path)) if not path.startswith("/") else posixpath.normpath(path.lstrip("/"))
    if joined.startswith("../") or joined == "..":
        return None
    return joined


def check_zip_entries(archive: zipfile.ZipFile, report: Report) -> dict[str, zipfile.ZipInfo]:
    files: dict[str, zipfile.ZipInfo] = {}
    seen: set[str] = set()
    bad = False
    total = 0
    for info in archive.infolist():
        name = info.filename
        problem = entry_name_problem(name)
        if problem:
            report.fail(f"ZIP entry '{name}' {problem}")
            bad = True
            continue
        if name in seen:
            report.fail(f"ZIP entry '{name}' appears more than once")
            bad = True
        seen.add(name)
        if info.flag_bits & 0x1:
            report.fail(f"ZIP entry '{name}' is encrypted; LMS importers cannot read it")
            bad = True
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            report.fail(f"ZIP entry '{name}' is a symbolic link")
            bad = True
        if is_junk(name):
            report.fail(f"ZIP entry '{name}' is junk/private tooling and must not ship")
            bad = True
        if name.endswith("/"):
            continue
        total += info.file_size
        files[name] = info
    if not bad:
        report.ok(f"ZIP structure is clean ({len(files)} file(s), {total:,} bytes uncompressed)")
    if total > MAX_TOTAL_BYTES_WARN:
        report.warn(f"package is {total / 1024 / 1024:.1f} MB uncompressed; large packages upload and load slowly on school networks")
    return files


# --------------------------------------------------------------------------- manifest checks


def q(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def check_manifest(archive: zipfile.ZipFile, files: dict[str, zipfile.ZipInfo], report: Report) -> list[tuple[str, str]]:
    """Validate imsmanifest.xml; return [(resource_id, launch_href)] for SCO resources."""
    if "imsmanifest.xml" not in files:
        nested = [name for name in files if name.endswith("/imsmanifest.xml")]
        if nested:
            report.fail(f"imsmanifest.xml is inside a folder ({nested[0]}); zip the folder's contents, not the folder")
        else:
            report.fail("imsmanifest.xml is missing from the package root")
        return []
    try:
        root = ElementTree.fromstring(archive.read("imsmanifest.xml"))
    except ElementTree.ParseError as error:
        report.fail(f"imsmanifest.xml is not well-formed XML: {error}")
        return []

    if root.tag == q(CP2004_NS, "manifest"):
        report.fail("this is a SCORM 2004 manifest; this validator checks SCORM 1.2 packages only")
        return []
    if root.tag != q(CP_NS, "manifest"):
        report.fail(f"imsmanifest.xml root is {root.tag}, not a SCORM 1.2 IMS content-packaging manifest")
        return []
    version = root.findtext(f"{q(CP_NS, 'metadata')}/{q(CP_NS, 'schemaversion')}", default="").strip()
    schema = root.findtext(f"{q(CP_NS, 'metadata')}/{q(CP_NS, 'schema')}", default="").strip()
    if version != "1.2" or schema != "ADL SCORM":
        report.fail(f"manifest metadata should declare schema 'ADL SCORM' version '1.2' (found '{schema}' '{version}')")
    else:
        report.ok("manifest declares ADL SCORM 1.2")

    identifiers: list[str] = [root.get("identifier", "")]
    for element in root.iter():
        if element is not root and element.get("identifier") is not None:
            identifiers.append(element.get("identifier", ""))
    invalid = [value for value in identifiers if not NCNAME.match(value)]
    duplicates = sorted({value for value in identifiers if identifiers.count(value) > 1})
    if invalid:
        report.fail(f"identifiers must be XML names (letter/underscore first, no spaces): {invalid[:3]}")
    if duplicates:
        report.fail(f"identifiers must be unique: {duplicates[:3]}")
    if not invalid and not duplicates:
        report.ok(f"{len(identifiers)} manifest identifier(s) are unique XML names")

    resources: dict[str, ElementTree.Element] = {}
    for resource in root.iter(q(CP_NS, "resource")):
        resources[resource.get("identifier", "")] = resource

    organizations = root.find(q(CP_NS, "organizations"))
    org_ids = {org.get("identifier", ""): org for org in (organizations.findall(q(CP_NS, "organization")) if organizations is not None else [])}
    default = organizations.get("default", "") if organizations is not None else ""
    if not org_ids:
        report.fail("manifest has no <organization>; the LMS has nothing to launch")
    elif default and default not in org_ids:
        report.fail(f"<organizations default='{default}'> does not match any organisation")
    else:
        report.ok("default organisation resolves")

    launchable: list[tuple[str, str]] = []
    for org in org_ids.values():
        if not (org.findtext(q(CP_NS, "title")) or "").strip():
            report.fail(f"organisation {org.get('identifier')} has no title")
        for item in org.iter(q(CP_NS, "item")):
            ref = item.get("identifierref")
            if not (item.findtext(q(CP_NS, "title")) or "").strip():
                report.fail(f"item {item.get('identifier')} has no title")
            if ref is None:
                continue
            resource = resources.get(ref)
            if resource is None:
                report.fail(f"item {item.get('identifier')} points at missing resource '{ref}'")
                continue
            if resource.get("href"):
                launchable.append((ref, resource.get("href", "")))
    if not launchable:
        report.fail("no <item> launches a resource with an href")

    listed: set[str] = set()
    sco_launches: list[tuple[str, str]] = []
    for resource_id, resource in resources.items():
        scormtype = resource.get(q(ADLCP_NS, "scormtype"))
        if scormtype not in ("sco", "asset"):
            report.fail(f"resource {resource_id} needs adlcp:scormtype='sco' or 'asset' (found {scormtype!r})")
        if resource.get("{http://www.w3.org/XML/1998/namespace}base"):
            report.warn(f"resource {resource_id} uses xml:base; this validator resolves paths from the package root")
        href = resource.get("href")
        if href:
            launch = resolve_local("", href)
            if launch is None or launch not in files:
                report.fail(f"resource {resource_id} launches '{href}', which is not in the package")
            elif scormtype == "sco":
                sco_launches.append((resource_id, launch))
        for file_element in resource.findall(q(CP_NS, "file")):
            file_href = file_element.get("href", "")
            resolved = resolve_local("", file_href)
            if resolved is None or resolved not in files:
                report.fail(f"resource {resource_id} lists '{file_href}', which is not in the package")
            else:
                listed.add(resolved)
        for dependency in resource.findall(q(CP_NS, "dependency")):
            if dependency.get("identifierref") not in resources:
                report.fail(f"resource {resource_id} depends on missing resource '{dependency.get('identifierref')}'")
    if not sco_launches:
        report.fail("package has no SCO resource; Canvas/QLearn's SCORM tool expects at least one")
    else:
        report.ok(f"{len(sco_launches)} SCO launch file(s) present: {', '.join(href for _, href in sco_launches)}")

    unlisted = sorted(name for name in files if name != "imsmanifest.xml" and name not in SCHEMA_FILES and name not in listed)
    if unlisted:
        report.fail(f"{len(unlisted)} packaged file(s) are not listed in the manifest: {unlisted[:5]}")
    else:
        report.ok("every packaged file is listed in the manifest")

    schema_location = root.get(q(XSI_NS, "schemaLocation"), "")
    named_xsds = [token for token in schema_location.split() if token.endswith(".xsd")]
    missing_xsds = [name for name in named_xsds if name not in files]
    if missing_xsds:
        report.warn(f"schemaLocation names {missing_xsds} but the file(s) are not packaged; most players ignore this")
    if not any(name in files for name in SCHEMA_FILES):
        report.note("SCORM 1.2 schema (.xsd) files are not bundled; most players, including Canvas's, import without them")
    return sco_launches


# --------------------------------------------------------------------------- launch page and content checks


def read_text(archive: zipfile.ZipFile, name: str) -> str | None:
    try:
        return archive.read(name).decode("utf-8")
    except UnicodeDecodeError:
        return None


def check_launch_pages(archive: zipfile.ZipFile, files: dict[str, zipfile.ZipInfo], launches: Iterable[tuple[str, str]], report: Report) -> None:
    launches = list(launches)
    launch_names = {launch for _, launch in launches}
    # Other pages of a multi-page activity get the same asset/internet checks as the launch page.
    others = [("page", name) for name in sorted(files) if name.lower().endswith((".html", ".htm")) and name not in launch_names]
    for resource_id, launch in launches + others:
        is_launch = launch in launch_names
        text = read_text(archive, launch)
        if text is None:
            report.fail(f"{launch} is not UTF-8 text")
            continue
        base_dir = posixpath.dirname(launch)
        collector = AssetCollector()
        collector.feed(text)
        missing: list[str] = []
        external: list[str] = []
        local_scripts: list[str] = []
        references = [(tag, attr, value) for tag, attr, value in collector.assets]
        references += [("css", "url", ref) for chunk in collector.css_chunks for ref in css_references(chunk)]
        for tag, attr, value in references:
            if is_external(value):
                external.append(f"<{tag} {attr}={value}>")
            elif is_local_reference(value):
                resolved = resolve_local(base_dir, value)
                if resolved is None or resolved not in files:
                    missing.append(value)
                elif tag == "script":
                    local_scripts.append(resolved)
        # CSS files loaded by the launch page can reference more assets.
        for tag, attr, value in collector.assets:
            if tag == "link" and is_local_reference(value):
                css_path = resolve_local(base_dir, value)
                if css_path and css_path in files and css_path.endswith(".css"):
                    css_text = read_text(archive, css_path) or ""
                    for ref in css_references(css_text):
                        if is_external(ref):
                            external.append(f"{css_path} url({ref})")
                        elif is_local_reference(ref):
                            target = resolve_local(posixpath.dirname(css_path), ref)
                            if target is None or target not in files:
                                missing.append(f"{css_path} -> {ref}")
        if external:
            report.fail(f"{launch} loads from the internet: {external[:5]}; school filters and offline devices break these")
        if missing:
            report.fail(f"{launch} references files that are not in the package: {missing[:5]}")
        if not external and not missing:
            report.ok(f"{launch}: every asset resolves inside the package and nothing loads from the internet")

        script_sources = collector.script_chunks + [read_text(archive, path) or "" for path in local_scripts]
        remote_loads = [load for chunk in script_sources for load in script_findings(chunk)[0]]
        mentioned = sorted({url for chunk in script_sources for url in script_findings(chunk)[1]})
        if remote_loads:
            report.fail(f"{launch} scripts load code from the internet: {remote_loads[:3]}")
        if mentioned:
            report.warn(f"{launch} scripts mention internet addresses {mentioned[:3]}; check nothing is downloaded or sent")
        script_texts = [text] + [read_text(archive, path) or "" for path in local_scripts]
        if not is_launch:
            continue
        if any("LMSInitialize" in chunk for chunk in script_texts):
            report.ok(f"{launch} starts a SCORM 1.2 session (LMSInitialize)")
        else:
            report.warn(f"{launch} never calls LMSInitialize; some players will not record that it opened")
        if collector.html_attrs.get("lang"):
            report.ok(f"{launch} declares lang=\"{collector.html_attrs['lang']}\"")
        else:
            report.warn(f"{launch} has no <html lang>; screen readers may use the wrong voice")
        if not collector.has_viewport:
            report.warn(f"{launch} has no viewport meta tag")
        if collector.inline_event_handlers:
            report.warn(f"{launch} uses {collector.inline_event_handlers} inline on…= handler(s); a strict player CSP would block them")


def check_content_safety(archive: zipfile.ZipFile, files: dict[str, zipfile.ZipInfo], report: Report) -> None:
    safety = Report()
    network_files: list[str] = []
    for name in sorted(files):
        if Path(name).suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = read_text(archive, name)
        if text is None:
            continue
        scan_source_text(text, safety, name)
        if Path(name).suffix.lower() in SCRIPT_SUFFIXES and NETWORK_CALLS.search(text):
            network_files.append(name)
    report.passes.extend(safety.passes)
    report.warnings.extend(safety.warnings)
    report.failures.extend(safety.failures)
    if not safety.failures:
        report.ok("no access tokens, credentials, private keys or LMS API endpoints found")
    if network_files:
        report.warn(f"network calls found in {network_files[:5]}; confirm nothing sends student data off the device")
    else:
        report.ok("no network calls (fetch/XHR/beacon/WebSocket) in packaged scripts")


# --------------------------------------------------------------------------- source equivalence


def restore_original(entries: dict[str, bytes], info: dict | None = None) -> bytes:
    """Undo packaging: re-inline split assets and remove the SCORM bridge tag."""
    launch = (info or {}).get("launch", "index.html")
    text = entries[launch].decode("utf-8")
    for split in (info or {}).get("split", []):
        content = entries[split["file"]].decode("utf-8")
        text = text.replace(split["replacement"], split["openTag"] + content + split["closeTag"], 1)
    text, count = BRIDGE_TAG_RE.subn("", text, count=1)
    if count != 1:
        raise ValueError("SCORM bridge tag not found exactly once in the launch page")
    return text.encode("utf-8")


def check_page_equivalence(archive: zipfile.ZipFile, report: Report) -> None:
    """Other pages of a multi-page package must be their recorded source plus only the bridge."""
    if "package-info.json" not in archive.namelist():
        return
    info = json.loads(archive.read("package-info.json").decode("utf-8"))
    for page in info.get("pages", []):
        try:
            text = archive.read(page["path"]).decode("utf-8")
        except KeyError:
            report.fail(f"package-info lists page {page['path']}, which is not in the package")
            continue
        restored, count = BRIDGE_TAG_RE.subn("", text, count=1)
        digest = hashlib.sha256(restored.encode("utf-8")).hexdigest()
        if count != 1 or digest != page.get("sha256"):
            report.fail(f"{page['path']} differs from its source beyond the SCORM bridge line(s)")
        else:
            report.ok(f"{page['path']} is its source page plus only the SCORM bridge line(s)")


def check_source_equivalence(archive: zipfile.ZipFile, source: Path, report: Report) -> None:
    entries = {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}
    info = None
    if "package-info.json" in entries:
        info = json.loads(entries["package-info.json"].decode("utf-8"))
    try:
        restored = restore_original(entries, info)
    except (KeyError, ValueError) as error:
        report.fail(f"could not reconstruct the source activity from the package: {error}")
        return
    if restored == source.read_bytes():
        report.ok(f"packaged activity is byte-for-byte {source.name} plus only the SCORM bridge line(s)")
    else:
        report.fail(f"packaged activity differs from {source.name} beyond the SCORM bridge line(s)")


# --------------------------------------------------------------------------- entry point


def validate_package(path: Path, source: Path | None = None) -> Report:
    report = Report()
    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, FileNotFoundError) as error:
        report.fail(f"{path} is not a readable ZIP file: {error}")
        return report
    with archive:
        files = check_zip_entries(archive, report)
        launches = check_manifest(archive, files, report)
        check_launch_pages(archive, files, launches, report)
        check_content_safety(archive, files, report)
        check_page_equivalence(archive, report)
        if source is not None:
            check_source_equivalence(archive, source, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("package", type=Path, help="SCORM 1.2 ZIP to check")
    parser.add_argument("--source", type=Path, help="original standalone HTML; prove the package changes nothing but the bridge")
    parser.add_argument("--json", type=Path, help="also write the report as JSON")
    args = parser.parse_args(argv)
    report = validate_package(args.package, args.source)
    report.print()
    if args.json:
        args.json.write_text(json.dumps(report.as_dict(), indent=2) + "\n", encoding="utf-8")
    print("RESULT: " + ("ready for a teacher test upload" if report.success else "NOT ready — fix the FAIL lines first"))
    return 0 if report.success else 1


if __name__ == "__main__":
    sys.exit(main())

"""SCORM 1.2 packaging: deterministic, unchanged board, valid manifest, safe content."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "qlearn-accessibility" / "scripts"
AAC_SCRIPTS = ROOT / "skills" / "agentic-aac-board-maker" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(filename: str, name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses need the module registered while it loads.
    spec.loader.exec_module(module)
    return module


validate_scorm = load_module("validate_scorm.py", "validate_scorm_tests")
build_scorm = load_module("build_scorm.py", "build_scorm_tests")

BOARD = ROOT / "generated" / "gaze-choice-2x2" / "gaze-choice-class-activity.html"
BOARD_IR = ROOT / "generated" / "gaze-choice-2x2" / "gaze-choice-class-activity.ir.json"
ALL_BOARDS = sorted(path for path in (ROOT / "generated").glob("*/*.html") if path.name != "partner-card.html")
CP = "{http://www.imsproject.org/xsd/imscp_rootv1p1p2}"
ADLCP = "{http://www.adlnet.org/xsd/adlcp_rootv1p2}"
GOOD_MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="m" version="1.0" xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2" xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2">
  <metadata><schema>ADL SCORM</schema><schemaversion>1.2</schemaversion></metadata>
  <organizations default="o"><organization identifier="o"><title>T</title>
    <item identifier="i" identifierref="r"><title>T</title></item></organization></organizations>
  <resources><resource identifier="r" type="webcontent" adlcp:scormtype="sco" href="index.html">{files}</resource></resources>
</manifest>"""
GOOD_PAGE = '<!doctype html><html lang="en-AU"><head><meta name="viewport" content="width=device-width"></head><body><script src="b.js"></script></body></html>'


def write_zip(path: Path, entries: dict[str, bytes | str]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return path


def minimal_package(path: Path, extra: dict[str, bytes | str] | None = None, files: list[str] | None = None) -> Path:
    entries: dict[str, bytes | str] = {"index.html": GOOD_PAGE, "b.js": "API.LMSInitialize('');"}
    entries.update(extra or {})
    listed = files if files is not None else [name for name in entries]
    manifest = GOOD_MANIFEST.format(files="".join(f'<file href="{name}"/>' for name in listed))
    return write_zip(path, {"imsmanifest.xml": manifest, **entries})


class BuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def build(self, name: str = "board.zip", **options) -> tuple[Path, dict]:
        output = self.dir / name
        return output, build_scorm.build_package(BOARD, output, **options)

    def test_inline_package_is_the_original_board_plus_only_the_bridge(self) -> None:
        before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
        output, info = self.build()
        self.assertEqual(before, hashlib.sha256(BOARD.read_bytes()).hexdigest(), "packaging must not touch the source board")
        with zipfile.ZipFile(output) as archive:
            launch = archive.read("index.html")
            entries = {name: archive.read(name) for name in archive.namelist()}
        tag = build_scorm.bridge_tag(False).encode("utf-8")
        self.assertEqual(1, launch.count(tag))
        self.assertEqual(BOARD.read_bytes(), launch.replace(tag, b"", 1))
        self.assertEqual(BOARD.read_bytes(), validate_scorm.restore_original(entries, info))
        self.assertEqual(info["source"]["sha256"], before)
        self.assertFalse(info["bridge"]["sendsStudentData"])

    def test_split_package_restores_byte_for_byte_and_keeps_data_inline(self) -> None:
        output, info = self.build("split.zip", layout="split")
        with zipfile.ZipFile(output) as archive:
            entries = {name: archive.read(name) for name in archive.namelist()}
        launch = entries["index.html"].decode("utf-8")
        self.assertIn('<script id="aac-board-ir" type="application/json">', launch, "board data stays inline")
        self.assertNotIn("<style", launch.lower())
        self.assertIn('data-aac-shared-runtime src="assets/inline-script-1.js"', launch)
        self.assertEqual({"assets/inline-script-1.js", "assets/inline-style-1.css"}, {item["file"] for item in info["split"]})
        self.assertEqual(BOARD.read_bytes(), validate_scorm.restore_original(entries, info))
        runtime = (ROOT / "skills" / "agentic-aac-board-maker" / "assets" / "aac-board-runtime.js").read_text(encoding="utf-8")
        self.assertIn(runtime.strip()[:200], entries["assets/inline-script-1.js"].decode("utf-8"))

    def test_build_is_deterministic(self) -> None:
        first, _ = self.build("a.zip")
        second, _ = self.build("b.zip")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(first) as archive:
            self.assertEqual("imsmanifest.xml", archive.namelist()[0])
            self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist()))

    def test_manifest_lists_every_file_and_launches_one_sco(self) -> None:
        output, _ = self.build()
        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())
            root = ElementTree.fromstring(archive.read("imsmanifest.xml"))
        self.assertEqual("1.2", root.findtext(f"{CP}metadata/{CP}schemaversion"))
        resources = list(root.iter(f"{CP}resource"))
        self.assertEqual(1, len(resources))
        self.assertEqual("sco", resources[0].get(f"{ADLCP}scormtype"))
        self.assertEqual("index.html", resources[0].get("href"))
        listed = {element.get("href") for element in resources[0].findall(f"{CP}file")}
        self.assertEqual(names - {"imsmanifest.xml"}, listed)
        self.assertEqual("Choose a Class Activity", root.findtext(f"{CP}organizations/{CP}organization/{CP}title"))
        self.assertIn("licences/ARASAAC-symbols-LICENCE.md", names, "symbol licence travels with the board")

    def test_packaged_board_still_passes_ir_runtime_parity(self) -> None:
        output, _ = self.build()
        launch = self.dir / "index.html"
        with zipfile.ZipFile(output) as archive:
            launch.write_bytes(archive.read("index.html"))
        result = subprocess.run(
            [sys.executable, str(AAC_SCRIPTS / "validate_html_parity.py"), str(BOARD_IR), str(launch)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_completion_reporting_is_opt_in(self) -> None:
        output, info = self.build("done.zip", report_completion=True)
        with zipfile.ZipFile(output) as archive:
            self.assertIn(b'data-report-completion="true"', archive.read("index.html"))
        self.assertTrue(info["bridge"]["reportCompletion"])
        _, default_info = self.build()
        self.assertFalse(default_info["bridge"]["reportCompletion"])

    def test_fullscreen_toggle_is_opt_in_and_reversible(self) -> None:
        output, info = self.build()
        with zipfile.ZipFile(output) as archive:
            self.assertNotIn("scorm/fullscreen-toggle.js", archive.namelist())
            self.assertNotIn(b"fullscreen-toggle", archive.read("index.html"))
        self.assertIsNone(info["fullscreenToggle"])
        for layout in ("inline", "split"):
            with self.subTest(layout=layout):
                output, info = self.build(f"toggle-{layout}.zip", layout=layout, fullscreen_toggle="bottom-left")
                with zipfile.ZipFile(output) as archive:
                    entries = {name: archive.read(name) for name in archive.namelist()}
                    listed = {e.get("href") for e in ElementTree.fromstring(entries["imsmanifest.xml"]).iter(f"{CP}file")}
                tag = build_scorm.bridge_tag(False, toggle_position="bottom-left").encode("utf-8")
                self.assertEqual(1, entries["index.html"].count(tag), "toggle line sits straight after the bridge line")
                self.assertEqual((build_scorm.SKILL_DIR / "assets" / "fullscreen-toggle.js").read_bytes(), entries["scorm/fullscreen-toggle.js"])
                self.assertIn("scorm/fullscreen-toggle.js", listed)
                self.assertEqual({"file": "scorm/fullscreen-toggle.js", "position": "bottom-left"}, info["fullscreenToggle"])
                self.assertEqual(BOARD.read_bytes(), validate_scorm.restore_original(entries, info))
                report = validate_scorm.validate_package(output, BOARD)
                self.assertTrue(report.success, report.failures)
                self.assertEqual([], report.warnings, "the toggle adds no network calls or internet addresses")
        with self.assertRaises(build_scorm.PackagingError):
            self.build("bad.zip", fullscreen_toggle="middle")

    def test_fullscreen_toggle_from_the_command_line(self) -> None:
        output = self.dir / "cli.zip"
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "build_scorm.py"), str(BOARD), str(output), "--fullscreen-toggle"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Full screen toggle: top-right", result.stdout)
        with zipfile.ZipFile(output) as archive:
            self.assertIn(b'<script src="scorm/fullscreen-toggle.js" data-position="top-right"></script>', archive.read("index.html"))

    def test_every_generated_board_packages_in_both_layouts(self) -> None:
        for board in ALL_BOARDS:
            for layout in ("inline", "split"):
                with self.subTest(board=board.name, layout=layout):
                    output = self.dir / f"{board.stem}.{layout}.zip"
                    build_scorm.build_package(board, output, layout=layout)
                    report = validate_scorm.validate_package(output, board)
                    self.assertTrue(report.success, report.failures)
                    self.assertEqual([], report.warnings)

    def test_builder_refuses_unsafe_or_online_sources(self) -> None:
        cases = {
            "token": "<html><body>1234~" + "a" * 64 + "</body></html>",
            "bearer": "<html><body><script>h={Authorization:'" + "Bearer " + "x" * 26 + "'}</script></body></html>",
            "api": "<html><body><script>fetch('/api/v1/courses')</script></body></html>",
            "cdn": '<html><head><script src="https://cdn.example.com/x.js"></script></head><body></body></html>',
            "webfont": "<html><head><style>@import url(https://fonts.example.com/a.css);</style></head><body></body></html>",
            "sensitive": '<html><body><script id="aac-board-ir" type="application/json">{"privacy":{"level":"anonymous","containsSensitiveData":true}}</script></body></html>',
            "no-body": "<html>no body tag",
        }
        for label, html in cases.items():
            with self.subTest(case=label):
                source = self.dir / f"{label}.html"
                source.write_text(html, encoding="utf-8")
                with self.assertRaises(build_scorm.PackagingError):
                    build_scorm.build_package(source, self.dir / f"{label}.zip")
                self.assertFalse((self.dir / f"{label}.zip").exists())

    def test_ordinary_links_to_websites_are_allowed(self) -> None:
        source = self.dir / "links.html"
        source.write_text('<!doctype html><html lang="en-AU"><head><meta name="viewport" content="width=device-width"><title>Links</title></head>'
                          '<body><a href="https://arasaac.org">ARASAAC</a></body></html>', encoding="utf-8")
        output = self.dir / "links.zip"
        build_scorm.build_package(source, output)
        self.assertTrue(validate_scorm.validate_package(output, source).success)

    def test_identifier_is_an_anonymous_xml_name(self) -> None:
        self.assertEqual("aac-2026-board", build_scorm.slug_identifier("2026 Board"))
        self.assertEqual("my-board", build_scorm.slug_identifier("My Board!!"))
        self.assertRegex(build_scorm.slug_identifier("???"), validate_scorm.NCNAME)

    def test_command_line_builds_and_reports(self) -> None:
        output = self.dir / "cli.zip"
        result = subprocess.run([sys.executable, str(SCRIPTS / "build_scorm.py"), str(BOARD), str(output)], capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Title in QLearn: Choose a Class Activity", result.stdout)
        check = subprocess.run([sys.executable, str(SCRIPTS / "validate_scorm.py"), str(output), "--source", str(BOARD)], capture_output=True, text=True, check=False)
        self.assertEqual(0, check.returncode, check.stdout)
        self.assertIn("RESULT: ready for a teacher test upload", check.stdout)


class SplitLayoutSafetyTests(unittest.TestCase):
    """The split layout must keep behaviour, not just be reversible."""

    PAGE = ('<!doctype html><HTML lang="en-AU"><head><meta name="viewport" content="width=device-width"><title>T</title>'
            '<STYLE class="theme" media="screen">p{color:#111}</STYLE></head><body><p>Hi</p>'
            '<script data-note="a>b">window.ok = 1;</script>'
            '<script id="data" type="application/json">{"a": "</style>"}</script></body></HTML>')

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def build(self, html: str) -> tuple[dict, dict]:
        source = self.dir / "page.html"
        source.write_text(html, encoding="utf-8")
        output = self.dir / "page.zip"
        info = build_scorm.build_package(source, output, layout="split")
        with zipfile.ZipFile(output) as archive:
            return info, {name: archive.read(name) for name in archive.namelist()}

    def test_attributes_ids_and_case_survive(self) -> None:
        info, entries = self.build(self.PAGE)
        launch = entries["index.html"].decode("utf-8")
        self.assertIn('href="assets/inline-style-1.css" class="theme" media="screen"', launch)
        self.assertIn('<script data-note="a>b" src="assets/inline-script-1.js"></script>', launch)
        self.assertEqual(b"window.ok = 1;", entries["assets/inline-script-1.js"])
        self.assertIn('<script id="data" type="application/json">', launch, "data blocks stay inline")
        self.assertEqual(self.PAGE.encode("utf-8"), validate_scorm.restore_original(entries, info))

    def test_unsafe_cases_are_refused(self) -> None:
        cases = {
            "async": '<html><body><script async>go()</script></body></html>',
            "defer": '<html><body><script defer>go()</script></body></html>',
            "svg-style": '<html><body><svg><style>circle{fill:red}</style><circle r="4"/></svg></body></html>',
            "template": '<html><body><template><script>go()</script></template></body></html>',
            "named-style": '<html><head><style id="theme">p{}</style></head><body><script>x()</script></body></html>',
        }
        for label, html in cases.items():
            with self.subTest(case=label), self.assertRaises(build_scorm.PackagingError):
                self.build(html)

    def test_text_inside_a_textarea_is_never_moved(self) -> None:
        # Newer Python parsers read <textarea> as plain text (nothing to move); older ones see a <style> and refuse.
        html = '<html><body><textarea><style>p{}</style></textarea></body></html>'
        try:
            info, entries = self.build(html)
        except build_scorm.PackagingError:
            return
        self.assertEqual([], info["split"])
        self.assertIn("<textarea><style>p{}</style></textarea>", entries["index.html"].decode("utf-8"))


class MultiPageTests(unittest.TestCase):
    """An activity made of several linked pages keeps one session and stays unchanged."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        page = ('<!doctype html><html lang="en-AU"><head><meta name="viewport" content="width=device-width">'
                '<!-- <title>Not this</title> --><title>{title}</title></head><body><a href="{other}">Go</a></body></html>')
        (self.dir / "index.html").write_text(page.format(title="Practice", other="sub/two.html"), encoding="utf-8")
        (self.dir / "sub").mkdir()
        (self.dir / "sub" / "two.html").write_text(page.format(title="Two", other="../index.html"), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_every_page_gets_the_bridge_and_stays_unchanged(self) -> None:
        output = self.dir / "multi.zip"
        info = build_scorm.build_package(self.dir / "index.html", output, pages=["sub/two.html"])
        self.assertEqual("Practice", info["title"], "a <title> inside a comment is ignored")
        with zipfile.ZipFile(output) as archive:
            launch = archive.read("index.html").decode("utf-8")
            second = archive.read("sub/two.html").decode("utf-8")
            listed = {e.get("href") for e in ElementTree.fromstring(archive.read("imsmanifest.xml")).iter(f"{CP}file")}
        self.assertIn('src="scorm/scorm12-bridge.js" data-report-completion="false" data-multi-page="true"', launch)
        self.assertIn('src="../scorm/scorm12-bridge.js" data-report-completion="false" data-multi-page="true"', second)
        self.assertIn("sub/two.html", listed)
        report = validate_scorm.validate_package(output, self.dir / "index.html")
        self.assertTrue(report.success, report.failures)
        self.assertTrue(any("sub/two.html is its source page" in item for item in report.passes))

    def test_every_page_gets_the_fullscreen_toggle_with_the_right_path(self) -> None:
        output = self.dir / "multi-toggle.zip"
        build_scorm.build_package(self.dir / "index.html", output, pages=["sub/two.html"], fullscreen_toggle="top-left")
        with zipfile.ZipFile(output) as archive:
            launch = archive.read("index.html").decode("utf-8")
            second = archive.read("sub/two.html").decode("utf-8")
        self.assertIn('<script src="scorm/fullscreen-toggle.js" data-position="top-left"></script>', launch)
        self.assertIn('<script src="../scorm/fullscreen-toggle.js" data-position="top-left"></script>', second)
        report = validate_scorm.validate_package(output, self.dir / "index.html")
        self.assertTrue(report.success, report.failures)

    def test_tampered_page_and_bad_pages_are_caught(self) -> None:
        output = self.dir / "multi.zip"
        build_scorm.build_package(self.dir / "index.html", output, pages=["sub/two.html"])
        with zipfile.ZipFile(output) as archive:
            entries = {name: archive.read(name) for name in archive.namelist()}
        entries["sub/two.html"] = entries["sub/two.html"].replace(b"Go", b"Gone")
        tampered = write_zip(self.dir / "tampered.zip", entries)
        self.assertTrue(any("differs from its source" in item for item in validate_scorm.validate_package(tampered).failures))
        for bad in (["../outside.html"], ["missing.html"], ["index.html"]):
            with self.subTest(pages=bad), self.assertRaises(build_scorm.PackagingError):
                build_scorm.build_package(self.dir / "index.html", self.dir / "bad.zip", pages=bad)
        with self.assertRaises(build_scorm.PackagingError):
            build_scorm.build_package(self.dir / "index.html", self.dir / "split.zip", pages=["sub/two.html"], layout="split")


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def assert_fails(self, package: Path, fragment: str) -> None:
        report = validate_scorm.validate_package(package)
        self.assertFalse(report.success, "expected a failure")
        self.assertTrue(any(fragment in failure for failure in report.failures), report.failures)

    def test_minimal_valid_package_passes(self) -> None:
        report = validate_scorm.validate_package(minimal_package(self.dir / "ok.zip"))
        self.assertTrue(report.success, report.failures)

    def test_manifest_must_be_at_the_root(self) -> None:
        package = write_zip(self.dir / "nested.zip", {"folder/imsmanifest.xml": GOOD_MANIFEST.format(files=""), "folder/index.html": GOOD_PAGE})
        self.assert_fails(package, "inside a folder")

    def test_missing_and_unlisted_files_fail(self) -> None:
        self.assert_fails(minimal_package(self.dir / "missing.zip", files=["index.html", "b.js", "gone.js"]), "not in the package")
        self.assert_fails(minimal_package(self.dir / "unlisted.zip", extra={"stray.css": "a{}"}, files=["index.html", "b.js"]), "not listed")

    def test_unsafe_zip_entries_fail(self) -> None:
        self.assert_fails(minimal_package(self.dir / "dotdot.zip", extra={"../evil.js": "x"}), "escapes the package root")
        self.assert_fails(minimal_package(self.dir / "junk.zip", extra={"__MACOSX/._index.html": "x"}), "junk")
        self.assert_fails(minimal_package(self.dir / "env.zip", extra={".env": "TOKEN=x"}), "junk")

    def test_symlink_entry_fails(self) -> None:
        package = minimal_package(self.dir / "link.zip")
        with zipfile.ZipFile(package, "a") as archive:
            info = zipfile.ZipInfo("link.js")
            info.external_attr = (0o120777 << 16)
            archive.writestr(info, "index.html")
        self.assert_fails(package, "symbolic link")

    def test_secrets_and_api_endpoints_fail(self) -> None:
        self.assert_fails(minimal_package(self.dir / "token.zip", extra={"b.js": "API.LMSInitialize(''); t='9~" + "Z" * 64 + "'"}), "access token")
        self.assert_fails(minimal_package(self.dir / "api.zip", extra={"b.js": "API.LMSInitialize(''); fetch('https://x.instructure.com/api/v1/courses')"}), "API endpoint")

    def test_external_assets_fail_and_network_calls_warn(self) -> None:
        page = GOOD_PAGE.replace('<script src="b.js"></script>', '<script src="b.js"></script><img src="https://example.com/a.png" alt="">')
        self.assert_fails(minimal_package(self.dir / "cdn.zip", extra={"index.html": page}), "loads from the internet")
        report = validate_scorm.validate_package(minimal_package(self.dir / "net.zip", extra={"b.js": "API.LMSInitialize(''); fetch('data.json')"}))
        self.assertTrue(any("network calls" in warning for warning in report.warnings))

    def test_hidden_internet_loads_are_caught(self) -> None:
        loads = {
            "svg-image": GOOD_PAGE.replace("</body>", '<svg><image href="https://example.com/a.png"/></svg></body>'),
            "svg-use": GOOD_PAGE.replace("</body>", '<svg><use xlink:href="https://example.com/s.svg#i"/></svg></body>'),
            "refresh": GOOD_PAGE.replace("<head>", '<head><meta http-equiv="refresh" content="0; url=https://example.com/">'),
            "base": GOOD_PAGE.replace("<head>", '<head><base href="https://example.com/">'),
            "image-set": GOOD_PAGE.replace("</body>", "<style>p{background:image-set('https://example.com/a.png' 1x)}</style></body>"),
            "import": GOOD_PAGE.replace("</body>", "<script>import('https://example.com/m.js')</script></body>"),
        }
        for label, page in loads.items():
            with self.subTest(case=label):
                self.assert_fails(minimal_package(self.dir / f"{label}.zip", extra={"index.html": page}), "internet")
        mention = GOOD_PAGE.replace("</body>", "<script>const img = new Image(); img.src = 'https://example.com/p.gif';</script></body>")
        report = validate_scorm.validate_package(minimal_package(self.dir / "mention.zip", extra={"index.html": mention}))
        self.assertTrue(any("mention internet addresses" in warning for warning in report.warnings), report.warnings)

    def test_srcset_with_data_uri_is_not_a_missing_file(self) -> None:
        page = GOOD_PAGE.replace("</body>", '<img alt="" srcset="data:image/png;base64,AAAA,BBBB 1x, b.js 2x"></body>')
        report = validate_scorm.validate_package(minimal_package(self.dir / "srcset.zip", extra={"index.html": page}))
        self.assertTrue(report.success, report.failures)
        self.assertEqual(["data:image/png;base64,AAAA,BBBB", "b.js"], validate_scorm.srcset_urls("data:image/png;base64,AAAA,BBBB 1x, b.js 2x"))

    def test_bad_identifiers_and_scorm_2004_fail(self) -> None:
        bad = GOOD_MANIFEST.replace('identifier="i"', 'identifier="1 bad"').format(files='<file href="index.html"/><file href="b.js"/>')
        self.assert_fails(write_zip(self.dir / "ids.zip", {"imsmanifest.xml": bad, "index.html": GOOD_PAGE, "b.js": "LMSInitialize"}), "XML names")
        manifest_2004 = '<manifest xmlns="http://www.imsglobal.org/xsd/imscp_v1p1" identifier="m"/>'
        self.assert_fails(write_zip(self.dir / "2004.zip", {"imsmanifest.xml": manifest_2004}), "SCORM 2004")

    def test_sco_without_lms_initialize_warns(self) -> None:
        report = validate_scorm.validate_package(minimal_package(self.dir / "quiet.zip", extra={"b.js": "console.log(1)"}))
        self.assertTrue(report.success)
        self.assertTrue(any("LMSInitialize" in warning for warning in report.warnings))

    def test_source_equivalence_detects_changes(self) -> None:
        output = self.dir / "board.zip"
        build_scorm.build_package(BOARD, output)
        changed = self.dir / "changed.html"
        changed.write_bytes(BOARD.read_bytes().replace(b"Choose a Class Activity", b"Choose an Activity", 1))
        report = validate_scorm.validate_package(output, changed)
        self.assertTrue(any("differs" in failure for failure in report.failures))

    def test_json_report(self) -> None:
        package = minimal_package(self.dir / "ok.zip")
        out = self.dir / "report.json"
        self.assertEqual(0, validate_scorm.main([str(package), "--json", str(out)]))
        self.assertTrue(json.loads(out.read_text(encoding="utf-8"))["success"])


if __name__ == "__main__":
    unittest.main()

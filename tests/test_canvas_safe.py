"""Canvas-safe page rendering and saved-page comparison (synthetic, de-identified fixtures only)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "qlearn-accessibility" / "scripts"
FIXTURE = ROOT / "tests" / "fixtures" / "qlearn" / "synthetic-lesson-page.html"
sys.path.insert(0, str(SCRIPTS))


def load_module(filename: str, name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


canvas_safe = load_module("render_canvas_safe.py", "render_canvas_safe_tests")
compare_saved = load_module("compare_saved_canvas_page.py", "compare_saved_tests")


def elements(html: str):
    return [element for element in canvas_safe.parse(html).iter() if element.tag != "#root"]


class CanvasSafeRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = FIXTURE.read_text(encoding="utf-8")
        cls.result = canvas_safe.transform(cls.source)

    def test_every_word_link_image_and_media_item_is_kept(self) -> None:
        lost = self.result.report["lost"]
        self.assertEqual({"words": [], "links": [], "images": [], "media": []}, lost)
        source, output = self.result.report["inventory"]["source"], self.result.report["inventory"]["output"]
        self.assertEqual(source["words"], output["words"])
        self.assertEqual(sorted(source["links"]), sorted(output["links"]))
        self.assertEqual(source["images"], output["images"])

    def test_output_uses_only_the_canvas_allowlist(self) -> None:
        for element in elements(self.result.html):
            self.assertIn(element.tag, canvas_safe.ALLOWED_TAGS | canvas_safe.MATHML_TAGS, element.tag)
            self.assertNotIn(element.tag, canvas_safe.PAGE_REMOVED_TAGS)
            for name, value in element.attrs:
                allowed = name in canvas_safe.GLOBAL_ATTRS or name.startswith(("aria-", "data-")) or name in canvas_safe.ELEMENT_ATTRS.get(element.tag, set())
                self.assertTrue(allowed, f"{name} on <{element.tag}>")
                self.assertFalse(name.startswith("on"))
            for prop, value in canvas_safe.parse_style(element.get("style")):
                self.assertTrue(canvas_safe.css_property_allowed(prop), prop)
                if prop == "position":
                    self.assertNotIn(value, {"fixed", "sticky"})
        self.assertNotRegex(self.result.html.lower(), r"<(script|style|form|button|label)\b")

    def test_headings_sit_under_the_page_title_without_skipping(self) -> None:
        levels = [int(element.tag[1]) for element in elements(self.result.html) if re.fullmatch(r"h[1-6]", element.tag)]
        self.assertEqual(2, levels[0])
        self.assertNotIn(1, levels)
        for previous, current in zip(levels, levels[1:]):
            self.assertLessEqual(current, previous + 1)

    def test_contrast_size_and_targets_are_fixed(self) -> None:
        html = self.result.html
        self.assertNotIn("#9a9a9a", html)
        self.assertNotIn("color: red", html)
        self.assertNotIn("font-size: 12px", html)
        self.assertIn("background: #ffeeaa", html, "simple <style> class rules are carried over inline")
        worksheet = next(element for element in elements(html) if element.tag == "a" and "5678" in element.get("href"))
        self.assertIn("min-height: 48px", worksheet.get("style"), "a link on its own line becomes a large target")
        self.assertIn('sandbox="allow-scripts allow-same-origin"', html)
        for warning in ("click here", "no header cells", "has no title", "colour did not carry meaning"):
            self.assertTrue(any(warning in item for item in self.result.warnings), warning)

    def test_teacher_decisions_block_saving_instead_of_guessing(self) -> None:
        self.assertFalse(self.result.ok)
        self.assertTrue(any("base64" in item for item in self.result.blocking))
        self.assertTrue(any("no alt text" in item for item in self.result.blocking))
        fixed = self.source.replace('<p><img src="/courses/1234/files/3456/preview"></p>', '<p><img src="/courses/1234/files/3456/preview" alt=""></p>')
        fixed = fixed.replace('<p><img src="data:image/png;base64,iVBORw0KGgo=" alt="Tiny embedded diagram"></p>', "")
        self.assertTrue(canvas_safe.transform(fixed).ok, canvas_safe.transform(fixed).blocking)

    def test_unsupported_content_is_reported_not_silently_dropped(self) -> None:
        result = canvas_safe.transform('<p>Before</p><object data="/x.swf"><p>Fallback words</p></object><svg><text>Chart</text></svg>'
                                       '<p><a href="javascript:alert(1)">Run</a></p><input value="Type here">')
        joined = " ".join(result.blocking)
        self.assertIn("<object>", joined)
        self.assertIn("<svg>", joined)
        self.assertIn("protocol Canvas removes", joined)
        self.assertIn("form field", joined)
        self.assertIn("lost in conversion", joined)

    def test_conversion_is_idempotent(self) -> None:
        again = canvas_safe.transform(self.result.html)
        self.assertEqual(self.result.html, again.html)
        self.assertEqual(1, again.html.count('data-aac-canvas-safe="1"'))

    def test_house_colours_meet_wcag_aa(self) -> None:
        styles = canvas_safe.load_styles()
        for foreground, background in styles["checkedPairs"]:
            self.assertGreaterEqual(canvas_safe.contrast_ratio(foreground, background), 4.5, (foreground, background))
        colours = set(re.findall(r"color: (#[0-9a-f]{6})", json.dumps(styles["elements"]) + styles["standaloneLink"] + styles["wrapper"]))
        checked = {pair[0] for pair in styles["checkedPairs"]}
        self.assertLessEqual(colours, checked, "every text colour in the house styles is in checkedPairs")

    def test_complex_css_rules_are_reported(self) -> None:
        result = canvas_safe.transform("<style>a:hover{color:red} @media print{p{display:none}} .ok{font-weight:bold}</style><p class='ok'>Hi</p>")
        self.assertIn("font-weight: bold", result.html)
        self.assertTrue(any("cannot be inlined" in warning for warning in result.warnings))

    def test_command_line_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out, report = Path(tmp) / "out.html", Path(tmp) / "report.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(2, canvas_safe.main([str(FIXTURE), str(out), "--report", str(report)]))
            self.assertFalse(json.loads(report.read_text(encoding="utf-8"))["ok"])
            clean = Path(tmp) / "clean.html"
            clean.write_text("<h2>Title</h2><p>Body text.</p>", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, canvas_safe.main([str(clean), str(out)]))


class CompareSavedPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sent = canvas_safe.transform("<h2>Plan</h2><p>Read the <a href='https://qlearn.eq.edu.au/courses/1/files/2/download?wrap=1'>worksheet</a>.</p>"
                                          "<p><img src='/courses/1/files/3/preview' alt='Diagram of the water cycle'></p>").html

    def test_identical_save_is_intact(self) -> None:
        result = compare_saved.compare(self.sent, self.sent)
        self.assertTrue(result["contentIntact"])
        self.assertEqual([], result["stylesRemoved"])

    def test_canvas_link_rewrites_are_not_losses(self) -> None:
        saved = self.sent.replace("https://qlearn.eq.edu.au/courses/1/files/2/download?wrap=1", "/courses/1/files/2/download?verifier=abc&amp;wrap=1")
        self.assertTrue(compare_saved.compare(self.sent, saved)["contentIntact"])

    def test_missing_content_and_stripped_styles_are_reported(self) -> None:
        saved = re.sub(r"<a [^>]*>worksheet</a>", "worksheet", self.sent).replace("text-underline-offset: 0.15em;", "")
        saved = saved.replace("Diagram of the water cycle", "")
        result = compare_saved.compare(self.sent, saved)
        self.assertFalse(result["contentIntact"])
        self.assertEqual(1, len(result["lost"]["links"]))
        self.assertEqual(1, len(result["lost"]["images"]))
        self.assertTrue(any("text-underline-offset" in item for item in result["stylesRemoved"]))

    def test_command_line_compares_against_the_original(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sent, saved, source = Path(tmp) / "sent.html", Path(tmp) / "saved.html", Path(tmp) / "source.html"
            source.write_text("<h2>Plan</h2><p>Read the worksheet.</p>", encoding="utf-8")
            sent.write_text(canvas_safe.transform(source.read_text()).html, encoding="utf-8")
            saved.write_text(sent.read_text(), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(0, compare_saved.main([str(sent), str(saved), "--source", str(source)]))
            self.assertIn("content intact", output.getvalue())
            saved.write_text(sent.read_text().replace("worksheet", ""), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(2, compare_saved.main([str(sent), str(saved)]))


if __name__ == "__main__":
    unittest.main()

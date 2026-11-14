"""The one-command build and the readable outline that agents rely on."""

import base64
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "agentic-aac-board-maker"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_board  # noqa: E402
import inspect_board  # noqa: E402

SKELETON = SKILL / "templates" / "board-json-skeleton.json"
SHOPS_DIR = ROOT / "generated" / "qcia-community-shops"
SHOPS = SHOPS_DIR / "qcia-community-shops.ir.json"
HOUSE_SYMBOL = SKILL / "assets" / "house-symbols" / "arasaac-5431.png"


def gaze_source(target=132, why_label="Why did that happen?"):
    """A small eye-gaze science board, written the way an agent would write it."""
    return {
        "id": "states-of-matter",
        "title": "States of matter",
        "purpose": "Student makes observations and predictions in a science practical.",
        "audience": {"ageBand": "secondary"},
        "access": {"intended": ["eye-gaze-dwell", "keyboard"], "profile": "eye-gaze-dwell", "minimumTargetSizePx": target, "dwellTimeMs": 1000},
        "communicationFunctions": ["comment", "explain", "ask", "repair", "regulate-rest"],
        "pages": [{
            "id": "page-observe", "name": "Observe", "grid": {"rows": 3, "columns": 3},
            "buttons": [
                {"id": "btn-melting", "label": "It is melting", "role": "evidence", "function": "comment", "wordClass": "verb", "searchTerm": "melt"},
                {"id": "btn-predict", "label": "I think it will change", "role": "evidence", "function": "explain", "wordClass": "verb", "searchTerm": "think"},
                {"id": "btn-why", "label": why_label, "spokenText": "Why did that happen?", "role": "question", "function": "ask", "wordClass": "question", "searchTerm": "why"},
                {"id": "btn-help", "label": "Help"},
                {"id": "btn-different", "label": "Different"},
                {"id": "btn-finished", "label": "Finished"},
            ],
        }],
    }


def write_source(folder, source, name="board.source.json"):
    path = Path(folder) / name
    path.write_text(json.dumps(source, indent=2), encoding="utf-8")
    return path


def step(report, name):
    return next(item for item in report.steps if item["name"] == name)


class StarterSkeletonTests(unittest.TestCase):
    def test_skeleton_is_small_enough_for_an_agent_to_read(self):
        text = SKELETON.read_text(encoding="utf-8")
        self.assertNotIn("data:", text)
        self.assertLess(len(text), 20_000)

    def test_skeleton_builds_a_complete_pack_and_then_checks_clean(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "starter.source.json"
            shutil.copy(SKELETON, source)
            report = build_board.build(source)
            self.assertTrue(report.passed, report.steps)
            for name in ("starter.ir.json", "starter.html", "partner-card.html", "starter.obz"):
                self.assertTrue((Path(tmp) / name).exists(), name)
            self.assertEqual(json.loads(SKELETON.read_text(encoding="utf-8")), json.loads(source.read_text(encoding="utf-8")), "the source file must not be modified")
            self.assertTrue(build_board.build(source, check=True).passed)


class BuildGateTests(unittest.TestCase):
    def test_page_too_tall_for_the_screen_fails_with_the_size_that_fits(self):
        with TemporaryDirectory() as tmp:
            report = build_board.build(write_source(tmp, gaze_source(target=160)))
            self.assertFalse(report.passed)
            fit = step(report, "screen fit")
            self.assertEqual("fail", fit["status"])
            self.assertIn("bottom row", fit["detail"])
            self.assertIn("132 px or less", fit["detail"])

    def test_confirmed_larger_viewport_lets_the_same_board_pass(self):
        with TemporaryDirectory() as tmp:
            report = build_board.build(write_source(tmp, gaze_source(target=160)), floor=(1280, 720))
            self.assertTrue(report.passed, report.steps)

    def test_house_word_label_reports_the_replaced_wording(self):
        with TemporaryDirectory() as tmp:
            report = build_board.build(write_source(tmp, gaze_source(why_label="Why?")))
            self.assertTrue(report.passed, report.steps)
            self.assertEqual(1, len(report.rewrites))
            self.assertIn("btn-why", report.rewrites[0])
            self.assertIn("Why did that happen?", report.rewrites[0])

    def test_own_phrase_with_its_own_label_is_left_alone(self):
        with TemporaryDirectory() as tmp:
            report = build_board.build(write_source(tmp, gaze_source()))
            self.assertEqual([], report.rewrites)
            built = json.loads((Path(tmp) / "board.ir.json").read_text(encoding="utf-8"))
            why = next(button for page in built["pages"] for button in page["buttons"] if button["id"] == "btn-why")
            self.assertEqual("Why did that happen?", why["spokenText"])

    def test_quiz_only_page_fails_even_though_house_standards_add_help_elsewhere(self):
        """The added spelling and core-word pages must not mask an answer-only page with no Help."""
        source = gaze_source()
        source["pages"][0]["buttons"] = [
            {"id": f"btn-{index}", "label": f"Thing {index}", "role": "evidence", "function": "answer", "wordClass": "noun"} for index in range(4)
        ]
        source["communicationFunctions"] = ["answer"]
        with TemporaryDirectory() as tmp:
            report = build_board.build(write_source(tmp, source))
            self.assertFalse(report.passed)
            detail = step(report, "board validation")["detail"]
            self.assertIn("no repair/refusal/finished route", detail)
            self.assertIn("quiz-only or answer-only", detail)
            self.assertEqual(["board.source.json"], sorted(path.name for path in Path(tmp).iterdir()), "an invalid board writes nothing")

    def test_answer_page_with_agency_and_help_still_passes(self):
        source = gaze_source()
        source["pages"][0]["buttons"] = [
            {"id": "btn-solid", "label": "Solid", "role": "evidence", "function": "answer", "wordClass": "noun"},
            {"id": "btn-liquid", "label": "Liquid", "role": "evidence", "function": "answer", "wordClass": "noun"},
            {"id": "btn-gas", "label": "Gas", "role": "evidence", "function": "answer", "wordClass": "noun"},
            {"id": "btn-unsure", "label": "I'm not sure", "role": "comment", "function": "comment", "wordClass": "social"},
            {"id": "btn-help", "label": "Help"},
            {"id": "btn-finished", "label": "Finished"},
        ]
        with TemporaryDirectory() as tmp:
            report = build_board.build(write_source(tmp, source))
            self.assertTrue(report.passed, report.steps)

    def test_overfull_page_explains_the_fix(self):
        source = gaze_source()
        source["pages"][0]["buttons"] += [
            {"id": f"btn-extra-{index}", "label": f"Extra {index}", "role": "fringe", "function": "comment", "wordClass": "noun"} for index in range(4)
        ]
        with TemporaryDirectory() as tmp:
            report = build_board.build(write_source(tmp, source))
            self.assertFalse(report.passed)
            self.assertIn("Split the page", step(report, "house standards")["detail"])

    def test_check_mode_catches_a_hand_edited_render_and_changes_nothing(self):
        with TemporaryDirectory() as tmp:
            source = write_source(tmp, gaze_source())
            self.assertTrue(build_board.build(source).passed)
            html = Path(tmp) / "board.html"
            edited = html.read_text(encoding="utf-8") + "\n<!-- hand edit -->\n"
            html.write_text(edited, encoding="utf-8")
            report = build_board.build(source, check=True)
            self.assertFalse(report.passed)
            self.assertEqual("fail", step(report, "HTML board")["status"])
            self.assertEqual(edited, html.read_text(encoding="utf-8"))

    def test_check_mode_reports_a_board_that_was_never_built(self):
        with TemporaryDirectory() as tmp:
            report = build_board.build(write_source(tmp, gaze_source()), check=True)
            self.assertFalse(report.passed)
            self.assertIn("not been built", step(report, "house standards")["detail"])

    def test_switch_scanning_points_to_the_interchange_export(self):
        source = gaze_source()
        source["access"] = {"intended": ["single-switch", "keyboard"], "profile": "single-switch", "switchScanning": True, "minimumTargetSizePx": 120}
        with TemporaryDirectory() as tmp:
            report = build_board.build(write_source(tmp, source))
            self.assertFalse(report.passed)
            self.assertIn("--formats obf,partner-card", step(report, "HTML board")["detail"])
            self.assertTrue(build_board.build(write_source(tmp, source), formats=("obf", "partner-card")).passed)

    def test_command_line_exit_status_matches_the_result(self):
        with TemporaryDirectory() as tmp:
            good = write_source(tmp, gaze_source(), "good.source.json")
            bad = write_source(tmp, gaze_source(target=160), "bad.source.json")
            run = lambda path: subprocess.run([sys.executable, str(SCRIPTS / "build_board.py"), str(path), "--quiet"], capture_output=True, text=True)  # noqa: E731
            passed, failed = run(good), run(bad)
            self.assertEqual(0, passed.returncode, passed.stdout + passed.stderr)
            self.assertIn("BUILD PASSED", passed.stdout)
            self.assertEqual(1, failed.returncode)
            self.assertIn("BUILD FAILED", failed.stdout)


class ReviewedSymbolTests(unittest.TestCase):
    def approve_symbol(self, ir_path, button_id):
        """Stand in for fetch_arasaac_symbols.py --apply-review, which embeds an approved picture."""
        data = json.loads(ir_path.read_text(encoding="utf-8"))
        uri = "data:image/png;base64," + base64.b64encode(HOUSE_SYMBOL.read_bytes()).decode("ascii")
        for page in data["pages"]:
            for button in page["buttons"]:
                if button["id"] == button_id:
                    button["symbolId"], button["symbolSrc"] = 5431, uri
        ir_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def symbol_of(self, ir_path, button_id):
        data = json.loads(ir_path.read_text(encoding="utf-8"))
        return next(button for page in data["pages"] for button in page["buttons"] if button["id"] == button_id).get("symbolSrc", "")

    def test_reviewed_symbol_survives_a_rebuild_from_the_source(self):
        with TemporaryDirectory() as tmp:
            source = write_source(tmp, gaze_source())
            build_board.build(source)
            built = Path(tmp) / "board.ir.json"
            self.approve_symbol(built, "btn-melting")
            self.assertFalse(build_board.build(built, check=True).passed, "renders are stale after a review")
            self.assertTrue(build_board.build(built).passed, "rebuilding in place re-renders")
            report = build_board.build(source)
            self.assertEqual(1, report.carried_symbols)
            self.assertTrue(self.symbol_of(built, "btn-melting").startswith("data:image/png"))

    def test_changed_meaning_goes_back_to_review(self):
        with TemporaryDirectory() as tmp:
            content = gaze_source()
            source = write_source(tmp, content)
            build_board.build(source)
            built = Path(tmp) / "board.ir.json"
            self.approve_symbol(built, "btn-melting")
            content["pages"][0]["buttons"][0].update({"label": "It is freezing", "searchTerm": "freeze"})
            report = build_board.build(write_source(tmp, content))
            self.assertEqual(0, report.carried_symbols)
            self.assertEqual("", self.symbol_of(built, "btn-melting"))

    def test_carry_can_be_switched_off(self):
        with TemporaryDirectory() as tmp:
            source = write_source(tmp, gaze_source())
            build_board.build(source)
            built = Path(tmp) / "board.ir.json"
            self.approve_symbol(built, "btn-melting")
            self.assertEqual(0, build_board.build(source, carry_symbols=False).carried_symbols)
            self.assertEqual("", self.symbol_of(built, "btn-melting"))


class ShippedExampleTests(unittest.TestCase):
    def test_every_shipped_example_passes_the_check(self):
        for ir in sorted((ROOT / "generated").glob("*/*.ir.json")):
            with self.subTest(board=ir.parent.name):
                report = build_board.build(ir, check=True)
                self.assertTrue(report.passed, report.steps)

    def test_rebuilding_a_shipped_example_reproduces_it(self):
        with TemporaryDirectory() as tmp:
            copy = Path(tmp) / "shops"
            shutil.copytree(SHOPS_DIR, copy)
            report = build_board.build(copy / SHOPS.name)
            self.assertTrue(report.passed, report.steps)
            for name in (SHOPS.name, "qcia-community-shops.html", "partner-card.html"):
                self.assertEqual((SHOPS_DIR / name).read_bytes(), (copy / name).read_bytes(), name)
            # Zip containers differ between zlib builds; the files inside must be identical.
            self.assertTrue(build_board.same_obf(SHOPS_DIR / "qcia-community-shops.obz", copy / "qcia-community-shops.obz"))


class OutlineTests(unittest.TestCase):
    def test_outline_is_a_small_fraction_of_the_built_file(self):
        raw = SHOPS.read_text(encoding="utf-8")
        summary = inspect_board.summarise(json.loads(raw), raw)
        text = inspect_board.render_text(summary)
        self.assertGreater(len(raw), 300_000)
        self.assertLess(len(text), 12_000)
        self.assertNotIn("base64", text)
        self.assertGreater(summary["file"]["embeddedImageBytes"], 0.5 * summary["file"]["bytes"])

    def test_outline_shows_house_words_at_their_addresses(self):
        raw = SHOPS.read_text(encoding="utf-8")
        summary = inspect_board.summarise(json.loads(raw), raw)
        first = summary["pages"][0]
        by_cell = {(button.get("row"), button.get("column")): button for button in first["buttons"]}
        self.assertEqual("help", by_cell[(first["rows"], 1)].get("houseWord"))
        self.assertFalse(first["generated"])
        self.assertTrue(any(page["generated"] for page in summary["pages"]))

    def test_attention_separates_failures_from_to_do_items(self):
        with TemporaryDirectory() as tmp:
            build_board.build(write_source(tmp, gaze_source()))
            raw = (Path(tmp) / "board.ir.json").read_text(encoding="utf-8")
        attention = inspect_board.summarise(json.loads(raw), raw)["attention"]
        levels = {item["level"] for item in attention}
        self.assertNotIn("fail", levels)
        todo = " ".join(item["text"] for item in attention if item["level"] == "todo")
        self.assertIn("own words have no symbol", todo)
        self.assertIn("It is melting", todo)
        self.assertNotIn("don't", todo, "house words are covered by the house symbol review")
        self.assertIn("partnerCard is the tool default", todo)

    def test_unbuilt_source_is_recognised_rather_than_failed(self):
        attention = inspect_board.summarise(gaze_source(), "")["attention"]
        self.assertFalse(any("must record house standards" in item["text"] for item in attention))
        self.assertTrue(any("not applied yet" in item["text"] for item in attention))

    def test_single_page_view_and_json_output(self):
        page = subprocess.run([sys.executable, str(SCRIPTS / "inspect_board.py"), str(SHOPS), "--page", "page-keyboard"], capture_output=True, text=True)
        self.assertEqual(0, page.returncode, page.stderr)
        self.assertIn("row 1:", page.stdout)
        as_json = subprocess.run([sys.executable, str(SCRIPTS / "inspect_board.py"), str(SHOPS), "--json"], capture_output=True, text=True)
        self.assertEqual("qcia-community-shops", json.loads(as_json.stdout)["board"]["id"])


if __name__ == "__main__":
    unittest.main()

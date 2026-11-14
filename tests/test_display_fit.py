"""Screen-fit maths: the bottom row (Help, Different, Finished) must stay on the screen."""

import importlib.util
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "agentic-aac-board-maker" / "scripts"
CHECKER = ROOT / "skills" / "accent-display-fit" / "scripts" / "check_accent_display.py"
sys.path.insert(0, str(SCRIPTS))

import display_fit  # noqa: E402
from apply_house_standards import apply  # noqa: E402
from validate_board_ir import validate  # noqa: E402


def load_checker():
    spec = importlib.util.spec_from_file_location("check_accent_display_for_tests", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def board(target, rows=3, columns=3, profile="eye-gaze-dwell", message_bar=True, **extra):
    ir = {
        "access": {"profile": profile, "intended": [profile, "keyboard"], "minimumTargetSizePx": target},
        "pages": [{"id": "page-main", "grid": {"rows": rows, "columns": columns}, "buttons": []}],
    }
    if message_bar:
        ir["messageBar"] = {"enabled": True}
    ir.update(extra)
    return ir


def page_html(grids, with_message_bar_element):
    pages = "".join(f'<div class="board-grid" style="--grid-rows:{rows};--grid-columns:{columns}"><button>Talk</button></div>' for rows, columns in grids)
    bar = '<section class="message-bar"></section>' if with_message_bar_element else ""
    return textwrap.dedent(
        f"""\
        <!doctype html>
        <html lang="en-AU"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>:root {{ --min-target: 150px; }} .message-bar {{ min-height: 60px; }} .board-grid {{ display: grid; gap: 12px; }}</style>
        </head><body>{bar}{pages}<noscript>Tell your teacher.</noscript></body></html>
        """
    )


def run_checker(html):
    with TemporaryDirectory() as tmp:
        candidate = Path(tmp) / "candidate.html"
        candidate.write_text(html, encoding="utf-8")
        return subprocess.run([sys.executable, str(CHECKER), str(candidate)], text=True, capture_output=True, check=False)


class FitMathsTests(unittest.TestCase):
    def test_both_copies_of_the_constants_agree(self):
        checker = load_checker()
        self.assertEqual(checker.CHROME_PLAIN, display_fit.CHROME_PLAIN)
        self.assertEqual(checker.CHROME_MESSAGE_BAR, display_fit.CHROME_MESSAGE_BAR)
        self.assertEqual(checker.DEFAULT_GAP, display_fit.GAP)
        self.assertEqual(checker.PROFILES["mustfit"], display_fit.MUST_FIT_FLOOR)

    def test_largest_targets_at_the_must_fit_floor(self):
        bar, plain = display_fit.CHROME_MESSAGE_BAR, display_fit.CHROME_PLAIN
        self.assertEqual(132, display_fit.largest_target(3, 3, bar))
        self.assertEqual(155, display_fit.largest_target(3, 3, plain))
        self.assertEqual(204, display_fit.largest_target(2, 3, bar))
        self.assertEqual(239, display_fit.largest_target(2, 3, plain))

    def test_shipped_target_size_fits_and_a_larger_one_is_cut_off(self):
        self.assertTrue(display_fit.board_fit(board(132))[0]["fits"])
        entry = display_fit.board_fit(board(160))[0]
        self.assertFalse(entry["fits"])
        self.assertEqual(84, entry["overflowPx"])
        self.assertEqual(132, entry["largestTarget"])
        self.assertIn("bottom row", display_fit.describe(entry))

    def test_confirmed_taller_viewport_fits_the_larger_target(self):
        self.assertTrue(display_fit.board_fit(board(160), floor=(1280, 720))[0]["fits"])

    def test_one_page_keyboard_needs_room_for_the_stop_speech_column(self):
        entry = display_fit.board_fit(board(96, rows=4, columns=11, profile="direct-selection"))[0]
        self.assertEqual(1308, entry["neededWidth"])
        self.assertFalse(entry["fits"])
        self.assertEqual(0, entry["overflowPx"])
        self.assertEqual(92, entry["largestTarget"])
        self.assertIn("92 px or less", display_fit.describe(entry))
        without_stop = board(96, rows=4, columns=11, profile="direct-selection", studentControls={"stopSpeechDuringPlayback": False})
        self.assertTrue(display_fit.board_fit(without_stop)[0]["fits"])

    def test_cvi_profile_uses_its_wider_gaps(self):
        standard = display_fit.board_fit(board(132))[0]["neededHeight"]
        cvi = display_fit.board_fit(board(132, display={"visualProfile": "cvi"}))[0]["neededHeight"]
        self.assertEqual(24, cvi - standard)

    def test_print_boards_are_not_screen_checked(self):
        self.assertFalse(display_fit.is_on_screen(board(160, profile="print-only")))
        self.assertTrue(display_fit.is_on_screen(board(160)))


class ValidatorFitTests(unittest.TestCase):
    def source(self, target):
        return {
            "id": "fit-board", "title": "Fit", "purpose": "Fit test", "audience": {"ageBand": "secondary"},
            "access": {"intended": ["eye-gaze-dwell", "keyboard"], "profile": "eye-gaze-dwell", "minimumTargetSizePx": target},
            "communicationFunctions": ["comment", "repair"],
            "pages": [{"id": "page-main", "name": "Main", "grid": {"rows": 3, "columns": 3}, "buttons": [
                {"id": "btn-like", "label": "I like it"}, {"id": "btn-help", "label": "Help"}, {"id": "btn-finished", "label": "Finished"},
            ]}],
        }

    def test_validator_warns_when_the_bottom_row_would_be_cut_off(self):
        ir, _ = apply(self.source(160))
        failures, warnings = validate(ir)
        self.assertEqual([], failures)
        fit = [warning for warning in warnings if warning.startswith("Screen fit:")]
        self.assertEqual(1, len(fit), "one warning per grid size, not one per page")
        self.assertIn("132 px or less", fit[0])

    def test_validator_is_quiet_when_the_board_fits(self):
        ir, _ = apply(self.source(132))
        _, warnings = validate(ir)
        self.assertFalse([warning for warning in warnings if warning.startswith("Screen fit:")])

    def test_page_without_a_repair_word_is_flagged(self):
        source = self.source(132)
        source["pages"].append({"id": "page-two", "name": "More", "grid": {"rows": 3, "columns": 3}, "buttons": [
            {"id": "btn-hot", "label": "It is hot", "role": "comment", "function": "comment", "wordClass": "describing"},
            {"id": "btn-cold", "label": "It is cold", "role": "comment", "function": "comment", "wordClass": "describing"},
            {"id": "btn-wet", "label": "It is wet", "role": "comment", "function": "comment", "wordClass": "describing"},
        ]})
        ir, _ = apply(source)
        _, warnings = validate(ir)
        flagged = [warning for warning in warnings if "no Help or other repair word" in warning]
        self.assertEqual(1, len(flagged))
        self.assertTrue(flagged[0].startswith("page-two"))


class AccentCheckerTests(unittest.TestCase):
    def test_message_bar_css_without_the_element_uses_plain_chrome(self):
        result = run_checker(page_html([(3, 3)], with_message_bar_element=False))
        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("needs ~498x584px", result.stdout)

    def test_message_bar_element_uses_message_bar_chrome(self):
        result = run_checker(page_html([(3, 3)], with_message_bar_element=True))
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("needs ~498x654px", result.stdout)

    def test_repeated_grid_size_is_reported_once(self):
        result = run_checker(page_html([(3, 3)] * 6, with_message_bar_element=True))
        self.assertEqual(1, result.stdout.count("FAIL 3x3 grid"), result.stdout)


if __name__ == "__main__":
    unittest.main()

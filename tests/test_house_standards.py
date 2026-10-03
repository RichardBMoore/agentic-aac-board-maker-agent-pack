import copy
import json
import sys
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "agentic-aac-board-maker" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import house_standards as hs  # noqa: E402
from apply_house_standards import HouseError, apply  # noqa: E402
from output_layout import grid_slots  # noqa: E402
from render_obf import render_boards, write_obz  # noqa: E402
from render_partner_card import render as render_card  # noqa: E402
from validate_board_ir import validate  # noqa: E402

SHOPS = ROOT / "generated" / "qcia-community-shops" / "qcia-community-shops.ir.json"
NEEDS = ROOT / "generated" / "needs-repair-board" / "secondary-needs-repair-board.ir.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def cell_of(ir, button_id):
    for page in ir["pages"]:
        for row, column, button in grid_slots(page):
            if button["id"] == button_id:
                return page["id"], (row + 1, column + 1)
    raise KeyError(button_id)


def minimal(buttons, rows=3, columns=3, **extra):
    ir = {
        "id": "test-board", "title": "Test", "purpose": "Test board", "audience": {"ageBand": "secondary", "tone": "age-respectful", "locale": "en-AU"},
        "access": {"intended": ["touch", "keyboard"], "profile": "direct-selection", "visibleTargetLimit": 9},
        "communicationFunctions": ["choose", "repair"],
        "pages": [{"id": "page-main", "name": "Main", "grid": {"rows": rows, "columns": columns}, "buttons": buttons}],
        "privacy": {"level": "anonymous", "containsSensitiveData": False},
    }
    ir.update(extra)
    return ir


def word(bid, label, wc="noun"):
    return {"id": bid, "label": label, "wordClass": wc, "role": "fringe", "function": "choose", "spokenText": label}


class HouseAddressTests(unittest.TestCase):
    def test_house_addresses_follow_the_corners(self):
        self.assertEqual((3, 1), hs.house_address("help", 3, 3))
        self.assertEqual((3, 3), hs.house_address("finished", 3, 3))
        self.assertEqual((3, 2), hs.house_address("different", 3, 3))
        self.assertEqual((1, 3), hs.house_address("stop", 3, 3))
        self.assertEqual((2, 3), hs.house_address("nav", 3, 3))
        self.assertEqual((2, 1), hs.house_address("keyboard", 3, 3))
        self.assertEqual((2, 1), hs.house_address("nav-back", 3, 3))
        self.assertEqual((4, 1), hs.house_address("help", 4, 5))
        self.assertEqual((4, 3), hs.house_address("different", 4, 5))
        self.assertEqual((2, 1), hs.house_address("help", 2, 3))
        self.assertIsNone(hs.house_address("different", 2, 2))
        self.assertIsNone(hs.house_address("help", 1, 4))

    def test_labels_match_house_words_but_letters_never_do(self):
        self.assertEqual("help", hs.lexicon_match("Help please"))
        self.assertEqual("wait", hs.lexicon_match("Please wait"))
        self.assertIsNone(hs.lexicon_match("Stop / wait"))  # ambiguous: choose Stop or Wait explicitly
        self.assertEqual("speak-message", hs.lexicon_match("🔊 Speak sentence"))
        self.assertEqual("i", hs.lexicon_match("I"))
        self.assertIsNone(hs.lexicon_match("i", "letter"))
        self.assertIsNone(hs.lexicon_match("Art"))

    def test_every_proposed_house_symbol_ships_with_the_pack(self):
        for word_id, entry in hs.words().items():
            symbol = entry["symbol"]
            if symbol["status"] in {"proposed", "approved"}:
                self.assertTrue((hs.SYMBOL_DIR / f"arasaac-{symbol['id']}.png").exists(), word_id)
        self.assertTrue((hs.SYMBOL_DIR / "LICENCE.md").exists())


class ApplyHouseStandardsTests(unittest.TestCase):
    def test_shipped_fixtures_are_idempotent(self):
        for path in sorted((ROOT / "generated").glob("*/*.ir.json")):
            raw = load(path)
            result, _ = apply(raw)
            self.assertEqual(raw, result, path.name)

    def test_help_moves_to_bottom_left_and_speaks_the_house_message(self):
        ir = minimal([word("btn-help", "Help please", "important"), word("btn-a", "Apples"), word("btn-b", "Bread")])
        result, report = apply(ir)
        self.assertEqual(("page-main", (3, 1)), cell_of(result, "btn-help"))
        help_button = next(b for b in result["pages"][0]["buttons"] if b["id"] == "btn-help")
        self.assertEqual(("Help", "Help please", "help"), (help_button["label"], help_button["spokenText"], help_button["lexiconId"]))
        self.assertTrue(any("matched house word 'help'" in line for line in report))

    def test_literacy_pages_keyboard_and_message_bar_are_added(self):
        ir = minimal([word("btn-a", "Apples"), word("btn-b", "Bread"), word("btn-help", "Help", "important")])
        result, _ = apply(ir)
        patterns = [page["pattern"] for page in result["pages"]]
        self.assertIn("core-words", patterns)
        self.assertIn("word-endings", patterns)
        self.assertIn("keyboard", patterns)
        self.assertEqual(5, patterns.count("keyboard-letters"))
        self.assertTrue(result["messageBar"]["enabled"])
        self.assertEqual(("page-main", (2, 1)), cell_of(result, "btn-keyboard"))
        letters = {b["label"] for page in result["pages"] if page["pattern"] == "keyboard-letters" for b in page["buttons"] if b.get("wordClass") == "letter"}
        self.assertEqual(set("abcdefghijklmnopqrstuvwxyz"), letters)
        self.assertEqual(([], []), (validate(result)[0], []))

    def test_small_boards_record_why_the_keyboard_is_omitted(self):
        ir = minimal([word("btn-a", "Apples"), word("btn-b", "Bread"), word("btn-help", "Help", "important")], rows=2, columns=3)
        result, _ = apply(ir)
        self.assertFalse(result["literacy"]["keyboard"]["enabled"])
        self.assertIn("3x3", result["literacy"]["keyboard"]["omitReason"])
        self.assertEqual(1, len(result["pages"]))

    def test_community_boards_get_the_introduction(self):
        ir = minimal([word("btn-a", "Apples"), word("btn-help", "Help", "important")])
        ir["audience"]["settings"] = ["community"]
        result, _ = apply(ir)
        self.assertTrue(any(b.get("lexiconId") == "how-i-talk" for b in result["pages"][0]["buttons"]))

    def test_overfull_page_asks_for_a_split(self):
        ir = minimal([word(f"btn-{index}", f"Item {index}") for index in range(8)] + [word("btn-help", "Help", "important")])
        with self.assertRaises(HouseError):
            apply(ir)

    def test_colour_follows_word_class(self):
        ir = minimal([word("btn-a", "run", "verb"), word("btn-b", "big", "describing"), word("btn-help", "Help", "important")])
        result, _ = apply(ir)
        fills = {b["id"]: b["style"]["fillColour"] for b in result["pages"][0]["buttons"] if b["id"] in {"btn-a", "btn-b"}}
        scheme = hs.load_settings()["colourSchemes"]["modified-fitzgerald"]["fills"]
        self.assertEqual({"btn-a": scheme["verb"], "btn-b": scheme["describing"]}, fills)

    def test_talking_pages_link_forward_and_back(self):
        result = load(NEEDS)
        repair = next(page for page in result["pages"] if page["id"] == "page-repair")
        kinds = sorted(action["type"] for b in repair["buttons"] if b["role"] == "navigation" for action in b["actions"] if "page" in action["type"])
        self.assertEqual(["navigate-page", "previous-page"], kinds)


class ValidatorHouseTests(unittest.TestCase):
    def setUp(self):
        self.ir = load(SHOPS)

    def test_shipped_board_passes(self):
        self.assertEqual([], validate(self.ir)[0])

    def test_same_label_different_message_fails(self):
        wait = next(b for b in self.ir["pages"][0]["buttons"] if b.get("lexiconId") == "wait")
        wait["spokenText"] = "I need to wait"
        self.assertTrue(any("house word 'wait'" in failure for failure in validate(self.ir)[0]))

    def test_house_word_without_lexicon_id_fails(self):
        wait = next(b for b in self.ir["pages"][0]["buttons"] if b.get("lexiconId") == "wait")
        del wait["lexiconId"]
        self.assertTrue(any("is the house word 'wait'" in failure for failure in validate(self.ir)[0]))

    def test_moved_house_word_fails(self):
        page = self.ir["pages"][0]
        help_button = next(b for b in page["buttons"] if b.get("lexiconId") == "help")
        hello = next(b for b in page["buttons"] if b.get("lexiconId") == "hello")
        help_button["position"], hello["position"] = hello["position"], help_button["position"]
        self.assertTrue(any("must sit at house address row 3, column 1" in failure for failure in validate(self.ir)[0]))

    def test_student_system_layout_skips_house_addresses(self):
        page = self.ir["pages"][0]
        help_button = next(b for b in page["buttons"] if b.get("lexiconId") == "help")
        hello = next(b for b in page["buttons"] if b.get("lexiconId") == "hello")
        help_button["position"], hello["position"] = hello["position"], help_button["position"]
        self.ir["house"].update({"layoutSource": "student-system", "layoutNote": "Matches the student's own device layout."})
        self.assertEqual([], validate(self.ir)[0])

    def test_missing_keyboard_route_fails(self):
        page = self.ir["pages"][0]
        page["buttons"] = [b for b in page["buttons"] if b.get("lexiconId") != "keyboard"]
        self.assertTrue(any("ABC" in failure for failure in validate(self.ir)[0]))

    def test_community_board_without_introduction_fails(self):
        page = self.ir["pages"][0]
        page["buttons"] = [b for b in page["buttons"] if b.get("lexiconId") != "how-i-talk"]
        self.assertTrue(any("How I talk" in failure for failure in validate(self.ir)[0]))

    def test_partner_card_must_name_real_buttons_and_wait_five_seconds(self):
        self.ir["partnerCard"]["modelWords"][0] = "btn-missing"
        self.ir["partnerCard"]["waitSeconds"] = 2
        failures = validate(self.ir)[0]
        self.assertTrue(any("btn-missing" in failure for failure in failures))
        self.assertTrue(any("at least 5" in failure for failure in failures))

    def test_schedule_steps_must_exist(self):
        schedule_ir = load(ROOT / "generated" / "visual-schedule-expressive" / "morning-routine-expressive-schedule.ir.json")
        schedule_ir["pages"][0]["schedule"]["steps"].append("btn-nowhere")
        self.assertTrue(any("btn-nowhere" in failure for failure in validate(schedule_ir)[0]))

    def test_new_ir_must_record_house_standards(self):
        del self.ir["house"]
        self.assertTrue(any("house standards" in failure for failure in validate(self.ir)[0]))

    def test_hidden_buttons_do_not_count_as_targets(self):
        page = copy.deepcopy(self.ir["pages"][0])
        page["id"] = "page-extra"
        page["buttons"] = [dict(b, id=b["id"] + "-x") for b in page["buttons"]]
        self.ir["pages"].append(page)
        page["grid"] = {"rows": 3, "columns": 4}
        page["buttons"].append(dict(word("btn-masked", "Later"), hidden=True, actions=[{"id": "a", "type": "log-attempt"}], searchTerm="", symbolId=None, symbolSrc="", symbolLayout="label-bottom"))
        self.assertFalse(any("exceeding visibleTargetLimit" in failure for failure in validate(self.ir)[0]))


class ExportTests(unittest.TestCase):
    def test_obf_maps_spelling_endings_hidden_and_image_licences(self):
        ir = load(SHOPS)
        ir["pages"][0]["buttons"][1]["hidden"] = True
        boards = {board["id"]: board for board in render_boards(ir)}
        letter = next(b for b in boards["page-keyboard-1"]["buttons"] if b["label"] == "q")
        self.assertEqual("+q", letter["action"])
        self.assertIn("load_board", letter)
        ending = next(b for b in boards["page-word-endings"]["buttons"] if b["label"] == "-ing")
        self.assertEqual(":ext_aac_ending_ing", ending["action"])
        self.assertTrue(boards["page-main"]["buttons"][1]["hidden"])
        image = next(image for image in boards["page-main"]["images"] if "symbol" in image)
        self.assertEqual("CC BY-NC-SA", image["license"]["type"])

    def test_obz_stores_each_picture_once(self):
        boards = render_boards(load(SHOPS))
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "board.obz"
            write_obz(boards, target)
            with zipfile.ZipFile(target) as archive:
                names = archive.namelist()
                manifest = json.loads(archive.read("manifest.json"))
                board = json.loads(archive.read("boards/page-main.obf"))
        images = [name for name in names if name.startswith("images/")]
        self.assertEqual(len(images), len(set(manifest["paths"]["images"].values())))
        self.assertTrue(all("data" not in image and image["path"] in names for image in board["images"]))

    def test_partner_card_lists_model_words_wait_and_no_hand_over_hand(self):
        html = render_card(load(SHOPS))
        self.assertIn("Where is it?", html)
        self.assertIn("15 seconds", html)
        self.assertIn("hand-over-hand", html)
        self.assertIn("Help is bottom-left on every page", html)


class HouseSymbolReviewTests(unittest.TestCase):
    def test_team_review_approves_a_symbol_once_for_every_board(self):
        from review_house_symbols import apply_decisions, build_manifest

        lexicon = copy.deepcopy(hs.load_lexicon())
        fetcher = lambda url: b"[]" if "/search/" in url else b"\x89PNG fake"  # noqa: E731
        manifest = build_manifest(lexicon, limit=1, fetcher=fetcher)
        entry = next(item for item in manifest["entries"] if item["buttonId"] == "help")
        proposed = lexicon["words"]["help"]["symbol"]["id"]
        self.assertEqual(proposed, entry["candidates"][0]["symbolId"])
        entry["approvedSymbolId"] = proposed
        entry["decisionNote"] = "approved"
        stop = next(item for item in manifest["entries"] if item["buttonId"] == "stop")
        stop["decisionNote"] = "text-only"
        report = apply_decisions(lexicon, manifest, fetcher=fetcher)
        self.assertIn(f"help: approved symbol {proposed}", report)
        self.assertEqual("approved", lexicon["words"]["help"]["symbol"]["status"])
        self.assertEqual("none", lexicon["words"]["stop"]["symbol"]["status"])

    def test_stale_review_is_rejected(self):
        from review_house_symbols import apply_decisions

        lexicon = copy.deepcopy(hs.load_lexicon())
        self.assertTrue(apply_decisions(lexicon, {"boardFingerprint": "old", "entries": []})[0].startswith("error"))


if __name__ == "__main__":
    unittest.main()

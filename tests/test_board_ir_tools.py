from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "skills" / "agentic-aac-board-maker" / "scripts" / "validate_board_ir.py"
RENDERER_PATH = ROOT / "skills" / "agentic-aac-board-maker" / "scripts" / "render_open_aac_studio.py"
OBF_RENDERER_PATH = ROOT / "skills" / "agentic-aac-board-maker" / "scripts" / "render_obf.py"
CASES_PATH = ROOT / "tests" / "fixtures" / "validator_cases.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module(VALIDATOR_PATH, "validate_board_ir")
renderer = load_module(RENDERER_PATH, "render_open_aac_studio")
obf_renderer = load_module(OBF_RENDERER_PATH, "render_obf")


class BoardIrValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    def assertValid(self, name: str) -> tuple[list[str], list[str]]:
        failures, warnings = validator.validate(self.cases[name])
        self.assertEqual([], failures, warnings)
        return failures, warnings

    def assertFailsWith(self, name: str, expected: str) -> None:
        failures, _warnings = validator.validate(self.cases[name])
        joined = "\n".join(failures)
        self.assertIn(expected, joined)

    def assertWarnsWith(self, name: str, expected: str) -> tuple[list[str], list[str]]:
        failures, warnings = validator.validate(self.cases[name])
        joined = "\n".join(warnings)
        self.assertIn(expected, joined)
        return failures, warnings

    def test_valid_0_3_passes(self) -> None:
        self.assertValid("valid_0_3")

    def test_legacy_0_2_still_passes(self) -> None:
        self.assertValid("legacy_0_2")

    def test_noun_grid_fails(self) -> None:
        self.assertFailsWith("noun_grid", "noun/content grid")

    def test_quiz_only_fails(self) -> None:
        self.assertFailsWith("quiz_only", "quiz-only")

    def test_missing_privacy_fails(self) -> None:
        self.assertFailsWith("missing_privacy", "Missing privacy level")

    def test_over_dense_gaze_fails(self) -> None:
        self.assertFailsWith("over_dense_gaze", "more than 9 buttons")

    def test_mixed_access_dense_gaze_warns_without_failing(self) -> None:
        failures, _warnings = self.assertWarnsWith(
            "mixed_gaze_dense", "listed in intended access but a page has more than 9 buttons"
        )
        self.assertEqual([], failures)

    def test_missing_repair_route_fails(self) -> None:
        self.assertFailsWith("missing_repair", "no repair/refusal/finished route")

    def test_thin_metadata_is_warning_not_failure(self) -> None:
        failures, warnings = validator.validate(self.cases["legacy_0_2"])
        self.assertEqual([], failures)
        self.assertTrue(any("Differentiation/UDL/SETT metadata is thin" in warning for warning in warnings))

    def test_dense_gaze_string_false_still_fails(self) -> None:
        # denseGazeTested must be boolean true; the string "false" must not lift the limit.
        failures, warnings = validator.validate(self.cases["dense_gaze_string_false"])
        self.assertTrue(any("more than 9 buttons" in failure for failure in failures))
        self.assertTrue(any("denseGazeTested" in warning for warning in warnings))

    def test_duplicate_button_ids_fail(self) -> None:
        self.assertFailsWith("duplicate_button_ids", "Duplicate button id")

    def test_duplicate_page_ids_fail(self) -> None:
        self.assertFailsWith("duplicate_page_ids", "Duplicate page id")

    def test_dangling_navigation_fails(self) -> None:
        self.assertFailsWith("dangling_navigation", "targets unknown page")

    def test_gaze_missing_min_target_fails(self) -> None:
        self.assertFailsWith("gaze_missing_min_target", "must declare a numeric minimumTargetSizePx")

    def test_gaze_zero_min_target_fails(self) -> None:
        self.assertFailsWith("gaze_zero_min_target", "minimumTargetSizePx >= 120")

    def test_multi_page_navigation_passes(self) -> None:
        self.assertValid("multi_page_navigation")

    def test_declared_vs_realised_function_drift_warns(self) -> None:
        drifted = json.loads(json.dumps(self.cases["valid_0_3"]))
        drifted["communicationFunctions"] = ["choose", "comment", "explain", "repair", "reflect"]
        failures, warnings = validator.validate(drifted)
        self.assertEqual([], failures)
        self.assertTrue(any("no button realises" in warning for warning in warnings))


class OpenAacStudioRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    def test_renderer_preserves_ir_powerhouse_metadata(self) -> None:
        rendered = renderer.render(self.cases["valid_0_3"])
        self.assertEqual("Open AAC Studio", rendered["app"])
        self.assertEqual("0.4.0", rendered["metadata"]["sourceIrSchemaVersion"])
        self.assertEqual("eye-gaze-dwell", rendered["metadata"]["accessProfile"])
        self.assertIn("sett", rendered["metadata"]["ir"])
        self.assertIn("udl", rendered["metadata"]["ir"])
        self.assertIn("differentiation", rendered["metadata"]["ir"])
        self.assertIn("evidencePlan", rendered["metadata"]["ir"])
        self.assertEqual("comment", rendered["pages"][0]["buttons"][0]["function"])
        self.assertEqual("I think", rendered["pages"][0]["buttons"][0]["spokenText"])

    def test_renderer_cli_writes_parseable_json(self) -> None:
        import subprocess
        import sys

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "board.ir.json"
            output = Path(tmp) / "board.open-aac-studio.json"
            source.write_text(json.dumps(self.cases["valid_0_3"]), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(RENDERER_PATH), str(source), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(data["pages"])
            self.assertTrue(data["pages"][0]["buttons"])

    def test_renderer_cli_rejects_invalid_json(self) -> None:
        import subprocess
        import sys

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "broken.ir.json"
            output = Path(tmp) / "out.json"
            source.write_text("{not json", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(RENDERER_PATH), str(source), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(1, result.returncode)

    def test_renderer_preserves_button_style_and_audio_cue(self) -> None:
        rendered = renderer.render(self.cases["styled_buttons"])
        first = rendered["pages"][0]["buttons"][0]
        self.assertEqual("#FFE6E6", first["style"]["fillColour"])
        self.assertEqual("#17212b", first["style"]["borderColour"])  # defaults still merged in
        self.assertEqual("thinking", first["audioCue"])  # distinct audio cue preserved
        self.assertEqual("I think", first["spokenText"])

    def test_renderer_emits_both_navigation_target_keys(self) -> None:
        rendered = renderer.render(self.cases["multi_page_navigation"])
        nav_button = next(b for b in rendered["pages"][0]["buttons"] if b["id"] == "btn-go-two")
        nav_action = next(a for a in nav_button["actions"] if a.get("type") == "navigate-page")
        self.assertEqual("page-two", nav_action["targetPageId"])
        self.assertEqual("page-two", nav_action["pageId"])

    def test_renderer_dwell_profile_min_target_defaults_to_120(self) -> None:
        ir = json.loads(json.dumps(self.cases["valid_0_3"]))
        del ir["access"]["minimumTargetSizePx"]
        rendered = renderer.render(ir)
        self.assertEqual(120, rendered["accessibility"]["minimumTargetSizePx"])

    def test_renderer_honours_source_date_epoch(self) -> None:
        import os

        os.environ["SOURCE_DATE_EPOCH"] = "0"
        try:
            first = renderer.render(self.cases["valid_0_3"])
            second = renderer.render(self.cases["valid_0_3"])
        finally:
            del os.environ["SOURCE_DATE_EPOCH"]
        self.assertEqual(first, second)
        self.assertEqual("1970-01-01T00:00:00Z", first["created"])

    def test_default_attribution_names_arasaac_author(self) -> None:
        ir = json.loads(json.dumps(self.cases["valid_0_3"]))
        ir.pop("attribution", None)
        ir.pop("licences", None)
        rendered = renderer.render(ir)
        self.assertIn("Sergio Palao", rendered["licences"][0]["attribution"])


class ObfRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    def test_single_page_board_structure(self) -> None:
        boards = obf_renderer.render_boards(self.cases["valid_0_3"])
        self.assertEqual(1, len(boards))
        board = boards[0]
        self.assertEqual("open-board-0.1", board["format"])
        self.assertTrue(all(isinstance(b["id"], str) for b in board["buttons"]))
        grid = board["grid"]
        self.assertEqual(grid["rows"], len(grid["order"]))
        self.assertTrue(all(len(row) == grid["columns"] for row in grid["order"]))
        placed = [cell for row in grid["order"] for cell in row if cell is not None]
        self.assertEqual([b["id"] for b in board["buttons"]], placed)
        self.assertIn("Sergio Palao", board["license"]["author_name"])

    def test_multi_page_board_links_pages(self) -> None:
        boards = obf_renderer.render_boards(self.cases["multi_page_navigation"])
        self.assertEqual(2, len(boards))
        nav_button = next(b for b in boards[0]["buttons"] if b["id"] == "btn-go-two")
        self.assertEqual({"id": "page-two", "path": "boards/page-two.obf"}, nav_button["load_board"])
        back_button = next(b for b in boards[1]["buttons"] if b["id"] == "btn-go-main")
        self.assertEqual("boards/page-main.obf", back_button["load_board"]["path"])

    def test_obz_cli_round_trip(self) -> None:
        import subprocess
        import sys
        import zipfile

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "board.ir.json"
            output = Path(tmp) / "board.obz"
            source.write_text(json.dumps(self.cases["multi_page_navigation"]), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(OBF_RENDERER_PATH), str(source), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            with zipfile.ZipFile(output) as archive:
                manifest = json.loads(archive.read("manifest.json"))
                self.assertEqual("open-board-0.1", manifest["format"])
                root_board = json.loads(archive.read(manifest["root"]))
                self.assertTrue(root_board["buttons"])

    def test_multi_page_to_obf_fails(self) -> None:
        import subprocess
        import sys

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "board.ir.json"
            output = Path(tmp) / "board.obf"
            source.write_text(json.dumps(self.cases["multi_page_navigation"]), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(OBF_RENDERER_PATH), str(source), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(1, result.returncode)

    def test_arasaac_symbol_id_becomes_image_with_license(self) -> None:
        ir = json.loads(json.dumps(self.cases["valid_0_3"]))
        ir["pages"][0]["buttons"][0]["symbolId"] = 2462
        boards = obf_renderer.render_boards(ir)
        board = boards[0]
        self.assertTrue(board["images"])
        image = board["images"][0]
        self.assertIn("static.arasaac.org/pictograms/2462", image["url"])
        self.assertIn("Sergio Palao", image["license"]["author_name"])
        button = board["buttons"][0]
        self.assertEqual(image["id"], button["image_id"])


if __name__ == "__main__":
    unittest.main()

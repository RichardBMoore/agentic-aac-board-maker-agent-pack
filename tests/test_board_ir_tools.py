from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "skills" / "agentic-aac-board-maker" / "scripts" / "validate_board_ir.py"
RENDERER_PATH = ROOT / "skills" / "agentic-aac-board-maker" / "scripts" / "render_open_aac_studio.py"
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

    def test_missing_repair_route_fails(self) -> None:
        self.assertFailsWith("missing_repair", "no repair/refusal/finished route")

    def test_thin_metadata_is_warning_not_failure(self) -> None:
        failures, warnings = validator.validate(self.cases["legacy_0_2"])
        self.assertEqual([], failures)
        self.assertTrue(any("Differentiation/UDL/SETT metadata is thin" in warning for warning in warnings))


class OpenAacStudioRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    def test_renderer_preserves_ir_powerhouse_metadata(self) -> None:
        rendered = renderer.render(self.cases["valid_0_3"])
        self.assertEqual("Open AAC Studio", rendered["app"])
        self.assertEqual("0.3.0", rendered["metadata"]["sourceIrSchemaVersion"])
        self.assertEqual("eye-gaze-dwell", rendered["metadata"]["accessProfile"])
        self.assertIn("sett", rendered["metadata"]["ir"])
        self.assertIn("udl", rendered["metadata"]["ir"])
        self.assertIn("differentiation", rendered["metadata"]["ir"])
        self.assertIn("evidencePlan", rendered["metadata"]["ir"])
        self.assertEqual("comment", rendered["pages"][0]["buttons"][0]["function"])
        self.assertEqual("I think", rendered["pages"][0]["buttons"][0]["spokenText"])

    def test_renderer_writes_parseable_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "board.ir.json"
            output = Path(tmp) / "board.open-aac-studio.json"
            source.write_text(json.dumps(self.cases["valid_0_3"]), encoding="utf-8")
            status = renderer.main_with_args([str(source), str(output)]) if hasattr(renderer, "main_with_args") else None
            if status is None:
                rendered = renderer.render(self.cases["valid_0_3"])
                output.write_text(json.dumps(rendered), encoding="utf-8")
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(data["pages"])
            self.assertTrue(data["pages"][0]["buttons"])


if __name__ == "__main__":
    unittest.main()

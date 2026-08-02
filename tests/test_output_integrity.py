from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "agentic-aac-board-maker" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(filename: str, name: str):
    path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


canonicalizer = load_module("canonicalize_board_ir.py", "canonicalize_output_integrity")
html_renderer = load_module("render_html.py", "render_html_output_integrity")
parity = load_module("validate_html_parity.py", "validate_html_output_integrity")


class CanonicalIrTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        schema_path = ROOT / "skills" / "agentic-aac-board-maker" / "references" / "aac-board-ir.schema.json"
        cls.schema = json.loads(schema_path.read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(cls.schema)

    def test_legacy_aliases_canonicalise_without_renderer_fields(self) -> None:
        legacy = {
            "schemaVersion": "0.3.0",
            "format": "agentic-aac-board-ir",
            "app": "renderer alias",
            "id": "legacy-board",
            "name": "Legacy board",
            "purpose": "Ask for help.",
            "audience": {"ageBand": "secondary", "tone": "age-respectful"},
            "accessibility": {"intendedAccess": ["touch"], "minimumTargetSizePx": 96},
            "settings": {"width": 1024, "height": 768},
            "communicationFunctions": ["repair"],
            "pages": [{"id": "main", "name": "Main", "gridRows": 1, "gridColumns": 1, "buttons": [{"id": "help", "label": "Help", "role": "repair", "function": "repair", "actions": ["speak"]}]}],
            "teacherNotes": {"modeling": "Model help.", "evidence": "Observe help."},
            "privacy": {"level": "anonymous", "containsSensitiveData": False},
            "licences": [{"source": "Text only", "licence": "None"}],
        }
        canonical = canonicalizer.canonicalize(legacy)
        self.assertEqual("0.4.0", canonical["schemaVersion"])
        self.assertEqual("Legacy board", canonical["title"])
        self.assertNotIn("app", canonical)
        self.assertNotIn("name", canonical)
        self.assertNotIn("settings", canonical)
        self.assertNotIn("accessibility", canonical)
        self.assertNotIn("licences", canonical)
        self.assertEqual([], list(self.validator.iter_errors(canonical)))

    def test_all_generated_ir_is_canonical_and_schema_valid(self) -> None:
        for path in sorted((ROOT / "generated").glob("*/*.ir.json")):
            with self.subTest(path=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data, canonicalizer.canonicalize(data))
                self.assertEqual([], list(self.validator.iter_errors(data)))


class HtmlParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ir_path = next((ROOT / "generated" / "gaze-choice-2x2").glob("*.ir.json"))
        cls.ir = json.loads(cls.ir_path.read_text(encoding="utf-8"))

    def test_fresh_render_has_exact_ir_and_runtime_parity(self) -> None:
        rendered = html_renderer.render(self.ir)
        self.assertEqual([], parity.validate(self.ir, rendered))

    def test_changed_visible_button_label_breaks_parity(self) -> None:
        rendered = html_renderer.render(self.ir).replace('data-label="Art"', 'data-label="Craft"', 1)
        failures = parity.validate(self.ir, rendered)
        self.assertTrue(any("HTML button" in failure for failure in failures))

    def test_changed_runtime_breaks_parity(self) -> None:
        rendered = html_renderer.render(self.ir).replace("class DwellController", "class DifferentDwellController", 1)
        failures = parity.validate(self.ir, rendered)
        self.assertTrue(any("runtime" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()

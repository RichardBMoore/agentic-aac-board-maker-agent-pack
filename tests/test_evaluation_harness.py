from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "agentic-aac-board-maker" / "scripts" / "evaluate_fresh_output.py"
MANIFEST = ROOT / "skills" / "agentic-aac-board-maker" / "fixtures" / "proof-of-concept-prompts.json"


def load_module():
    spec = importlib.util.spec_from_file_location("evaluate_fresh_output_tests", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


evaluator = load_module()


class FreshOutputEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_shipped_proof_outputs_pass_as_fresh_candidates(self) -> None:
        report = evaluator.evaluate(ROOT / "generated", self.manifest)
        self.assertTrue(report["passed"], json.dumps(report, indent=2))

    def test_missing_required_help_route_fails(self) -> None:
        fixture = next(item for item in self.manifest["fixtures"] if item["id"] == "gaze-choice-2x2")
        manifest = {"version": self.manifest["version"], "fixtures": [fixture]}
        with tempfile.TemporaryDirectory() as tmp:
            candidate_root = Path(tmp)
            source = ROOT / "generated" / fixture["id"]
            target = candidate_root / fixture["id"]
            shutil.copytree(source, target)
            ir_path = next(target.glob("*.ir.json"))
            data = json.loads(ir_path.read_text(encoding="utf-8"))
            for page in data["pages"]:
                page["buttons"] = [button for button in page["buttons"] if "help" not in button["label"].lower()]
            ir_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            report = evaluator.evaluate(candidate_root, manifest)
        self.assertFalse(report["passed"])
        failed_names = [item["name"] for item in report["fixtures"][0]["checks"] if not item["passed"]]
        self.assertIn("label:help", failed_names)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "hooks" / "validate_board_outputs.py"
VALID_IR = ROOT / "generated" / "gaze-choice-2x2" / "gaze-choice-class-activity.ir.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hook = load_module(HOOK_PATH, "validate_board_outputs_hook")


def payload_for(path: str | Path, cwd: str | Path | None = None) -> dict:
    payload = {"tool_input": {"file_path": str(path)}}
    if cwd is not None:
        payload["cwd"] = str(cwd)
    return payload


def run_main(payload: object) -> tuple[int, str]:
    stderr = io.StringIO()
    with redirect_stderr(stderr):
        code = hook.main(io.StringIO(json.dumps(payload)))
    return code, stderr.getvalue()


class PayloadAndPathTests(unittest.TestCase):
    def test_relative_path_resolves_against_payload_cwd(self) -> None:
        target = hook.extract_target(payload_for("boards/example.ir.json", "/tmp/project"))
        self.assertEqual(Path("/tmp/project/boards/example.ir.json"), target)

    def test_absolute_path_is_preserved(self) -> None:
        target = hook.extract_target(payload_for(VALID_IR))
        self.assertEqual(VALID_IR, target)

    def test_malformed_payload_shapes_have_no_target(self) -> None:
        malformed = [None, [], {}, {"tool_input": []}, {"tool_input": {}}, {"tool_input": {"file_path": " "}}]
        for payload in malformed:
            with self.subTest(payload=payload):
                self.assertIsNone(hook.extract_target(payload))


class HookRoutingTests(unittest.TestCase):
    def test_malformed_json_and_non_object_payload_are_ignored(self) -> None:
        self.assertEqual(0, hook.main(io.StringIO("{")))
        self.assertEqual((0, ""), run_main([]))

    def test_missing_and_non_board_files_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            text_file = tmp_path / "notes.txt"
            text_file.write_text("not a board", encoding="utf-8")
            with mock.patch.object(hook, "run_checker") as checker:
                self.assertEqual((0, ""), run_main(payload_for(tmp_path / "missing.ir.json")))
                self.assertEqual((0, ""), run_main(payload_for(text_file)))
                checker.assert_not_called()

    def test_relative_ir_path_routes_using_payload_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "board.ir.json"
            target.write_text("{}", encoding="utf-8")
            with mock.patch.object(hook, "run_checker", return_value=(0, "")) as checker:
                self.assertEqual((0, ""), run_main(payload_for(target.name, tmp)))
            self.assertEqual(
                [mock.call(hook.IR_VALIDATOR, target), mock.call(hook.IR_CANONICALIZER, target, "--check")],
                checker.call_args_list,
            )

    def test_valid_ir_passes_and_invalid_ir_blocks(self) -> None:
        self.assertEqual((0, ""), run_main(payload_for(VALID_IR)))

        with tempfile.TemporaryDirectory() as tmp:
            invalid_ir = Path(tmp) / "invalid.ir.json"
            invalid_ir.write_text("{}", encoding="utf-8")
            code, stderr = run_main(payload_for(invalid_ir))
        self.assertEqual(2, code)
        self.assertIn("AAC Board IR validation failed", stderr)
        self.assertIn("Missing required top-level field", stderr)

    def test_missing_validator_blocks_ir(self) -> None:
        with mock.patch.object(hook, "IR_VALIDATOR", ROOT / "missing-validator.py"):
            code, stderr = run_main(payload_for(VALID_IR))
        self.assertEqual(2, code)
        self.assertIn("Validator is missing", stderr)

    def test_dwell_html_routes_to_gaze_checker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "board.html"
            target.write_text('<html><body data-dwell-enabled="true"><button class="dwell-btn">Dwell choice</button></body></html>', encoding="utf-8")
            with mock.patch.object(hook, "run_checker", return_value=(0, "")) as checker:
                self.assertEqual((0, ""), run_main(payload_for(target)))
            checker.assert_called_once_with(hook.GAZE_CHECKER, target)

    def test_paired_generated_html_routes_to_parity_after_gaze_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "board.html"
            paired = Path(tmp) / "board.ir.json"
            target.write_text('<html><body data-dwell-enabled="true"><button class="dwell-btn">Dwell choice</button></body></html>', encoding="utf-8")
            paired.write_text("{}", encoding="utf-8")
            with mock.patch.object(hook, "run_checker", return_value=(0, "")) as checker:
                self.assertEqual((0, ""), run_main(payload_for(target)))
            self.assertEqual(
                [mock.call(hook.GAZE_CHECKER, target), mock.call(hook.HTML_PARITY, paired, target)],
                checker.call_args_list,
            )

    def test_dwell_html_failure_blocks_and_plain_html_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            dwell = tmp_path / "dwell.html"
            dwell.write_text('<body data-dwell-enabled="true"><button>Dwell choice</button></body>', encoding="utf-8")
            plain = tmp_path / "plain.html"
            plain.write_text("<button>Choice</button>", encoding="utf-8")

            with mock.patch.object(hook, "run_checker", return_value=(1, "bad gaze output")) as checker:
                code, stderr = run_main(payload_for(dwell))
                self.assertEqual((0, ""), run_main(payload_for(plain)))

            self.assertEqual(2, code)
            self.assertIn("Eye-gaze/dwell HTML checks failed", stderr)
            self.assertIn("bad gaze output", stderr)
            checker.assert_called_once_with(hook.GAZE_CHECKER, dwell)


class CheckerFailureTests(unittest.TestCase):
    def test_missing_checker_returns_failure(self) -> None:
        code, output = hook.run_checker(ROOT / "missing.py", VALID_IR)
        self.assertEqual(2, code)
        self.assertIn("Validator is missing", output)

    def test_timeout_returns_failure(self) -> None:
        timeout = subprocess.TimeoutExpired(["validator"], hook.TIMEOUT_SECONDS)
        with mock.patch.object(hook.subprocess, "run", side_effect=timeout):
            code, output = hook.run_checker(hook.IR_VALIDATOR, VALID_IR)
        self.assertEqual(2, code)
        self.assertIn("timed out", output)

    def test_launch_error_returns_failure(self) -> None:
        with mock.patch.object(hook.subprocess, "run", side_effect=OSError("python unavailable")):
            code, output = hook.run_checker(hook.IR_VALIDATOR, VALID_IR)
        self.assertEqual(2, code)
        self.assertIn("Could not start validator", output)
        self.assertIn("python unavailable", output)


if __name__ == "__main__":
    unittest.main()

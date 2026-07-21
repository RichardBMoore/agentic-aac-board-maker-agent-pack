from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "skills" / "build-aac-student-supports" / "scripts" / "check_eye_gaze_html.py"
TEMPLATE = ROOT / "skills" / "build-aac-student-supports" / "assets" / "eye-gaze-single-file-template.html"


def run_checker(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(path)],
        check=False,
        capture_output=True,
        text=True,
    )


class EyeGazeFullscreenCheckerTests(unittest.TestCase):
    def test_canonical_template_has_fullscreen_support(self) -> None:
        result = run_checker(TEMPLATE)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_missing_fullscreen_api_request_fails(self) -> None:
        text = TEMPLATE.read_text(encoding="utf-8").replace("requestFullscreen", "requestFull_screen")
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "missing-fullscreen-api.html"
            candidate.write_text(text, encoding="utf-8")
            result = run_checker(candidate)
        self.assertEqual(1, result.returncode)
        self.assertIn("No Fullscreen API startup/control request found", result.stdout)

    def test_fullscreen_control_must_be_gaze_sized(self) -> None:
        text = TEMPLATE.read_text(encoding="utf-8").replace(
            'class="dwell-btn utility" id="fullScreenButton"',
            'class="utility" id="fullScreenButton"',
        )
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "small-fullscreen-control.html"
            candidate.write_text(text, encoding="utf-8")
            result = run_checker(candidate)
        self.assertEqual(1, result.returncode)
        self.assertIn("No gaze-sized .dwell-btn Full screen control found", result.stdout)


if __name__ == "__main__":
    unittest.main()

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "skills" / "accent-display-fit" / "scripts" / "check_accent_display.py"


def fixture_html(min_target: str = "120") -> str:
    return textwrap.dedent(
        f"""\
        <!doctype html>
        <html lang="en-AU">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width,initial-scale=1">
          <style>
            :root {{ --min-target: {min_target}px; --grid-rows: 1; --grid-columns: 1; }}
            html, body {{ min-height: 100vh; min-height: 100dvh; }}
            .board-grid {{ display: grid; gap: 12px; }}
          </style>
        </head>
        <body>
          <main class="board-grid"><button>Talk</button></main>
          <noscript>Tell your teacher this activity needs scripting enabled.</noscript>
        </body>
        </html>
        """
    )


class AccentDisplayCheckerTests(unittest.TestCase):
    def run_checker(self, html: str, *args: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate.html"
            candidate.write_text(html, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(CHECKER), str(candidate), *args],
                text=True,
                capture_output=True,
                check=False,
            )

    def test_valid_candidate_passes_mustfit(self) -> None:
        result = self.run_checker(fixture_html())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_published_grace_profile_is_available(self) -> None:
        result = self.run_checker(fixture_html(), "--profile", "grace")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1024x460 floor", result.stdout)

    def test_target_below_120_pixels_fails(self) -> None:
        result = self.run_checker(fixture_html("80"))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("must be at least 120px", result.stdout)


if __name__ == "__main__":
    unittest.main()

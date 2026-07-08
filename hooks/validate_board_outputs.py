#!/usr/bin/env python3
"""Claude Code PostToolUse hook: auto-validate AAC board outputs on write.

Registered in hooks/hooks.json for Write|Edit. Whenever the agent writes:

- ``*.ir.json``  -> run the canonical IR validator
  (skills/agentic-aac-board-maker/scripts/validate_board_ir.py)
- ``*.html`` containing dwell markup -> run the strict eye-gaze checker
  (skills/build-aac-student-supports/scripts/check_eye_gaze_html.py)

On failure the hook exits 2 so the validator output is surfaced back to the
agent, which can then repair the board before presenting it as a draft. Files
that are not board outputs are ignored (exit 0, no output).

This automates the pack's "run QA before claiming a board is ready" rule
instead of relying on the agent remembering to do it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[1]
IR_VALIDATOR = PACK_ROOT / "skills" / "agentic-aac-board-maker" / "scripts" / "validate_board_ir.py"
GAZE_CHECKER = PACK_ROOT / "skills" / "build-aac-student-supports" / "scripts" / "check_eye_gaze_html.py"
TIMEOUT_SECONDS = 60


def run_checker(script: Path, target: Path) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(script), str(target)],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def looks_like_dwell_html(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return False
    return "dwell" in text and "<button" in text


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0

    file_path = str(payload.get("tool_input", {}).get("file_path", "")).strip()
    if not file_path:
        return 0
    target = Path(file_path)
    if not target.exists():
        return 0

    if target.name.endswith(".ir.json") and IR_VALIDATOR.exists():
        code, output = run_checker(IR_VALIDATOR, target)
        if code != 0:
            print(
                f"AAC Board IR validation failed for {target.name}. Fix the IR before "
                f"rendering or delivering this board:\n{output}",
                file=sys.stderr,
            )
            return 2
        return 0

    if target.suffix.lower() in {".html", ".htm"} and GAZE_CHECKER.exists() and looks_like_dwell_html(target):
        code, output = run_checker(GAZE_CHECKER, target)
        if code != 0:
            print(
                f"Eye-gaze/dwell HTML checks failed for {target.name}. Repair before "
                f"presenting this board as a draft:\n{output}",
                file=sys.stderr,
            )
            return 2
        return 0

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.TimeoutExpired:
        print("Board validation hook timed out; run the validators manually.", file=sys.stderr)
        raise SystemExit(0)

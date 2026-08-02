#!/usr/bin/env python3
"""Claude Code PostToolUse hook: auto-validate AAC board outputs on write.

Registered in hooks/hooks.json for Write|Edit. Whenever the agent writes:

- ``*.ir.json``  -> run the semantic validator and canonical-form check
  (skills/agentic-aac-board-maker/scripts/validate_board_ir.py)
- ``*.html`` containing dwell markup -> run the strict eye-gaze checker; when
  a same-stem ``*.ir.json`` exists, also enforce HTML/IR/shared-runtime parity
  (skills/build-aac-student-supports/scripts/check_eye_gaze_html.py)

On failure the hook exits 2 so the validator output is surfaced back to the
agent, which can then repair the board before presenting it as a draft. Missing
validators, launch errors, and timeouts also fail closed. Files that are not
board outputs are ignored (exit 0, no output).

This automates the pack's "run QA before claiming a board is ready" rule
instead of relying on the agent remembering to do it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TextIO

PACK_ROOT = Path(__file__).resolve().parents[1]
IR_VALIDATOR = PACK_ROOT / "skills" / "agentic-aac-board-maker" / "scripts" / "validate_board_ir.py"
IR_CANONICALIZER = PACK_ROOT / "skills" / "agentic-aac-board-maker" / "scripts" / "canonicalize_board_ir.py"
HTML_PARITY = PACK_ROOT / "skills" / "agentic-aac-board-maker" / "scripts" / "validate_html_parity.py"
GAZE_CHECKER = PACK_ROOT / "skills" / "build-aac-student-supports" / "scripts" / "check_eye_gaze_html.py"
TIMEOUT_SECONDS = 60


def run_checker(script: Path, target: Path, *extra_args: str | Path) -> tuple[int, str]:
    if not script.is_file():
        return 2, f"Validator is missing from the plugin installation: {script}"
    try:
        result = subprocess.run(
            [sys.executable, str(script), str(target), *(str(value) for value in extra_args)],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return 2, f"Validator timed out after {TIMEOUT_SECONDS} seconds."
    except OSError as error:
        return 2, f"Could not start validator: {error}"

    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0 and not output:
        output = f"Validator exited with status {result.returncode} and no diagnostic output."
    return result.returncode, output


def looks_like_dwell_html(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return False
    return 'data-dwell-enabled="true"' in text and "<button" in text


def extract_target(payload: object) -> Path | None:
    if not isinstance(payload, dict):
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    raw_path = tool_input.get("file_path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None

    target = Path(raw_path.strip()).expanduser()
    if not target.is_absolute():
        cwd = payload.get("cwd")
        if isinstance(cwd, str) and cwd.strip():
            target = Path(cwd).expanduser() / target
    return target


def main(stdin: TextIO | None = None) -> int:
    try:
        payload = json.load(stdin if stdin is not None else sys.stdin)
    except (OSError, ValueError):
        return 0

    target = extract_target(payload)
    if target is None or not target.is_file():
        return 0

    if target.name.lower().endswith(".ir.json"):
        code, output = run_checker(IR_VALIDATOR, target)
        if code != 0:
            print(
                f"AAC Board IR validation failed for {target.name}. Fix the IR before "
                f"rendering or delivering this board:\n{output}",
                file=sys.stderr,
            )
            return 2
        code, output = run_checker(IR_CANONICALIZER, target, "--check")
        if code != 0:
            print(
                f"AAC Board IR is valid legacy/best-effort input but not canonical output. "
                f"Canonicalise it before rendering or delivery:\n{output}",
                file=sys.stderr,
            )
            return 2
        return 0

    if target.suffix.lower() in {".html", ".htm"} and looks_like_dwell_html(target):
        code, output = run_checker(GAZE_CHECKER, target)
        if code != 0:
            print(
                f"Eye-gaze/dwell HTML checks failed for {target.name}. Repair before "
                f"presenting this board as a draft:\n{output}",
                file=sys.stderr,
            )
            return 2
        paired_ir = target.with_name(target.name.rsplit(".", 1)[0] + ".ir.json")
        if paired_ir.is_file():
            code, output = run_checker(HTML_PARITY, paired_ir, target)
            if code != 0:
                print(
                    f"HTML/IR/shared-runtime parity failed for {target.name}. Re-render from the paired IR:\n{output}",
                    file=sys.stderr,
                )
                return 2
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

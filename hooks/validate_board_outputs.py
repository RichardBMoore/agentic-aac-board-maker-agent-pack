#!/usr/bin/env python3
"""PostToolUse hook: auto-validate AAC board outputs on write.

Registered in hooks/hooks.json for Write|Edit. Whenever the agent writes:

- ``*.ir.json`` that has not been built yet -> say that the next step is
  scripts/build_board.py (this is the expected state of a freshly written
  board, not a mistake in it)
- ``*.ir.json``  -> run the semantic validator and canonical-form check
  (skills/agentic-aac-board-maker/scripts/validate_board_ir.py)
- ``*.html`` containing dwell markup -> run the strict eye-gaze checker; when
  a same-stem ``*.ir.json`` exists, also enforce HTML/IR/shared-runtime parity
  (skills/build-aac-student-supports/scripts/check_eye_gaze_html.py)

On failure the hook exits 2 so the validator output is surfaced back to the
agent, which can then repair the board before presenting it as a draft. Missing
validators, launch errors, and timeouts also fail closed. Files that are not
board outputs are ignored (exit 0, no output).

Two payload shapes are understood: Claude Code's ``tool_input.file_path`` and
the Codex ``apply_patch`` shape, where the patch text names the files
(``*** Add File:`` / ``*** Update File:``). The Codex shape is covered by unit
tests against the documented format but has not been run inside a live Codex
session.

The hook is a safety net. scripts/build_board.py runs the same checks and more
on every host, including ones that do not run plugin hooks.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import TextIO

PACK_ROOT = Path(__file__).resolve().parents[1]
BUILD_TOOL = PACK_ROOT / "skills" / "agentic-aac-board-maker" / "scripts" / "build_board.py"
PATCH_FILE_LINE = re.compile(r"^\*\*\* (?:Add File|Update File|Move to): (.+?)\s*$", re.MULTILINE)
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


def patch_paths(tool_input: dict) -> list[str]:
    """File paths named by a Codex apply_patch payload (added, updated or moved-to files)."""
    for key in ("command", "patch", "input"):
        value = tool_input.get(key)
        if isinstance(value, list):
            value = "\n".join(str(item) for item in value)
        if isinstance(value, str) and "*** Begin Patch" in value:
            return PATCH_FILE_LINE.findall(value)
    return []


def extract_targets(payload: object) -> list[Path]:
    """Every file this tool call wrote, as absolute paths where the payload allows."""
    if not isinstance(payload, dict):
        return []
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return []
    raw_path = tool_input.get("file_path")
    raw_paths = [raw_path] if isinstance(raw_path, str) and raw_path.strip() else patch_paths(tool_input)

    cwd = payload.get("cwd")
    targets: list[Path] = []
    for raw in raw_paths:
        target = Path(raw.strip()).expanduser()
        if not target.is_absolute() and isinstance(cwd, str) and cwd.strip():
            target = Path(cwd).expanduser() / target
        if target not in targets:
            targets.append(target)
    return targets


def extract_target(payload: object) -> Path | None:
    targets = extract_targets(payload)
    return targets[0] if targets else None


def is_unbuilt_board(path: Path) -> bool:
    """A board that has pages but no house standards yet: written, not built."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and bool(data.get("pages")) and not data.get("house")


def check_target(target: Path) -> str | None:
    """Return a message for the agent when this file needs action, else None."""
    if target.name.lower().endswith(".ir.json"):
        if is_unbuilt_board(target):
            return (
                f"{target.name} is written but not built yet. This is the expected next step, not a mistake in the file. Run:\n"
                f"  python3 \"{BUILD_TOOL}\" \"{target}\"\n"
                "It applies house standards, validates the board, renders the outputs and lists what still needs attention. "
                "Tip: name the small file you edit <name>.source.json so <name>.ir.json stays a build product."
            )
        code, output = run_checker(IR_VALIDATOR, target)
        if code != 0:
            return (
                f"AAC Board IR validation failed for {target.name}. Fix the IR before "
                f"rendering or delivering this board:\n{output}"
            )
        code, output = run_checker(IR_CANONICALIZER, target, "--check")
        if code != 0:
            return (
                f"AAC Board IR is valid legacy/best-effort input but not canonical output. "
                f"Canonicalise it before rendering or delivery:\n{output}"
            )
        return None

    if target.suffix.lower() in {".html", ".htm"} and looks_like_dwell_html(target):
        code, output = run_checker(GAZE_CHECKER, target)
        if code != 0:
            return (
                f"Eye-gaze/dwell HTML checks failed for {target.name}. Repair before "
                f"presenting this board as a draft:\n{output}"
            )
        paired_ir = target.with_name(target.name.rsplit(".", 1)[0] + ".ir.json")
        if paired_ir.is_file():
            code, output = run_checker(HTML_PARITY, paired_ir, target)
            if code != 0:
                return f"HTML/IR/shared-runtime parity failed for {target.name}. Re-render from the paired IR:\n{output}"
    return None


def main(stdin: TextIO | None = None) -> int:
    try:
        payload = json.load(stdin if stdin is not None else sys.stdin)
    except (OSError, ValueError):
        return 0

    messages = [message for target in extract_targets(payload) if target.is_file() and (message := check_target(target))]
    if not messages:
        return 0
    print("\n\n".join(messages), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

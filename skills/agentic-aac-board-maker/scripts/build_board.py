#!/usr/bin/env python3
"""Build a whole AAC board pack from one file, and say plainly what still needs work.

One command replaces the separate apply / validate / render / check steps, so no
step can be skipped or run out of order:

  1. apply house standards (fixed places for key words, shared word list,
     spelling and core-word pages, colour by word type, partner card);
  2. validate the board (canonical form, JSON Schema, communication and access rules);
  3. render the offline HTML board, the partner card and an Open Board Format export;
  4. check the HTML matches the board, the eye-gaze rules and the screen-fit rules;
  5. print a short outline of the finished board and what still needs attention.

Usage:
  build_board.py shops.source.json                 # writes shops.ir.json + outputs beside it
  build_board.py shops.source.json --out-dir pack  # ... or into another folder
  build_board.py pack/shops.ir.json                # rebuild an existing board in place
  build_board.py pack/shops.ir.json --check        # change nothing; exit 1 if anything is stale or failing

Write and edit the small *.source.json file. The built *.ir.json is mostly
embedded pictures: view it with inspect_board.py rather than opening it.
Symbols a reviewer approved in the built board are kept when the source is
rebuilt (matched by button id, label and search term).

Exit status: 0 when every check passes (warnings and to-do items are listed but
do not fail the build), 1 otherwise.
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import display_fit  # noqa: E402
import house_standards as hs  # noqa: E402
import inspect_board  # noqa: E402
from apply_house_standards import HouseError, apply  # noqa: E402
from canonicalize_board_ir import canonicalize  # noqa: E402
from render_html import render as render_html  # noqa: E402
from render_partner_card import render as render_partner_card  # noqa: E402
from validate_board_ir import validate as semantic_validate  # noqa: E402
from validate_html_parity import validate as parity_validate  # noqa: E402

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:  # jsonschema is a development dependency, not a runtime one.
    Draft202012Validator = None

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SCHEMA_PATH = SKILL_DIR / "references" / "aac-board-ir.schema.json"
GAZE_CHECKER = SKILL_DIR.parent / "build-aac-student-supports" / "scripts" / "check_eye_gaze_html.py"
DEFAULT_FORMATS = ("html", "partner-card", "obf")
ALL_FORMATS = (*DEFAULT_FORMATS, "open-aac-studio")
INPUT_SUFFIXES = (".source.json", ".ir.json", ".json")
NOT_VERIFIED = [
    "the real student, device, mount, calibration and lighting",
    "the speech voice on the target device",
    "whether the student recognises each symbol",
    "browser interaction (run the Playwright tests) and print pagination",
]


class Report:
    """Collects step results so the summary and the exit status agree."""

    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.steps: list[dict[str, str]] = []
        self.outputs: list[dict[str, str]] = []
        self.notes: list[str] = []
        self.rewrites: list[str] = []
        self.house_changes: list[str] = []
        self.carried_symbols = 0
        self.summary: dict[str, Any] | None = None

    def step(self, name: str, status: str, detail: str = "") -> None:
        self.steps.append({"name": name, "status": status, "detail": detail})

    @property
    def passed(self) -> bool:
        return bool(self.steps) and not any(step["status"] == "fail" for step in self.steps)

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "passed": self.passed,
            "steps": self.steps,
            "outputs": self.outputs,
            "houseChanges": self.house_changes,
            "rewrittenByHouseWordList": self.rewrites,
            "carriedSymbols": self.carried_symbols,
            "notes": self.notes,
            "board": self.summary,
            "notVerified": NOT_VERIFIED,
        }


def stem_of(path: Path) -> str:
    for suffix in INPUT_SUFFIXES:
        if path.name.endswith(suffix):
            return path.name[: -len(suffix)]
    return path.stem


def buttons_by_id(ir: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(button.get("id")): button
        for page in ir.get("pages", []) if isinstance(page, dict)
        for button in page.get("buttons", []) if isinstance(button, dict)
    }


def carry_reviewed_symbols(source: dict[str, Any], previous: dict[str, Any]) -> int:
    """Keep symbols a reviewer approved in the last build when the small source file has none.

    Only non-house buttons are matched, and only when id, label and search term
    are all unchanged, so a button whose meaning changed goes back to review.
    """
    earlier = buttons_by_id(previous)
    carried = 0
    for button in buttons_by_id(source).values():
        old = earlier.get(str(button.get("id")))
        if not old or button.get("symbolSrc") or not old.get("symbolSrc"):
            continue
        if button.get("lexiconId") or old.get("lexiconId") or hs.lexicon_match(str(button.get("label", "")), button.get("wordClass")):
            continue
        if button.get("label") != old.get("label") or button.get("searchTerm") != old.get("searchTerm"):
            continue
        button["symbolSrc"] = old["symbolSrc"]
        for field in ("symbolId", "symbolStatus"):
            if old.get(field) is not None:
                button[field] = old[field]
        carried += 1
    return carried


def house_rewrites(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    """Buttons whose own wording was replaced because the label is a house word."""
    notes = []
    built = buttons_by_id(after)
    for button_id, original in buttons_by_id(before).items():
        result = built.get(button_id)
        if not result or not result.get("lexiconId") or original.get("lexiconId"):
            continue
        wrote = hs.normalise_label(str(original.get("spokenText", "")))
        if wrote in {hs.normalise_label(str(original.get("label", ""))), hs.normalise_label(str(result.get("spokenText", "")))}:
            continue
        behaviour = hs.words()[result["lexiconId"]].get("behaviour")
        effect = "adds the word to the message bar" if behaviour == "compose" else "says this on every board"
        notes.append(
            f"{button_id}: “{original.get('label')}” is the house word '{result['lexiconId']}', so it now says “{result.get('spokenText')}” "
            f"({effect}) instead of your “{original.get('spokenText')}”. If you meant your own phrase, give the button a different label."
        )
    return notes


def schema_errors(ir: dict[str, Any]) -> list[str] | None:
    """Schema problems, or None when jsonschema is not installed."""
    if Draft202012Validator is None:
        return None
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(ir), key=lambda error: list(error.path))
    return [f"{'.'.join(str(part) for part in error.path) or '<root>'}: {error.message}" for error in errors[:5]]


def run_script(script: Path, *args: str | Path) -> tuple[int, str]:
    try:
        result = subprocess.run(
            [sys.executable, str(script), *(str(arg) for arg in args)],
            capture_output=True, text=True, timeout=120, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return 1, str(error)
    return result.returncode, (result.stdout + result.stderr).strip()


def same_obf(first: Path, second: Path) -> bool:
    if first.suffix == ".obf":
        return json.loads(first.read_text(encoding="utf-8")) == json.loads(second.read_text(encoding="utf-8"))
    with zipfile.ZipFile(first) as one, zipfile.ZipFile(second) as two:
        return {name: one.read(name) for name in one.namelist()} == {name: two.read(name) for name in two.namelist()}


def same_open_aac_studio(first: Path, second: Path) -> bool:
    def load(path: Path) -> dict[str, Any]:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("created", None)
        data.pop("modified", None)
        return data
    return load(first) == load(second)


def write_or_compare(report: Report, kind: str, target: Path, fresh_text: str | None = None, fresh_file: Path | None = None, same=None) -> bool:
    """Write an output (build) or compare it with a fresh render (check). Returns False on drift."""
    if report.mode == "check":
        if not target.exists():
            report.outputs.append({"kind": kind, "path": str(target), "status": "missing"})
            return False
        if fresh_text is not None:
            matches = target.read_text(encoding="utf-8") == fresh_text
        else:
            matches = same(target, fresh_file)
        report.outputs.append({"kind": kind, "path": str(target), "status": "current" if matches else "stale"})
        return matches
    target.parent.mkdir(parents=True, exist_ok=True)
    if fresh_text is not None:
        target.write_text(fresh_text, encoding="utf-8")
    else:
        target.write_bytes(fresh_file.read_bytes())
    report.outputs.append({"kind": kind, "path": str(target), "status": "written"})
    return True


def build(
    input_path: Path,
    out_dir: Path | None = None,
    check: bool = False,
    formats: tuple[str, ...] | None = None,
    floor: tuple[int, int] = display_fit.MUST_FIT_FLOOR,
    paper: str = "A4",
    orientation: str = "landscape",
    carry_symbols: bool = True,
) -> Report:
    report = Report("check" if check else "build")
    try:
        raw_text = input_path.read_text(encoding="utf-8")
        source = json.loads(raw_text)
    except (OSError, json.JSONDecodeError) as error:
        report.step("read the board file", "fail", f"cannot read {input_path}: {error}")
        return report
    if not isinstance(source, dict):
        report.step("read the board file", "fail", "the top-level JSON value must be an object")
        return report

    if not [page for page in source.get("pages") or [] if isinstance(page, dict) and page.get("buttons")]:
        report.step("read the board file", "fail", "the board has no pages with buttons. Start from templates/board-json-skeleton.json.")
        return report

    stem = stem_of(input_path)
    folder = (out_dir or input_path.parent).resolve()
    ir_path = folder / f"{stem}.ir.json"
    in_place = input_path.resolve() == ir_path
    previous: dict[str, Any] | None = None
    if not in_place and ir_path.exists():
        try:
            previous = json.loads(ir_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = None

    # 1. House standards.
    working = copy.deepcopy(source)
    if carry_symbols and isinstance(previous, dict):
        report.carried_symbols = carry_reviewed_symbols(working, previous)
    try:
        before = canonicalize(working)
        ir, changes = apply(working)
    except HouseError as error:
        report.step("house standards", "fail", str(error))
        return report
    except (IndexError, KeyError, TypeError, ValueError) as error:
        report.step("house standards", "fail", f"the board is missing required structure ({type(error).__name__}: {error}). Start from templates/board-json-skeleton.json.")
        return report
    report.house_changes = changes
    report.rewrites = house_rewrites(before, ir)
    if check:
        on_disk = source if in_place else previous
        if on_disk is None:
            report.step("house standards", "fail", f"{ir_path.name} has not been built yet; run build_board.py without --check.")
            return report
        if on_disk != ir:
            report.step("house standards", "fail", f"{ir_path.name} is stale or was edited after building; run build_board.py without --check.")
        else:
            report.step("house standards", "pass", "the built board matches the house standards")
    else:
        report.step("house standards", "pass", f"{len(changes)} change(s) applied" if changes else "already applied")

    # 2. Validation.
    failures, _warnings = semantic_validate(ir)
    problems = schema_errors(ir)
    if problems is None:
        report.notes.append("JSON Schema check skipped: the jsonschema package is not installed (pip install jsonschema).")
    elif problems:
        failures = [f"schema: {problem}" for problem in problems] + failures
    if failures:
        report.step("board validation", "fail", "; ".join(failures))
    else:
        report.step("board validation", "pass", "canonical form, communication and access rules" + ("" if problems is None else ", JSON Schema"))

    if failures and not check:
        # Do not leave a half-valid pack behind; the source file is untouched.
        report.notes.append("Nothing was written because the board does not validate yet.")
        report.summary = inspect_board.summarise(ir, "")
        return report

    ir_text = json.dumps(ir, indent=2, ensure_ascii=False) + "\n"
    if not check:
        folder.mkdir(parents=True, exist_ok=True)
        ir_path.write_text(ir_text, encoding="utf-8")
        report.outputs.append({"kind": "board IR", "path": str(ir_path), "status": "written"})
    report.summary = inspect_board.summarise(ir, ir_text)

    wanted = set(formats or DEFAULT_FORMATS)
    oas_path = folder / f"{stem}.open-aac-studio.json"
    if formats is None and oas_path.exists():
        wanted.add("open-aac-studio")  # keep an existing export in step with the board

    # 3. HTML board + parity + access checks.
    if "html" in wanted:
        html_path = folder / f"{stem}.html"
        try:
            html_text = render_html(ir, paper=paper, orientation=orientation)
        except (ValueError, TypeError) as error:
            report.step("HTML board", "fail", f"{error} For a scanning player, export Open Board Format instead: --formats obf,partner-card.")
        else:
            current = write_or_compare(report, "HTML board", html_path, fresh_text=html_text)
            drift = parity_validate(ir, html_text)
            if drift:
                report.step("HTML board", "fail", "HTML does not match the board: " + "; ".join(drift))
            elif not current:
                report.step("HTML board", "fail", f"{html_path.name} is missing or stale; rebuild (never hand-edit generated HTML).")
            else:
                report.step("HTML board", "pass", "rendered offline and in parity with the board and shared runtime")
            if 'data-dwell-enabled="true"' in html_text:
                if GAZE_CHECKER.is_file():
                    with tempfile.TemporaryDirectory() as tmp:
                        fresh_html = Path(tmp) / html_path.name
                        fresh_html.write_text(html_text, encoding="utf-8")
                        code, output = run_script(GAZE_CHECKER, fresh_html)
                    report.step("eye-gaze and dwell rules", "pass" if code == 0 else "fail", "" if code == 0 else output)
                else:
                    report.step("eye-gaze and dwell rules", "skip", "checker not installed beside this skill (build-aac-student-supports)")

    # 4. Screen fit. The house layout puts Help, Different and Finished on the bottom row.
    if display_fit.is_on_screen(ir):
        misfits = [entry for entry in display_fit.board_fit(ir, floor) if not entry["fits"]]
        if misfits:
            report.step("screen fit", "fail", " ".join(display_fit.describe(entry, floor) for entry in misfits))
        else:
            report.step("screen fit", "pass", f"every page fits a {floor[0]}x{floor[1]} screen without cutting off the bottom row")
    else:
        report.step("screen fit", "skip", "print board")

    # 5. Partner card and interchange exports.
    if "partner-card" in wanted:
        current = write_or_compare(report, "partner card", folder / "partner-card.html", fresh_text=render_partner_card(ir))
        report.step("partner card", "pass" if current else "fail", "" if current else "partner-card.html is missing or stale; rebuild.")
    with tempfile.TemporaryDirectory() as tmp:
        fresh_ir = Path(tmp) / "board.ir.json"
        fresh_ir.write_text(ir_text, encoding="utf-8")
        if "obf" in wanted:
            suffix = ".obf" if len(ir["pages"]) == 1 else ".obz"
            fresh = Path(tmp) / f"board{suffix}"
            code, output = run_script(SCRIPT_DIR / "render_obf.py", fresh_ir, fresh)
            if code != 0:
                report.step("Open Board Format export", "fail", output)
            else:
                current = write_or_compare(report, "Open Board Format", folder / f"{stem}{suffix}", fresh_file=fresh, same=same_obf)
                report.step("Open Board Format export", "pass" if current else "fail", "" if current else f"{stem}{suffix} is missing or stale; rebuild.")
            other = folder / f"{stem}{'.obz' if suffix == '.obf' else '.obf'}"
            if other.exists():
                report.notes.append(f"{other.name} is left over from an earlier page count; delete it so nobody imports the old board.")
        if "open-aac-studio" in wanted:
            fresh = Path(tmp) / "board.open-aac-studio.json"
            code, output = run_script(SCRIPT_DIR / "render_open_aac_studio.py", fresh_ir, fresh)
            if code != 0:
                report.step("Open AAC Studio export", "fail", output)
            else:
                current = write_or_compare(report, "Open AAC Studio JSON", oas_path, fresh_file=fresh, same=same_open_aac_studio)
                report.step("Open AAC Studio export", "pass" if current else "fail", "" if current else f"{oas_path.name} is missing or stale; rebuild.")

    missing = [name for name in ("README.md", "teacher-notes.md") if not (folder / name).exists()]
    if missing:
        report.notes.append(f"Still to write for a full resource pack: {', '.join(missing)} (purpose, access, how to open and print, what the team must check).")
    return report


def render_report(report: Report, outline: bool = True) -> str:
    marks = {"pass": "ok  ", "fail": "FAIL", "skip": "skip"}
    board = (report.summary or {}).get("board", {})
    title = f"{board.get('title', 'board')} [{board.get('id', '?')}]" if board else "board"
    verb = "CHECK" if report.mode == "check" else "BUILD"
    lines = [f"{verb} {'PASSED' if report.passed else 'FAILED'}: {title}", ""]
    for step in report.steps:
        lines.append(f"  {marks[step['status']]}  {step['name']}" + (f": {step['detail']}" if step["detail"] else ""))
    if report.rewrites:
        lines += ["", "Your wording was replaced by the house word list (same word, same message on every board):"]
        lines += [f"  - {note}" for note in report.rewrites]
    if report.house_changes and report.mode == "build":
        lines += ["", "House standards changed:"] + [f"  - {change}" for change in report.house_changes]
    if report.carried_symbols:
        lines += ["", f"Kept {report.carried_symbols} reviewed symbol(s) from the previous build (same id, label and search term)."]
    if report.outputs:
        lines += ["", "Files:"] + [f"  {item['status']:8} {item['path']}" for item in report.outputs]
    if report.notes:
        lines += [""] + [f"Note: {note}" for note in report.notes]
    if outline and report.summary:
        lines += ["", "=" * 72, inspect_board.render_text(report.summary)]
    else:
        lines += ["", "Not checked here: " + "; ".join(NOT_VERIFIED) + "."]
    return "\n".join(lines)


def parse_floor(value: str) -> tuple[int, int]:
    try:
        width, height = (int(part) for part in value.lower().split("x"))
    except ValueError as error:
        raise argparse.ArgumentTypeError("use WIDTHxHEIGHT in CSS pixels, for example 1280x720") from error
    return width, height


def parse_formats(value: str) -> tuple[str, ...]:
    chosen = tuple(part.strip() for part in value.split(",") if part.strip())
    unknown = [part for part in chosen if part not in ALL_FORMATS]
    if unknown or not chosen:
        raise argparse.ArgumentTypeError(f"choose from {', '.join(ALL_FORMATS)}")
    return chosen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_file", type=Path, help="A *.source.json you wrote, or an existing *.ir.json to rebuild in place.")
    parser.add_argument("--out-dir", type=Path, help="Folder for the built board and its outputs (default: beside the input).")
    parser.add_argument("--check", action="store_true", help="Change nothing; exit 1 if the board or any output is failing, missing or stale.")
    parser.add_argument("--formats", type=parse_formats, help=f"Comma-separated outputs (default {','.join(DEFAULT_FORMATS)}; also open-aac-studio).")
    parser.add_argument(
        "--display-floor", type=parse_floor, default=display_fit.MUST_FIT_FLOOR,
        help="Smallest screen the board must fit, WIDTHxHEIGHT in CSS px (default 1264x600, an Accent 1400 in maximised Edge). "
        "Change it only when the team has confirmed the device's real viewport.",
    )
    parser.add_argument("--paper", choices=("A4", "A3"), default="A4")
    parser.add_argument("--orientation", choices=("portrait", "landscape"), default="landscape")
    parser.add_argument("--no-carry-symbols", action="store_true", help="Do not keep reviewed symbols from the previous build.")
    parser.add_argument("--report", type=Path, help="Also write the full result as JSON to this file.")
    parser.add_argument("--quiet", action="store_true", help="Print the step results only, without the board outline.")
    args = parser.parse_args(argv)

    report = build(
        args.input_file, out_dir=args.out_dir, check=args.check, formats=args.formats, floor=args.display_floor,
        paper=args.paper, orientation=args.orientation, carry_symbols=not args.no_carry_symbols,
    )
    print(render_report(report, outline=not args.quiet))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report.as_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

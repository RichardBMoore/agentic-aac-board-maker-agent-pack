#!/usr/bin/env python3
"""Show an AAC Board IR as a short outline an agent or teacher can read.

A built board IR is mostly embedded picture data (often 300-450 KB, about 80%
base64), so opening the JSON directly wastes a whole context window and hides
the board. This prints what matters instead: each page as a grid, every
button's words, role, word class and symbol status, and a list of what still
needs attention before the board is handed over.

Usage:
  inspect_board.py board.ir.json                # outline + what needs attention
  inspect_board.py board.ir.json --all          # also expand keyboard/core-word pages
  inspect_board.py board.ir.json --page page-shop
  inspect_board.py board.ir.json --json         # the same information as JSON

It never changes the file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import display_fit  # noqa: E402
import house_standards as hs  # noqa: E402
from apply_house_standards import HouseError, apply  # noqa: E402
from canonicalize_board_ir import canonicalize  # noqa: E402
from output_layout import grid_slots  # noqa: E402
from validate_board_ir import validate  # noqa: E402

GENERATED_PATTERNS = hs.GENERATED_PATTERNS
NON_WORD_CLASSES = {"letter", "ending", "operation"}
DEFAULT_ACTIONS = {"speak-text", "speak-label", "log-attempt"}
ACTION_SHORT = {
    "add-to-message": "+message",
    "speak-message": "speak message",
    "remove-last-word": "undo word",
    "clear-message": "clear message",
    "add-letter": "+letter",
    "add-space": "+space",
    "delete-letter": "delete letter",
    "add-word-ending": "+ending",
    "schedule-done": "step done",
    "next-page": "next page",
    "previous-page": "previous page",
    "mark-correct": "mark correct",
    "mark-incorrect": "mark incorrect",
}
DATA_URI = re.compile(r'data:[^"\\]+')


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def clip(value: Any, limit: int = 60) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def symbol_state(button: dict[str, Any]) -> str:
    source = str(button.get("symbolSrc") or "")
    if not source:
        return "none"
    return str(button.get("symbolStatus") or "embedded")


def describe_actions(button: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for raw in as_list(button.get("actions")):
        action = as_dict(raw)
        kind = str(action.get("type", raw if isinstance(raw, str) else ""))
        if kind in DEFAULT_ACTIONS:
            continue
        if kind == "navigate-page":
            result.append(f"→{action.get('targetPageId', '?')}")
        else:
            result.append(ACTION_SHORT.get(kind, kind))
    return result


def is_word_button(button: dict[str, Any]) -> bool:
    """A button that carries vocabulary, so a missing symbol matters."""
    if button.get("hidden") is True or button.get("role") == "navigation":
        return False
    return button.get("wordClass") not in NON_WORD_CLASSES


def button_summary(button: dict[str, Any], cell: tuple[int, int] | None) -> dict[str, Any]:
    label, spoken = str(button.get("label", "")), str(button.get("spokenText", ""))
    summary: dict[str, Any] = {
        "id": button.get("id"),
        "label": label,
        "role": button.get("role"),
        "function": button.get("function"),
        "wordClass": button.get("wordClass"),
        "symbol": symbol_state(button),
    }
    if cell:
        summary["row"], summary["column"] = cell
    if spoken and spoken != label:
        summary["says"] = spoken
    if button.get("lexiconId"):
        summary["houseWord"] = button["lexiconId"]
    if button.get("symbolId"):
        summary["symbolId"] = button["symbolId"]
    if summary["symbol"] == "none" and button.get("searchTerm"):
        summary["searchTerm"] = button["searchTerm"]
    actions = describe_actions(button)
    if actions:
        summary["actions"] = actions
    if button.get("hidden") is True:
        summary["hidden"] = True
    return summary


def page_summary(page: dict[str, Any]) -> dict[str, Any]:
    grid = as_dict(page.get("grid"))
    buttons = [as_dict(raw) for raw in as_list(page.get("buttons"))]
    cells: dict[str, tuple[int, int]] = {}
    layout_error = None
    try:
        cells = {str(button.get("id")): (row + 1, column + 1) for row, column, button in grid_slots(page)}
    except (KeyError, TypeError, ValueError) as error:
        layout_error = str(error)
    summary: dict[str, Any] = {
        "id": page.get("id"),
        "name": page.get("name"),
        "pattern": page.get("pattern"),
        "rows": grid.get("rows"),
        "columns": grid.get("columns"),
        "targets": sum(1 for button in buttons if button.get("hidden") is not True),
        "generated": page.get("pattern") in GENERATED_PATTERNS,
        "buttons": [button_summary(button, cells.get(str(button.get("id")))) for button in buttons],
    }
    if as_dict(page.get("schedule")).get("steps"):
        summary["scheduleSteps"] = list(page["schedule"]["steps"])
    if layout_error:
        summary["layoutError"] = layout_error
    return summary


def default_teacher_notes() -> dict[str, Any]:
    return canonicalize({"pages": []})["teacherNotes"]


def attention(ir: dict[str, Any]) -> list[dict[str, str]]:
    """What still needs a decision or a fix, most serious first."""
    items: list[dict[str, str]] = []
    applied = bool(as_dict(ir.get("house")))
    failures, warnings = validate(ir)
    for failure in failures:
        if not applied and "must record house standards" in failure:
            continue
        items.append({"level": "fail", "text": failure})
    if not applied:
        items.append({"level": "todo", "text": "House standards are not applied yet (this looks like a source file). Run scripts/build_board.py on it."})
    else:
        try:
            result, _ = apply(ir)
        except HouseError as error:
            items.append({"level": "fail", "text": f"House standards cannot be applied: {error}"})
        else:
            if result != ir:
                items.append({"level": "fail", "text": "The file has drifted from the house standards (edited after building). Re-run scripts/build_board.py."})
    items.extend({"level": "warn", "text": warning} for warning in warnings)

    buttons = [as_dict(raw) for page in as_list(ir.get("pages")) for raw in as_list(as_dict(page).get("buttons"))]
    # House words get their symbol (or deliberately none) from the house set, so only this board's own words count here.
    words = [button for button in buttons if is_word_button(button) and not button.get("lexiconId")]
    missing = [button for button in words if symbol_state(button) == "none"]
    if applied and words and missing:  # before the build, house words have not been given their symbols yet
        labels = ", ".join(f"“{clip(button.get('label'), 24)}”" for button in missing[:8]) + (", …" if len(missing) > 8 else "")
        items.append({
            "level": "todo",
            "text": (
                f"{len(missing)} of {len(words)} of this board's own words have no symbol: {labels}. Text-only is fine when the team chose it; otherwise "
                "make a review sheet with scripts/fetch_arasaac_symbols.py <ir> --review-out symbol-review.json (needs internet and a human reviewer)."
            ),
        })
    proposed = sum(1 for button in buttons if button.get("symbolStatus") == "proposed")
    if proposed:
        items.append({"level": "info", "text": f"{proposed} house symbols are 'proposed': chosen by the agent and awaiting one team review. Say so in the handover."})

    card = as_dict(ir.get("partnerCard"))
    if str(card.get("notes", "")).startswith("Default card"):
        items.append({"level": "todo", "text": "partnerCard is the tool default. Choose this week's 3-5 model words, comment examples and wait time for this board."})
    if applied and as_dict(ir.get("teacherNotes")) == default_teacher_notes():
        items.append({"level": "todo", "text": "teacherNotes are the tool defaults. Write modelling, evidence and customisation notes for this board."})
    keyboard = as_dict(as_dict(ir.get("literacy")).get("keyboard"))
    if keyboard.get("enabled") is False:
        items.append({"level": "info", "text": f"No spelling keyboard: {clip(keyboard.get('omitReason'), 140) or 'no reason recorded'}"})
    if as_dict(ir.get("evidenceLog")).get("enabled") is True:
        items.append({"level": "info", "text": "The selection log is ON. Confirm the team and family agreed its purpose."})
    if as_dict(ir.get("systemFit")).get("reviewStatus") == "team-input-needed":
        items.append({"level": "info", "text": "systemFit is 'team-input-needed': list the unresolved items (existing AAC system, calibration, positioning, voice, partner signals) in the handover."})
    return items


def summarise(ir: dict[str, Any], raw_text: str = "") -> dict[str, Any]:
    access, audience, house = as_dict(ir.get("access")), as_dict(ir.get("audience")), as_dict(ir.get("house"))
    pages = [page_summary(as_dict(page)) for page in as_list(ir.get("pages"))]
    all_buttons = [button for page in pages for button in page["buttons"]]
    states = [button["symbol"] for button in all_buttons]
    image_bytes = sum(len(match) for match in DATA_URI.findall(raw_text))
    fit = display_fit.board_fit(ir) if display_fit.is_on_screen(ir) else []
    return {
        "board": {
            "id": ir.get("id"),
            "title": ir.get("title"),
            "purpose": ir.get("purpose"),
            "schemaVersion": ir.get("schemaVersion"),
            "houseStandards": house.get("standardsVersion"),
            "layoutSource": house.get("layoutSource"),
            "ageBand": audience.get("ageBand"),
            "locale": audience.get("locale"),
            "settings": audience.get("settings") or [],
            "accessProfile": access.get("profile"),
            "intendedAccess": access.get("intended") or [],
            "minimumTargetSizePx": access.get("minimumTargetSizePx"),
            "dwellTimeMs": access.get("dwellTimeMs"),
            "visibleTargetLimit": access.get("visibleTargetLimit"),
            "messageBar": bool(as_dict(ir.get("messageBar")).get("enabled")),
            "visualProfile": as_dict(ir.get("display")).get("visualProfile") or "standard",
            "communicationFunctions": as_list(ir.get("communicationFunctions")),
        },
        "file": {"bytes": len(raw_text.encode("utf-8")), "embeddedImageBytes": image_bytes},
        "counts": {
            "pages": len(pages),
            "generatedPages": sum(1 for page in pages if page["generated"]),
            "buttons": len(all_buttons),
            "symbols": {state: states.count(state) for state in ("approved", "proposed", "embedded", "none") if states.count(state)},
        },
        "displayFit": fit,
        "pages": pages,
        "attention": attention(ir),
    }


def render_grid(page: dict[str, Any]) -> list[str]:
    rows, columns = page.get("rows") or 0, page.get("columns") or 0
    cells = {(button.get("row"), button.get("column")): button for button in page["buttons"]}
    lines = []
    for row in range(1, rows + 1):
        parts = []
        for column in range(1, columns + 1):
            button = cells.get((row, column))
            if button is None:
                parts.append("·")
            else:
                parts.append(f"{clip(button['label'], 22)}{' (hidden)' if button.get('hidden') else ''}")
        lines.append(f"    row {row}: " + " | ".join(parts))
    return lines


def render_button(button: dict[str, Any]) -> str:
    parts = [f"{button['id']}", f"“{clip(button['label'], 30)}”", f"{button.get('role')}/{button.get('function')}"]
    parts.append(f"class {button['wordClass']}" if button.get("wordClass") else "class MISSING")
    if button.get("houseWord"):
        parts.append(f"house:{button['houseWord']}")
    if button.get("says"):
        parts.append(f"says “{clip(button['says'], 50)}”")
    if button["symbol"] == "none":
        parts.append(f"symbol none (search “{button['searchTerm']}”)" if button.get("searchTerm") else "symbol none")
    else:
        parts.append(f"symbol {button['symbol']}" + (f" #{button['symbolId']}" if button.get("symbolId") else ""))
    if button.get("actions"):
        parts.append("does " + ", ".join(button["actions"]))
    if button.get("hidden"):
        parts.append("HIDDEN")
    return "      " + " · ".join(parts)


def render_text(summary: dict[str, Any], show_all: bool = False, only_page: str | None = None) -> str:
    board, counts, file = summary["board"], summary["counts"], summary["file"]
    house = f"house standards {board['houseStandards']} applied" if board["houseStandards"] else "house standards NOT applied (source file)"
    lines = [
        f"{board['title']}  [{board['id']}]  IR {board['schemaVersion']}, {house}",
        f"Purpose: {clip(board['purpose'], 200)}",
        (
            f"Audience: {board['ageBand']}, {board['locale']}"
            + (f", settings {', '.join(board['settings'])}" if board["settings"] else "")
            + f"  |  Access: {board['accessProfile']} (intended: {', '.join(board['intendedAccess'])})"
        ),
        (
            f"Targets: at least {board['minimumTargetSizePx']} px, limit {board['visibleTargetLimit']} per page"
            + (f", dwell {board['dwellTimeMs']} ms" if board["dwellTimeMs"] else "")
            + f"  |  Message bar: {'yes' if board['messageBar'] else 'no'}  |  Visual profile: {board['visualProfile']}"
        ),
        f"Communication functions: {', '.join(board['communicationFunctions'])}",
    ]
    symbols = ", ".join(f"{count} {state}" for state, count in counts["symbols"].items()) or "none"
    lines.append(f"Pages: {counts['pages']} ({counts['generatedPages']} added by house standards)  |  Buttons: {counts['buttons']}  |  Symbols: {symbols}")
    if file["bytes"]:
        share = round(100 * file["embeddedImageBytes"] / file["bytes"]) if file["bytes"] else 0
        note = "  (do not open this file directly; use this outline)" if share >= 30 else ""
        lines.append(f"File: {file['bytes'] // 1024} KB, {share}% embedded pictures{note}")
    for entry in summary["displayFit"]:
        lines.append(("Fit: " if entry["fits"] else "Fit PROBLEM: ") + display_fit.describe(entry))
    lines.append("")

    for page in summary["pages"]:
        if only_page and page["id"] != only_page:
            continue
        tag = " (added by house standards)" if page["generated"] else ""
        lines.append(f"{page['id']}  “{page['name']}”  {page['pattern']}  {page['rows']}x{page['columns']}, {page['targets']} targets{tag}")
        if page.get("layoutError"):
            lines.append(f"    LAYOUT ERROR: {page['layoutError']}")
        if page["generated"] and not show_all and not only_page:
            lines.append("    " + ", ".join(clip(button["label"], 14) for button in page["buttons"]))
            continue
        lines.extend(render_grid(page))
        if page.get("scheduleSteps"):
            lines.append("    schedule order: " + " → ".join(page["scheduleSteps"]))
        lines.extend(render_button(button) for button in page["buttons"])
    if only_page and not any(page["id"] == only_page for page in summary["pages"]):
        lines.append(f"No page with id {only_page!r}. Pages: {', '.join(str(page['id']) for page in summary['pages'])}")

    lines.append("")
    order = {"fail": 0, "warn": 1, "todo": 2, "info": 3}
    names = {"fail": "FAIL", "warn": "WARN", "todo": "TO DO", "info": "NOTE"}
    items = sorted(summary["attention"], key=lambda item: order[item["level"]])
    lines.append("Needs attention:" if items else "Needs attention: nothing found by these static checks.")
    lines.extend(f"  {names[item['level']]}: {item['text']}" for item in items)
    lines.append("")
    lines.append("Not checked here: the real student, device, mount and voice; whether the student knows these symbols; print pagination.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ir_file", type=Path)
    parser.add_argument("--all", action="store_true", help="Expand the keyboard, core words and word endings pages too.")
    parser.add_argument("--page", help="Show only this page id, fully expanded.")
    parser.add_argument("--json", action="store_true", help="Print the outline as JSON.")
    args = parser.parse_args(argv)
    try:
        raw_text = args.ir_file.read_text(encoding="utf-8")
        ir = json.loads(raw_text)
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot read IR: {error}", file=sys.stderr)
        return 1
    if not isinstance(ir, dict):
        print("FAIL: IR top-level value must be an object.", file=sys.stderr)
        return 1
    summary = summarise(ir, raw_text)
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(render_text(summary, show_all=args.all, only_page=args.page))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Render a one-page communication partner card from canonical AAC Board IR.

The card turns teacher notes into a practical page for anyone talking with the
student: this week's 3-5 words to model (and where they are), how long to wait,
comments to use instead of test questions, and a least-to-most prompt ladder
with no hand-over-hand.

Usage:
  python3 render_partner_card.py board.ir.json partner-card.html
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any

try:
    from canonicalize_board_ir import canonicalize
except ModuleNotFoundError:  # Supports importlib-based unit tests.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from canonicalize_board_ir import canonicalize

import house_standards as hs
from output_layout import grid_slots

DEFAULT_LADDER = hs.load_settings()["partnerCard"]["promptLadder"]


def describe_cell(row: int, column: int, rows: int, columns: int) -> str:
    if rows == 3 and columns == 3:
        return f"{['top', 'middle', 'bottom'][row - 1]} {['left', 'middle', 'right'][column - 1]}".replace("middle middle", "centre")
    vertical = "top" if row == 1 else "bottom" if row == rows else f"row {row}"
    horizontal = "left" if column == 1 else "right" if column == columns else f"column {column}"
    return f"{vertical} {horizontal}"


def button_locations(ir: dict[str, Any]) -> dict[str, tuple[dict[str, Any], dict[str, Any], str]]:
    result = {}
    for page in ir["pages"]:
        rows, columns = page["grid"]["rows"], page["grid"]["columns"]
        for row, column, button in grid_slots(page):
            result[button["id"]] = (button, page, describe_cell(row + 1, column + 1, rows, columns))
    return result


HOUSE_PLACE_NAMES = {
    "help": ("Help", "bottom-left"),
    "different": ("Different", "bottom-middle"),
    "undo": ("Undo", "bottom-middle"),
    "finished": ("Finished", "bottom-right"),
    "stop": ("Stop", "top-right"),
    "speak-message": ("Speak", "top-right"),
    "keyboard": ("ABC", "left-middle of the first page"),
}


def house_places_sentence(ir: dict[str, Any]) -> str:
    """Describe only the house words this board actually uses, and where."""
    talking = [page for page in ir["pages"] if page.get("pattern") not in {"keyboard", "keyboard-letters"}]
    present: dict[str, int] = {}
    for page in talking:
        for button in page["buttons"]:
            word = button.get("lexiconId")
            if word in HOUSE_PLACE_NAMES and not button.get("hidden"):
                present[word] = present.get(word, 0) + 1
    parts = []
    for word, (label, where) in HOUSE_PLACE_NAMES.items():
        if word in present:
            scope = "on every page" if present[word] == len(talking) and word != "keyboard" else "wherever it appears"
            parts.append(f"{label} is {where} {scope}" if word != "keyboard" else f"{label} is {where}")
    navigation = any(button.get("role") == "navigation" for page in talking for button in page["buttons"])
    sentence = "; ".join(parts) + "." if parts else ""
    if navigation:
        sentence += " Page buttons: \u25b6 forward is right-middle, \u25c0 back is left-middle."
    if ir["studentControls"].get("stopSpeechDuringPlayback"):
        sentence += " Stop speech appears at the right edge while the board is talking."
    return sentence.strip()


def card_fragment(ir: dict[str, Any], heading_level: int = 2) -> str:
    """HTML fragment (no document wrapper) shared by the board's teacher panel and the standalone card."""
    card = ir.get("partnerCard")
    h = f"h{heading_level}"
    sub = f"h{heading_level + 1}"
    if not card:
        return f'<section class="partner-card"><{h}>Partner card</{h}><p>No partner card yet. Add model words, wait time and comment examples.</p></section>'
    locations = button_locations(ir)
    words = []
    for button_id in card["modelWords"]:
        button, page, where = locations.get(button_id, ({"label": button_id, "spokenText": ""}, {"name": "?"}, "?"))
        said = f' — says “{html.escape(button["spokenText"])}”' if button.get("spokenText") and button["spokenText"] != button["label"] else ""
        words.append(f'<li><strong>{html.escape(button["label"])}</strong>{said} <span class="where">({html.escape(page["name"])} page, {html.escape(where)})</span></li>')
    comments = "".join(f"<li>{html.escape(example)}</li>" for example in card["commentExamples"])
    ladder = "".join(f"<li>{html.escape(step)}</li>" for step in card.get("promptLadder") or DEFAULT_LADDER)
    notes = f'<p class="card-notes">{html.escape(card["notes"])}</p>' if card.get("notes") else ""
    house_places = house_places_sentence(ir)
    return (
        f'<section class="partner-card" aria-label="Partner card"><{h}>Partner card: {html.escape(ir["title"])}</{h}>'
        f'<{sub}>1. Model these words this week</{sub}><p>Touch the button on the board as you say the word in your own talk. Don’t ask the student to copy you.</p><ul>{"".join(words)}</ul>'
        f'<{sub}>2. Wait</{sub}><p>After you model, comment or ask, wait at least <strong>{int(card["waitSeconds"])} seconds</strong>. Count in your head and keep an expectant look.</p>'
        f'<{sub}>3. Comment more than you question</{sub}><ul>{comments}</ul><p>Avoid test questions you already know the answer to.</p>'
        f'<{sub}>4. If more support is needed (least to most)</{sub}><ol>{ladder}</ol>'
        f'<{sub}>5. Every way counts</{sub}><p>Respond to speech, sounds, looks, gestures and the board. {house_places}</p>{notes}</section>'
    )


def render(ir_input: dict[str, Any]) -> str:
    ir = canonicalize(ir_input)
    css = (
        "body{font-family:Verdana,Arial,sans-serif;color:#17212b;max-width:780px;margin:auto;padding:18px;line-height:1.45}"
        "h1{font-size:1.5rem;margin:0 0 6px}h2{font-size:1.1rem;margin:16px 0 4px}.where{color:#45525e}"
        "li{margin:3px 0}@page{size:A4 portrait;margin:14mm}"
    )
    return (
        f'<!doctype html>\n<html lang="{html.escape(ir["audience"]["locale"])}"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>Partner card — {html.escape(ir["title"])}</title>'
        f"<style>{css}</style></head><body>{card_fragment(ir, 1)}</body></html>\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ir_file", type=Path)
    parser.add_argument("output_file", type=Path)
    args = parser.parse_args(argv)
    try:
        raw = json.loads(args.ir_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot read IR: {error}", file=sys.stderr)
        return 1
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(render(raw), encoding="utf-8")
    print(f"Wrote {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

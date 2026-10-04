#!/usr/bin/env python3
"""Apply house standards to an AAC Board IR (idempotent).

What it does, in order:

1. Uses the house word list (references/house-lexicon.json): any button whose
   label matches a house word gets that word's label, spoken message, word
   class, actions and (when the team has a symbol for it) symbol.
2. Adds literacy pages unless the board opts out: a gaze-safe spelling
   keyboard reached by an ABC button on the first page, a core words page
   (I, want, don't, like, go, more) and, for older students, a word endings page.
3. Links talking pages in a ring with one navigation button per page.
4. Adds the "How I talk" introduction to community boards.
5. Places house words at their permanent addresses (references/house-layout.json)
   and fills content around them, keeping existing valid positions.
6. Colours buttons by word class (references/house-settings.json) and fills
   speech, evidence-log, partner-card and literacy defaults.

Usage:
  python3 apply_house_standards.py board.ir.json [out.ir.json]
  python3 apply_house_standards.py board.ir.json --check   # exit 1 if not already applied
"""

from __future__ import annotations

import argparse
import copy
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

KEYBOARD_GROUPS = {
    "qwerty": ["qwert", "yuiop", "asdfg", "hjkl ", "zxcvbnm"],
    "abc": ["abcdef", "ghijkl", "mnopqr", "stuvwx", "yz "],
}
FULL_ROWS = {
    "qwerty": ["qwertyuiop", "asdfghjkl", "zxcvbnm"],
    "abc": ["abcdefghij", "klmnopqrst", "uvwxyz"],
}
MANAGED_ACTIONS = {
    "speak-text", "speak-label", "add-to-message", "log-attempt", "speak-message", "remove-last-word",
    "clear-message", "delete-letter", "add-space", "add-letter",
}
GENERATED_PATTERNS = {"keyboard", "keyboard-letters", "core-words", "word-endings"}
ENDING_LABELS = {"s": "-s", "ing": "-ing", "ed": "-ed", "er": "-er", "est": "-est"}


class HouseError(ValueError):
    """A board cannot meet the house standards without a design decision."""


def text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def action(button_id: str, action_type: str, **extra: Any) -> dict[str, Any]:
    return {"id": f"act-{button_id}-{action_type}", "type": action_type, **extra}


def is_gaze_or_switch(ir: dict[str, Any]) -> bool:
    access = ir["access"]
    methods = set(access.get("intended", [])) | {access.get("profile")}
    return bool(methods & {"eye-gaze-dwell", "mouse-dwell", "single-switch", "two-switch", "partner-assisted-scanning"})


def word_button(word_id: str, button_id: str | None = None) -> dict[str, Any]:
    entry = hs.words()[word_id]
    return {
        "id": button_id or f"btn-{word_id}",
        "label": entry["label"],
        "role": entry["role"],
        "function": entry["function"],
        "spokenText": entry["spokenText"],
        "searchTerm": entry["searchTerm"],
        "symbolId": None,
        "symbolSrc": "",
        "symbolLayout": "label-bottom",
        "actions": [],
        "lexiconId": word_id,
    }


def apply_word(button: dict[str, Any], word_id: str, report: list[str]) -> None:
    entry = hs.words()[word_id]
    if button.get("lexiconId") != word_id:
        report.append(f"{button['id']}: matched house word '{word_id}' (label '{button['label']}').")
    button["lexiconId"] = word_id
    for field in ("label", "spokenText", "wordClass", "role", "function", "searchTerm"):
        button[field] = entry[field]
    bid = button["id"]
    kept = [item for item in button.get("actions", []) if item.get("type") not in MANAGED_ACTIONS and not (word_id == "keyboard" and item.get("type") == "navigate-page")]
    behaviour = entry["behaviour"]
    if behaviour == "speak":
        managed = [action(bid, "speak-text", text=entry["spokenText"]), action(bid, "log-attempt")]
    elif behaviour == "compose":
        managed = [action(bid, "add-to-message", text=entry["spokenText"]), action(bid, "speak-text", text=entry["spokenText"]), action(bid, "log-attempt")]
    else:
        operation = entry["operationAction"]
        if operation == "navigate-page":
            existing = next((item for item in button.get("actions", []) if item.get("type") == "navigate-page"), None)
            managed = [existing] if existing else []
        else:
            managed = [action(bid, operation)]
            if operation == "speak-message":
                managed.append(action(bid, "log-attempt"))
    button["actions"] = managed + kept
    symbol = entry.get("symbol", {})
    if symbol.get("id") and symbol.get("status") in {"proposed", "approved"}:
        data = hs.symbol_data_uri(int(symbol["id"]))
        if data:
            button["symbolId"] = int(symbol["id"])
            button["symbolSrc"] = data
            button["symbolStatus"] = symbol["status"]


def literacy_config(ir: dict[str, Any], report: list[str]) -> dict[str, Any]:
    settings = hs.load_settings()["literacy"]
    existing = copy.deepcopy(ir.get("literacy") or {})
    small = all(page["grid"]["rows"] < 3 or page["grid"]["columns"] < 3 for page in ir["pages"] if page.get("pattern") not in GENERATED_PATTERNS)
    small_reason = "Early choice board smaller than 3x3; spelling and core words stay on the student's main system."
    if "keyboard" not in existing:
        existing["keyboard"] = {"enabled": False, "omitReason": small_reason} if small else {"enabled": True, "layout": settings["keyboard"]["layout"], "mode": settings["keyboard"]["mode"]}
        if small:
            report.append("Keyboard omitted by default for a board smaller than 3x3 (omitReason recorded).")
    if "coreWords" not in existing:
        existing["coreWords"] = {"enabled": not small, "words": list(settings["coreWords"]["words"])}
    if "wordEndings" not in existing:
        enabled = (not small) and hs.ending_enabled_for(ir["audience"]["ageBand"])
        existing["wordEndings"] = {"enabled": enabled, "endings": list(settings["wordEndings"]["endings"])}
    keyboard = existing["keyboard"]
    if keyboard.get("enabled"):
        keyboard.setdefault("layout", settings["keyboard"]["layout"])
        keyboard.setdefault("mode", settings["keyboard"]["mode"])
    return existing


def page(page_id: str, name: str, pattern: str, buttons: list[dict[str, Any]], rows: int = 3, columns: int = 3) -> dict[str, Any]:
    return {"id": page_id, "name": name, "pattern": pattern, "layout": "grid", "grid": {"rows": rows, "columns": columns}, "buttons": buttons}


def nav_button(button_id: str, label: str, target: str) -> dict[str, Any]:
    return {
        "id": button_id, "label": label, "role": "navigation", "function": "navigate", "spokenText": f"Go to {label.strip('◀▶ ')}",
        "searchTerm": "next", "symbolId": None, "symbolSrc": "", "symbolLayout": "label-bottom", "wordClass": "operation",
        "actions": [action(button_id, "navigate-page", targetPageId=target)],
    }


def keyboard_pages(home_id: str, home_name: str, layout: str, mode: str, limit: int) -> list[dict[str, Any]]:
    if mode == "full" and limit >= 32:
        rows = FULL_ROWS[layout]
        buttons: list[dict[str, Any]] = []
        for row_index, letters in enumerate(rows, start=1):
            for column_index, letter in enumerate(letters, start=1 if row_index == 1 else 2):
                buttons.append(letter_button(letter, None, hs.cell_position(row_index, column_index, 4, 11)))
        back = nav_button("kbd-back", "\u25c0 Back", home_id)
        back["spokenText"] = f"Go back to {home_name}"
        buttons += [word_button("speak-message", "kbd-speak"), word_button("delete-letter", "kbd-delete"), word_button("clear", "kbd-clear"), word_button("space", "kbd-space"), word_button("help", "kbd-help"), back]
        buttons[-3]["position"] = hs.cell_position(4, 2, 4, 11)
        return [page("page-keyboard", "Keyboard", "keyboard", buttons, 4, 11)]
    groups = KEYBOARD_GROUPS[layout]
    group_page_id = "page-keyboard"
    group_buttons: list[dict[str, Any]] = []
    letter_pages: list[dict[str, Any]] = []
    for index, group in enumerate(groups, start=1):
        letters = [character for character in group if character != " "]
        label = " ".join(letters) + (" ␣" if " " in group else "")
        letter_page_id = f"page-keyboard-{index}"
        group_buttons.append({
            "id": f"kbd-group-{index}", "label": label, "role": "core", "function": "navigate", "spokenText": " ".join(letters),
            "searchTerm": "alphabet", "symbolId": None, "symbolSrc": "", "symbolLayout": "label-bottom", "wordClass": "letter",
            "actions": [action(f"kbd-group-{index}", "navigate-page", targetPageId=letter_page_id)],
        })
        buttons = [letter_button(letter, group_page_id) for letter in letters]
        if " " in group:
            space = word_button("space", f"kbd-space-{index}")
            space["actions"] = [action(space["id"], "add-space"), action(space["id"], "navigate-page", targetPageId=group_page_id)]
            buttons.append(space)
        letters_back = nav_button(f"kbd-back-{index}", "\u25c0 Letters", group_page_id)
        letters_back["spokenText"] = "Go back to the letter groups"
        buttons += [word_button("help", f"kbd-help-{index}"), letters_back]
        letter_pages.append(page(letter_page_id, f"Letters {letters[0]}–{letters[-1]}", "keyboard-letters", buttons))
    back = nav_button("kbd-back", "\u25c0 Back", home_id)
    back["spokenText"] = f"Go back to {home_name}"
    group_buttons += [word_button("speak-message", "kbd-speak"), word_button("delete-letter", "kbd-delete"), word_button("help", "kbd-help"), back]
    return [page(group_page_id, "Keyboard", "keyboard", group_buttons)] + letter_pages


def letter_button(letter: str, return_page: str | None, position: dict[str, float] | None = None) -> dict[str, Any]:
    button_id = f"kbd-{letter}"
    actions = [action(button_id, "add-letter", text=letter), action(button_id, "speak-text", text=letter.upper())]
    if return_page:
        actions.append(action(button_id, "navigate-page", targetPageId=return_page))
    actions.append(action(button_id, "log-attempt"))
    button = {
        "id": button_id, "label": letter, "role": "core", "function": "initiate", "spokenText": letter.upper(), "searchTerm": letter,
        "symbolId": None, "symbolSrc": "", "symbolLayout": "label-bottom", "wordClass": "letter", "actions": actions,
    }
    if position:
        button["position"] = position
    return button


def core_words_page(words: list[str]) -> dict[str, Any]:
    known = [word for word in words if word in hs.words()]
    if len(known) > 6:
        raise HouseError("A 3x3 core words page holds at most 6 words beside Speak, navigation and Help.")
    buttons = [word_button(word, f"core-{word}") for word in known]
    buttons += [word_button("speak-message", "core-speak"), word_button("help", "core-help")]
    return page("page-core-words", "Core words", "core-words", buttons)


def endings_page(endings: list[str]) -> dict[str, Any]:
    buttons = []
    for ending in endings[:3]:
        button_id = f"end-{ending}"
        buttons.append({
            "id": button_id, "label": ENDING_LABELS[ending], "role": "sentence", "function": "explain",
            "spokenText": f"add {ending}", "searchTerm": "grammar", "symbolId": None, "symbolSrc": "", "symbolLayout": "label-bottom",
            "wordClass": "ending", "actions": [action(button_id, "add-word-ending", text=ending), action(button_id, "log-attempt")],
        })
    buttons += [word_button("speak-message", "end-speak"), word_button("undo", "end-undo"), word_button("clear", "end-clear"), word_button("help", "end-help")]
    return page("page-word-endings", "Word endings", "word-endings", buttons)


def wire_ring(ring: list[dict[str, Any]], talking_count: int, report: list[str]) -> None:
    """One forward button per ring page; a back button on talking pages after the first."""
    if len(ring) < 2:
        return
    for index, current in enumerate(ring):
        target = ring[(index + 1) % len(ring)]
        navs = [button for button in current["buttons"] if button.get("role") == "navigation" and not button.get("lexiconId")]
        forward = next((button for button in navs if "previous-page" not in hs.action_types(button)), None)
        backward = next((button for button in navs if "previous-page" in hs.action_types(button)), None)
        for extra in navs:
            if extra is not forward and extra is not backward:
                current["buttons"].remove(extra)
                report.append(f"{current['id']}: removed extra navigation button {extra['id']} (one forward and one back cell per page).")
        if forward is None:
            forward = nav_button(f"nav-{current['id']}", "", target["id"])
            current["buttons"].append(forward)
        label = f"{target['name']} ▶"
        forward.update({"label": label, "spokenText": f"Go to {target['name']}", "wordClass": "operation", "function": "navigate"})
        forward.pop("position", None)
        others = [item for item in forward.get("actions", []) if item.get("type") not in hs.NAVIGATION_ACTIONS]
        forward["actions"] = [action(forward["id"], "navigate-page", targetPageId=target["id"])] + others
        # Talking pages and the word endings page get a back button; the core words page is full (six words).
        wants_back = 0 < index and (index < talking_count or current.get("pattern") == "word-endings")
        if wants_back:
            previous = ring[index - 1]
            if backward is None:
                backward = nav_button(f"back-{current['id']}", "", previous["id"])
                current["buttons"].append(backward)
            backward.update({"label": f"◀ {previous['name']}", "spokenText": f"Go back to {previous['name']}", "wordClass": "operation", "function": "navigate"})
            backward.pop("position", None)
            others = [item for item in backward.get("actions", []) if item.get("type") not in hs.NAVIGATION_ACTIONS]
            backward["actions"] = [action(backward["id"], "previous-page")] + others
        elif backward is not None:
            current["buttons"].remove(backward)
            report.append(f"{current['id']}: removed back button {backward['id']} (the first page and generated pages are forward-only).")


def place_page(current: dict[str, Any], report: list[str]) -> None:
    rows, columns = current["grid"]["rows"], current["grid"]["columns"]
    reserved = hs.reserved_addresses(rows, columns)
    taken: dict[tuple[int, int], dict[str, Any]] = {}
    unplaced: list[dict[str, Any]] = []
    present_slots: set[str] = set()
    for button in current["buttons"]:
        slot = hs.slot_for_button(button)
        address = hs.house_address(slot, rows, columns) if slot else None
        if slot and address is None:
            report.append(f"{current['id']}: no house address for '{slot}' on a {rows}x{columns} grid; placed as content.")
        if address is None:
            unplaced.append(button)
            continue
        if address in taken:
            raise HouseError(
                f"{current['id']}: '{button['label']}' and '{taken[address]['label']}' share house address {address}. "
                "Split the page or drop one of them."
            )
        taken[address] = button
        present_slots.add(slot)
    reserved_for_present = {address for address, slot in reserved.items() if slot in present_slots}
    remaining: list[dict[str, Any]] = []
    for button in unplaced:
        cell = existing_cell(button, rows, columns)
        if cell and cell not in taken and cell not in reserved_for_present:
            taken[cell] = button
        else:
            remaining.append(button)
    free = [(row, column) for row in range(1, rows + 1) for column in range(1, columns + 1) if (row, column) not in taken]
    help_cell = hs.house_address("help", rows, columns)
    # Reading order keeps content predictable; the Help cell is only used as a last resort.
    ordered = [cell for cell in free if cell != help_cell] + [cell for cell in free if cell == help_cell]
    if len(remaining) > len(ordered):
        raise HouseError(f"{current['id']}: needs {len(taken) + len(remaining)} cells but its {rows}x{columns} grid has {rows * columns}. Split the page.")
    for button, cell in zip(remaining, ordered):
        taken[cell] = button
        if cell == help_cell:
            report.append(f"{current['id']}: content '{button['label']}' had to use the Help cell.")
    for (row, column), button in taken.items():
        button["position"] = hs.cell_position(row, column, rows, columns)
    current["buttons"] = [taken[cell] for cell in sorted(taken)]


def existing_cell(button: dict[str, Any], rows: int, columns: int) -> tuple[int, int] | None:
    position = button.get("position")
    if not isinstance(position, dict):
        return None
    try:
        column = round(float(position["x"]) * columns / 100) + 1
        row = round(float(position["y"]) * rows / 100) + 1
    except (KeyError, TypeError, ValueError):
        return None
    if 1 <= row <= rows and 1 <= column <= columns:
        return (row, column)
    return None


def default_partner_card(ir: dict[str, Any]) -> dict[str, Any]:
    candidates = []
    for current in ir["pages"]:
        if current.get("pattern") in {"keyboard", "keyboard-letters"}:
            continue
        for button in current["buttons"]:
            if button.get("hidden") or button.get("wordClass") in {"operation", "letter", "ending"} or button.get("role") == "navigation":
                continue
            if button.get("lexiconId") in {"help", "how-i-talk"}:
                continue
            candidates.append(button)
    preferred = [button for button in candidates if button.get("role") in {"core", "comment", "question", "sentence"}] or candidates
    chosen = (preferred + [button for button in candidates if button not in preferred])[:4]
    if len(chosen) < 3:
        chosen = candidates[:3]
    settings = hs.load_settings()["partnerCard"]
    wait = settings["waitSeconds"] + (5 if is_gaze_or_switch(ir) else 0)
    return {
        "modelWords": [button["id"] for button in chosen],
        "waitSeconds": wait,
        "commentExamples": [f"Touch “{button['label']}” as you say “{button['spokenText']}” about what is happening." for button in chosen[:2]],
        "promptLadder": list(settings["promptLadder"]),
        "notes": "Default card: replace the model words with this week's 3–5 targets.",
    }


def apply(raw: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    report: list[str] = []
    ir = canonicalize(raw)
    settings = hs.load_settings()

    house = ir.setdefault("house", {"standardsVersion": hs.HOUSE_STANDARDS_VERSION, "layoutSource": "house"})
    house["standardsVersion"] = hs.HOUSE_STANDARDS_VERSION
    house.setdefault("layoutSource", "house")
    house["symbolSet"] = f"house-lexicon {hs.load_lexicon()['version']}"

    display = ir["display"]
    if display.get("visualProfile") == "cvi":
        cvi = settings["visualProfiles"]["cvi"]
        display["colourScheme"] = "none"
        display["backgroundColour"] = cvi["background"]
        display.setdefault("highlightColour", cvi["highlightColour"])
    else:
        display.setdefault("colourScheme", settings["colourScheme"])
    if "speech" not in ir:
        speech = {key: value for key, value in settings["speech"].items() if key != "note" and value not in ("", None)}
        ir["speech"] = speech
    ir.setdefault("evidenceLog", copy.deepcopy(settings["evidenceLog"]))

    for current in ir["pages"]:
        for button in current["buttons"]:
            word_id = button.get("lexiconId") or hs.lexicon_match(button["label"], button.get("wordClass"))
            if word_id:
                apply_word(button, word_id, report)

    literacy = literacy_config(ir, report)
    ir["literacy"] = literacy
    talking = [current for current in ir["pages"] if current.get("pattern") not in GENERATED_PATTERNS]
    home = talking[0]
    generated: dict[str, dict[str, Any]] = {current["pattern"]: current for current in ir["pages"] if current.get("pattern") in GENERATED_PATTERNS}

    core_page = generated.get("core-words")
    if literacy["coreWords"]["enabled"] and core_page is None:
        core_page = core_words_page(literacy["coreWords"].get("words") or settings["literacy"]["coreWords"]["words"])
        report.append("Added a Core words page.")
    endings_page_obj = generated.get("word-endings")
    if literacy["wordEndings"]["enabled"] and endings_page_obj is None:
        endings_page_obj = endings_page(literacy["wordEndings"].get("endings") or settings["literacy"]["wordEndings"]["endings"])
        report.append("Added a Word endings page.")
    ring = talking + [item for item in (core_page if literacy["coreWords"]["enabled"] else None, endings_page_obj if literacy["wordEndings"]["enabled"] else None) if item]
    wire_ring(ring, len(talking), report)

    keyboard_existing = [current for current in ir["pages"] if current.get("pattern") in {"keyboard", "keyboard-letters"}]
    keyboard = literacy["keyboard"]
    if keyboard.get("enabled"):
        if not keyboard_existing:
            mode = keyboard.get("mode", "grouped")
            if mode == "full" and ir["access"]["visibleTargetLimit"] < 32:
                report.append("Full keyboard needs visibleTargetLimit >= 32; used the grouped keyboard instead.")
            keyboard_existing = keyboard_pages(home["id"], home["name"], keyboard.get("layout", "qwerty"), mode, ir["access"]["visibleTargetLimit"])
            report.append(f"Added a {keyboard.get('layout', 'qwerty').upper()} spelling keyboard ({len(keyboard_existing)} page(s)).")
        if not any(button.get("lexiconId") == "keyboard" for button in home["buttons"]):
            abc = word_button("keyboard", "btn-keyboard")
            abc["actions"] = [action("btn-keyboard", "navigate-page", targetPageId="page-keyboard")]
            home["buttons"].append(abc)
            report.append(f"{home['id']}: added the ABC keyboard button.")
    else:
        keyboard_existing = []

    if "community" in ir["audience"].get("settings", []) and not any(button.get("lexiconId") == "how-i-talk" for button in home["buttons"]):
        home["buttons"].insert(0, word_button("how-i-talk"))
        report.append(f"{home['id']}: added the 'How I talk' introduction for unfamiliar partners.")

    ir["pages"] = ring + keyboard_existing
    if (literacy["keyboard"].get("enabled") or literacy["coreWords"]["enabled"]) and not ir.get("messageBar", {}).get("enabled"):
        ir["messageBar"] = {"enabled": True, "placeholder": "Your message appears here.", "speakControl": True, "clearControl": False, "undoControl": False}
        report.append("Enabled the message bar for spelling and core words.")

    for current in ir["pages"]:
        for button in current["buttons"]:
            word_id = button.get("lexiconId")
            if word_id:
                apply_word(button, word_id, report)
            if not button.get("wordClass") and button.get("role") == "navigation":
                button["wordClass"] = "operation"

    if house["layoutSource"] == "house":
        for current in ir["pages"]:
            place_page(current, report)

    scheme = display.get("colourScheme", "none")
    for current in ir["pages"]:
        for button in current["buttons"]:
            fill = hs.fill_for(button.get("wordClass"), scheme)
            if fill:
                button.setdefault("style", {})["fillColour"] = fill

    functions = list(dict.fromkeys(ir["communicationFunctions"] + [button["function"] for current in ir["pages"] for button in current["buttons"]]))
    ir["communicationFunctions"] = functions
    if "partnerCard" not in ir:
        ir["partnerCard"] = default_partner_card(ir)
        report.append("Added a default partner card: choose this week's model words.")
    return canonicalize(ir), report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_file", type=Path)
    parser.add_argument("output_file", type=Path, nargs="?")
    parser.add_argument("--check", action="store_true", help="Exit 1 if applying the standards would change the IR.")
    args = parser.parse_args(argv)
    try:
        raw = json.loads(args.input_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot read IR: {error}", file=sys.stderr)
        return 1
    try:
        result, report = apply(raw)
    except HouseError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    if args.check:
        if result != raw:
            print(f"FAIL: {args.input_file} does not match the house standards; run apply_house_standards.py.")
            return 1
        print(f"PASS: {args.input_file} already meets the house standards.")
        return 0
    output = args.output_file or args.input_file
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for line in report:
        print(f"- {line}")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate an Agentic AAC Board IR JSON file.

This is a lightweight static gate. It checks the design contract, not whether a
resource is clinically appropriate for a specific student.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import house_standards as hs  # noqa: E402
from output_layout import grid_slots  # noqa: E402


ALLOWED_ROLES = {
    "core",
    "fringe",
    "repair",
    "navigation",
    "comment",
    "question",
    "sentence",
    "evidence",
    "teacher",
}

ALLOWED_FUNCTIONS = {
    "initiate",
    "request",
    "refuse",
    "choose",
    "comment",
    "ask",
    "answer",
    "sequence",
    "explain",
    "repair",
    "reflect",
    "socialise",
    "navigate",
    "regulate-rest",
}

ALLOWED_ACCESS_PROFILES = {
    "direct-selection",
    "eye-gaze-dwell",
    "mouse-dwell",
    "single-switch",
    "two-switch",
    "partner-assisted-print",
    "partner-assisted-scanning",
    "print-only",
    "keyboard",
    "mixed-access",
    "unspecified",
}

AGENCY_FUNCTIONS = {
    "initiate",
    "request",
    "refuse",
    "comment",
    "ask",
    "repair",
    "reflect",
    "socialise",
    "regulate-rest",
}

CONTENT_ONLY_FUNCTIONS = {"answer", "choose", "sequence"}
CONTENT_ONLY_ROLES = {"fringe", "evidence"}

REPAIR_LABELS = {
    "help",
    "stop",
    "finished",
    "finish",
    "different",
    "not that",
    "wrong one",
    "i don't know",
    "i do not know",
    "wait",
    "break",
    "show me",
}

RECOMMENDED_POWERHOUSE_FIELDS = {
    "sett",
    "udl",
    "differentiation",
    "participationBarriers",
    "evidencePlan",
}

SENSITIVE_ID_HINTS = {
    "diagnosis",
    "medical",
    "behaviour",
    "behavior",
    "oneschool",
    "nccd",
    "disability",
    "parent",
    "address",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def grid_size(page: dict[str, Any]) -> tuple[int, int]:
    grid = as_dict(page.get("grid"))
    rows = page.get("gridRows", grid.get("rows", 0))
    columns = page.get("gridColumns", grid.get("columns", 0))
    try:
        return int(rows), int(columns)
    except (TypeError, ValueError):
        return 0, 0


def button_spoken_text(button: dict[str, Any]) -> str:
    return (
        text(button.get("spokenText"))
        or text(button.get("speakText"))
        or text(button.get("audioCue"))
        or text(button.get("label"))
    )


def has_repair_route(pages: list[Any]) -> bool:
    for raw_page in pages:
        page = as_dict(raw_page)
        for raw_button in as_list(page.get("buttons")):
            button = as_dict(raw_button)
            label = text(button.get("label")).lower()
            role = text(button.get("role"))
            function = text(button.get("function"))
            if role == "repair" or function in {"repair", "refuse", "regulate-rest"}:
                return True
            if label in REPAIR_LABELS:
                return True
    return False


def content_button_count(pages: list[Any]) -> int:
    total = 0
    for raw_page in pages:
        page = as_dict(raw_page)
        for raw_button in as_list(page.get("buttons")):
            button = as_dict(raw_button)
            role = text(button.get("role"))
            if role not in {"repair", "navigation", "teacher"}:
                total += 1
    return total


def content_buttons(pages: list[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for raw_page in pages:
        page = as_dict(raw_page)
        for raw_button in as_list(page.get("buttons")):
            button = as_dict(raw_button)
            role = text(button.get("role"))
            if role not in {"repair", "navigation", "teacher"}:
                result.append(button)
    return result


def has_button_agency(pages: list[Any]) -> bool:
    for raw_page in pages:
        page = as_dict(raw_page)
        for raw_button in as_list(page.get("buttons")):
            button = as_dict(raw_button)
            if text(button.get("function")) in AGENCY_FUNCTIONS:
                return True
            if text(button.get("role")) in {"core", "repair", "comment", "question", "sentence"}:
                return True
    return False


def has_evidence_route(data: dict[str, Any], pages: list[Any]) -> bool:
    if as_dict(data.get("evidencePlan")):
        return True
    teacher_notes = as_dict(data.get("teacherNotes"))
    if text(teacher_notes.get("evidence")):
        return True
    for button in content_buttons(pages):
        if text(button.get("role")) == "evidence" or text(button.get("function")) in {"explain", "reflect"}:
            return True
    return False


def has_differentiation_metadata(data: dict[str, Any]) -> bool:
    return any(data.get(field) for field in ("sett", "udl", "differentiation", "participationBarriers"))


NAVIGATION_ACTION_TYPES = {"navigate-page", "next-page", "previous-page"}


def button_actions(button: dict[str, Any]) -> list[Any]:
    return as_list(button.get("actions"))


def navigation_target(action: Any) -> str:
    if isinstance(action, dict):
        return text(action.get("targetPageId")) or text(action.get("pageId"))
    return ""


def realised_button_functions(pages: list[Any]) -> set[str]:
    realised: set[str] = set()
    for raw_page in pages:
        page = as_dict(raw_page)
        for raw_button in as_list(page.get("buttons")):
            function = text(as_dict(raw_button).get("function"))
            if function:
                realised.add(function)
    return realised


def uses_symbol_strategy(data: dict[str, Any]) -> bool:
    if data.get("symbolStrategy"):
        return True
    for raw_page in as_list(data.get("pages")):
        page = as_dict(raw_page)
        for raw_button in as_list(page.get("buttons")):
            button = as_dict(raw_button)
            if button.get("searchTerm") or button.get("symbolId") or button.get("symbolSrc"):
                return True
    return False


def validate(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    if data.get("format") != "agentic-aac-board-ir":
        warnings.append("format is not 'agentic-aac-board-ir'; treating file as best-effort IR.")

    for field in ("id", "purpose", "communicationFunctions", "pages"):
        if not data.get(field):
            failures.append(f"Missing required top-level field: {field}")

    schema_version = text(data.get("schemaVersion"))
    communication_functions = as_list(data.get("communicationFunctions"))
    for value in communication_functions:
        function = text(value)
        if function and function not in ALLOWED_FUNCTIONS:
            failures.append(f"Unknown top-level communication function '{function}'.")
    if communication_functions:
        if not any(text(value) in AGENCY_FUNCTIONS for value in communication_functions):
            warnings.append("communicationFunctions does not include an obvious agency/social/repair function.")

    title = text(data.get("title")) or text(data.get("name"))
    if not title:
        failures.append("Missing title/name.")

    activity_id = text(data.get("id"))
    if activity_id and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", activity_id):
        warnings.append("id should be lowercase kebab-case without spaces.")
    if any(hint in activity_id.lower() for hint in SENSITIVE_ID_HINTS):
        failures.append("id appears to contain privacy-sensitive wording.")

    access = as_dict(data.get("access"))
    profile = text(access.get("profile")) or text(data.get("accessMethod")) or "unspecified"
    if profile not in ALLOWED_ACCESS_PROFILES:
        warnings.append(f"Unknown access profile '{profile}'.")
    intended = as_list(access.get("intended")) or as_list(as_dict(data.get("accessibility")).get("intendedAccess"))
    if not intended:
        warnings.append("No explicit intended access list found.")

    minimum_target = access.get("minimumTargetSizePx")
    if minimum_target is None:
        minimum_target = as_dict(data.get("accessibility")).get("minimumTargetSizePx")
    try:
        minimum_target_px = int(minimum_target) if minimum_target is not None else None
    except (TypeError, ValueError):
        minimum_target_px = None
        warnings.append("minimumTargetSizePx is not numeric.")

    pages = as_list(data.get("pages"))
    if not pages:
        failures.append("pages must be a non-empty array.")

    page_ids = {text(as_dict(raw_page).get("id")) for raw_page in pages if text(as_dict(raw_page).get("id"))}

    max_buttons_per_page = 0
    max_content_buttons_per_page = 0
    seen_page_ids: set[str] = set()
    seen_button_ids: set[str] = set()
    for page_index, raw_page in enumerate(pages, start=1):
        page = as_dict(raw_page)
        page_label = text(page.get("id")) or text(page.get("name")) or f"page {page_index}"
        page_id = text(page.get("id"))
        if page_id:
            if page_id in seen_page_ids:
                failures.append(f"Duplicate page id '{page_id}'.")
            seen_page_ids.add(page_id)
        all_buttons = as_list(page.get("buttons"))
        buttons = [raw for raw in all_buttons if as_dict(raw).get("hidden") is not True]
        rows, columns = grid_size(page)
        if rows <= 0 or columns <= 0:
            failures.append(f"{page_label}: grid rows/columns must be positive.")
        if not buttons:
            failures.append(f"{page_label}: page has no buttons.")
        if rows and columns and len(all_buttons) > rows * columns:
            failures.append(f"{page_label}: has more buttons than declared grid cells.")
        max_buttons_per_page = max(max_buttons_per_page, len(buttons))
        page_content_buttons = [
            as_dict(raw_button)
            for raw_button in buttons
            if text(as_dict(raw_button).get("role")) not in {"repair", "navigation", "teacher"}
        ]
        max_content_buttons_per_page = max(max_content_buttons_per_page, len(page_content_buttons))

        for button_index, raw_button in enumerate(all_buttons, start=1):
            button = as_dict(raw_button)
            button_label = text(button.get("id")) or f"{page_label} button {button_index}"
            button_id = text(button.get("id"))
            if not button_id:
                failures.append(f"{button_label}: missing id.")
            else:
                if button_id in seen_button_ids:
                    failures.append(f"Duplicate button id '{button_id}' (button ids must be unique across the whole board).")
                seen_button_ids.add(button_id)
            if not text(button.get("label")):
                failures.append(f"{button_label}: missing label.")
            if not button_spoken_text(button):
                failures.append(f"{button_label}: missing spokenText/audioCue.")

            role = text(button.get("role"))
            function = text(button.get("function"))
            if not role:
                failures.append(f"{button_label}: missing role.")
            elif role not in ALLOWED_ROLES:
                failures.append(f"{button_label}: unknown role '{role}'.")
            if not function:
                failures.append(f"{button_label}: missing communication function.")
            elif function not in ALLOWED_FUNCTIONS:
                failures.append(f"{button_label}: unknown function '{function}'.")
            if role == "teacher" and not page.get("teacherOnly"):
                failures.append(f"{button_label}: teacher button appears in a student-facing page.")

            has_navigation_action = False
            for action in button_actions(button):
                action_type = text(action.get("type")) if isinstance(action, dict) else text(action)
                if action_type not in NAVIGATION_ACTION_TYPES:
                    continue
                has_navigation_action = True
                if action_type == "navigate-page":
                    target = navigation_target(action)
                    if not target:
                        failures.append(f"{button_label}: navigate-page action has no targetPageId.")
                    elif page_ids and target not in page_ids:
                        failures.append(f"{button_label}: navigate-page targets unknown page '{target}'.")
            if (role == "navigation" or function == "navigate") and not has_navigation_action:
                warnings.append(
                    f"{button_label}: navigation button has no navigate-page/next-page/previous-page action; "
                    "the renderer will fall back to speak-only behaviour."
                )

    dense_gaze_raw = access.get("denseGazeTested", data.get("denseGazeTested"))
    dense_gaze_tested = dense_gaze_raw is True
    if dense_gaze_raw is not None and not isinstance(dense_gaze_raw, bool):
        warnings.append(
            f"denseGazeTested is {dense_gaze_raw!r}; it must be boolean true to lift the gaze density limit, "
            "so it is being treated as untested."
        )
    intended_access = {text(value).lower() for value in intended}
    gaze_in_intended = bool({"eye-gaze-dwell", "mouse-dwell"} & intended_access)
    if profile in {"eye-gaze-dwell", "mouse-dwell"} and max_buttons_per_page > 9 and not dense_gaze_tested:
        failures.append("Eye-gaze/mouse-dwell profile has more than 9 buttons on a page without denseGazeTested=true.")
    elif gaze_in_intended and max_buttons_per_page > 9 and not dense_gaze_tested:
        warnings.append(
            "Eye-gaze/mouse-dwell is listed in intended access but a page has more than 9 buttons; "
            "split into calmer pages, enlarge targets, or set denseGazeTested=true once dense gaze access is tested."
        )
    if profile in {"eye-gaze-dwell", "mouse-dwell"}:
        if minimum_target_px is None:
            failures.append(
                "Eye-gaze/mouse-dwell profile must declare a numeric minimumTargetSizePx of at least 120 "
                "(prefer 200+ per gaze-interface research)."
            )
        elif minimum_target_px < 120:
            failures.append("Eye-gaze/mouse-dwell profile should use minimumTargetSizePx >= 120.")
    if profile == "direct-selection" and minimum_target_px is not None and minimum_target_px < 44:
        failures.append("Direct-selection profile should not use minimumTargetSizePx below 44.")
    if profile in {"single-switch", "two-switch"} and max_buttons_per_page > 9:
        warnings.append("Switch-scanning board has more than 9 buttons on a page; confirm scan fatigue and pattern.")

    visible_target_limit = access.get("visibleTargetLimit")
    if visible_target_limit is not None:
        try:
            limit = int(visible_target_limit)
        except (TypeError, ValueError):
            failures.append("visibleTargetLimit must be an integer.")
        else:
            if max_buttons_per_page > limit:
                failures.append(
                    f"A page has {max_buttons_per_page} active student targets, exceeding visibleTargetLimit={limit}."
                )
    controls = as_dict(data.get("studentControls"))
    setup_limit = access.get("setupTargetLimit")
    if controls and setup_limit is not None:
        setup_count = sum(bool(controls.get(field)) for field in ("startBoard", "fullScreen", "soundCheck"))
        try:
            if setup_count > int(setup_limit):
                failures.append(
                    f"Setup has {setup_count} active student targets, exceeding setupTargetLimit={setup_limit}."
                )
        except (TypeError, ValueError):
            failures.append("setupTargetLimit must be an integer.")

    total_content_buttons = content_button_count(pages)
    if total_content_buttons > 2 and not has_repair_route(pages):
        failures.append("Board has more than two content buttons but no repair/refusal/finished route.")
    if total_content_buttons >= 4:
        content = content_buttons(pages)
        content_functions = {text(button.get("function")) for button in content if text(button.get("function"))}
        content_roles = {text(button.get("role")) for button in content if text(button.get("role"))}
        top_level_functions = {text(value) for value in communication_functions}
        if content_functions <= CONTENT_ONLY_FUNCTIONS and content_roles <= CONTENT_ONLY_ROLES and not top_level_functions.intersection(AGENCY_FUNCTIONS):
            failures.append("Board appears to be a noun/content grid with no communication agency function.")
        if content_functions <= {"answer"} or (top_level_functions <= {"answer", "choose"} and max_content_buttons_per_page >= 3 and not has_button_agency(pages)):
            failures.append("Board appears quiz-only or answer-only; add repair, explanation, uncertainty, or student agency.")

    declared_functions = {text(value) for value in communication_functions if text(value)}
    realised_functions = realised_button_functions(pages)
    if declared_functions and realised_functions:
        unrealised = sorted(declared_functions - realised_functions)
        undeclared = sorted(realised_functions - declared_functions)
        if unrealised:
            warnings.append(
                "communicationFunctions declares functions no button realises: " + ", ".join(unrealised) + "."
            )
        if undeclared:
            warnings.append(
                "Buttons realise functions missing from communicationFunctions: " + ", ".join(undeclared) + "."
            )

    all_action_types: set[str] = set()
    for raw_page in pages:
        for raw_button in as_list(as_dict(raw_page).get("buttons")):
            for action in button_actions(as_dict(raw_button)):
                action_type = text(action.get("type")) if isinstance(action, dict) else text(action)
                if action_type:
                    all_action_types.add(action_type)
    message_bar = as_dict(data.get("messageBar"))
    message_actions = {"add-to-message", "speak-message", "remove-last-word", "clear-message"}
    if message_bar:
        if "add-to-message" not in all_action_types:
            warnings.append("messageBar is declared but no button has an add-to-message action.")
        if "speak-message" not in all_action_types:
            warnings.append("messageBar is declared but no button has a speak-message action.")
    elif all_action_types & message_actions:
        warnings.append(
            "Buttons use message-bar actions (" + ", ".join(sorted(all_action_types & message_actions)) +
            ") but no top-level messageBar object is declared."
        )

    privacy = as_dict(data.get("privacy"))
    privacy_level = text(privacy.get("level")) or text(as_dict(data.get("metadata")).get("privacyLevel"))
    if not privacy_level:
        failures.append("Missing privacy level.")
    elif privacy_level not in {"anonymous", "local-profile", "sensitive-approved"}:
        warnings.append(f"Unrecognised privacy level '{privacy_level}'.")

    attribution = as_list(data.get("attribution")) or as_list(data.get("licences"))
    if uses_symbol_strategy(data) and not attribution:
        failures.append("Symbol strategy/search terms detected but attribution/licensing notes are missing.")

    teacher_notes = as_dict(data.get("teacherNotes"))
    if not teacher_notes:
        warnings.append("Missing teacherNotes.")
    elif not text(teacher_notes.get("modeling")):
        warnings.append("teacherNotes should include a modeling note.")
    if schema_version.startswith("0.3"):
        missing_powerhouse = sorted(field for field in RECOMMENDED_POWERHOUSE_FIELDS if not data.get(field))
        if missing_powerhouse:
            warnings.append("IR 0.3.0 is missing recommended powerhouse fields: " + ", ".join(missing_powerhouse))
    if not has_differentiation_metadata(data):
        warnings.append("Differentiation/UDL/SETT metadata is thin; add supports when the task is more than a tiny board.")
    if not has_evidence_route(data, pages):
        warnings.append("Evidence route is thin; add evidencePlan or teacherNotes.evidence when curriculum/QCIA evidence matters.")

    house_checks(data, failures, warnings)
    return failures, warnings


ACTIVE_STRIP = {"speak-text", "speak-label", "add-to-message", "log-attempt"}


def page_cells(page: dict[str, Any]) -> dict[str, tuple[int, int]]:
    try:
        return {button["id"]: (row + 1, column + 1) for row, column, button in grid_slots(page)}
    except (KeyError, TypeError, ValueError):
        return {}


def house_checks(data: dict[str, Any], failures: list[str], warnings: list[str]) -> None:
    """House word list, layout, literacy, colour, partner-card and schedule checks."""
    pages = [as_dict(raw) for raw in as_list(data.get("pages"))]
    house = as_dict(data.get("house"))
    if not house:
        if text(data.get("schemaVersion")) >= "0.5.0":
            failures.append("IR 0.5.0 must record house standards; run scripts/apply_house_standards.py.")
        else:
            warnings.append("House standards (layout, word list, literacy pages) not applied; run scripts/apply_house_standards.py.")
        return
    lexicon = hs.words()
    button_ids: dict[str, str] = {}
    for page in pages:
        for raw in as_list(page.get("buttons")):
            button = as_dict(raw)
            button_ids[text(button.get("id"))] = text(page.get("id"))

    # Same button, same message: every recurring word uses the shared word list.
    for page in pages:
        for raw in as_list(page.get("buttons")):
            button = as_dict(raw)
            bid = text(button.get("id"))
            lexicon_id = text(button.get("lexiconId"))
            if lexicon_id:
                entry = lexicon.get(lexicon_id)
                if entry is None:
                    failures.append(f"{bid}: unknown house word '{lexicon_id}'.")
                    continue
                for field in ("label", "spokenText", "wordClass"):
                    if button.get(field) != entry[field]:
                        failures.append(
                            f"{bid}: house word '{lexicon_id}' must use {field} {entry[field]!r}, not {button.get(field)!r}."
                        )
                speech = [as_dict(action).get("text") for action in as_list(button.get("actions")) if as_dict(action).get("type") in {"speak-text", "add-to-message"}]
                if any(value != entry["spokenText"] for value in speech if value):
                    failures.append(f"{bid}: house word '{lexicon_id}' speaks something other than {entry['spokenText']!r}.")
            else:
                match = hs.lexicon_match(text(button.get("label")), text(button.get("wordClass")))
                if match:
                    failures.append(
                        f"{bid}: label {text(button.get('label'))!r} is the house word '{match}'; set lexiconId so it says "
                        f"{lexicon[match]['spokenText']!r} on every board."
                    )
            if not button.get("hidden") and not text(button.get("wordClass")):
                warnings.append(f"{bid}: no wordClass; colour coding and logging need one.")

    # Permanent addresses for house words.
    if text(house.get("layoutSource")) == "house":
        for page in pages:
            rows, columns = grid_size(page)
            cells = page_cells(page)
            page_id = text(page.get("id"))
            used: dict[tuple[int, int], str] = {}
            help_cell = hs.house_address("help", rows, columns)
            if rows < 2 or columns < 2:
                warnings.append(f"{page_id}: no house layout for a {rows}x{columns} grid.")
                continue
            for raw in as_list(page.get("buttons")):
                button = as_dict(raw)
                bid = text(button.get("id"))
                slot = hs.slot_for_button(button)
                cell = cells.get(bid)
                if slot:
                    address = hs.house_address(slot, rows, columns)
                    if address is None:
                        warnings.append(f"{page_id}: no house address for '{slot}' on a {rows}x{columns} grid ({bid}).")
                    elif cell != address:
                        failures.append(
                            f"{page_id}: '{text(button.get('label'))}' must sit at house address row {address[0]}, column {address[1]} "
                            f"(found {cell}). House words never move between boards."
                        )
                    elif address in used:
                        failures.append(f"{page_id}: '{used[address]}' and '{text(button.get('label'))}' share house address {address}.")
                    if address:
                        used[address] = text(button.get("label"))
                elif cell and cell == help_cell and not button.get("hidden"):
                    warnings.append(f"{page_id}: content '{text(button.get('label'))}' sits in the Help cell; Help lives there on every other board.")

    # Literacy: a keyboard from the first page, or a recorded reason.
    literacy = as_dict(data.get("literacy"))
    keyboard = as_dict(literacy.get("keyboard"))
    if not keyboard:
        warnings.append("literacy.keyboard is not declared; every board should reach a spelling keyboard or record why not.")
    elif keyboard.get("enabled") is True:
        keyboard_pages = {text(page.get("id")) for page in pages if text(page.get("pattern")) == "keyboard"}
        if not keyboard_pages:
            failures.append("literacy.keyboard is enabled but there is no keyboard page.")
        elif pages:
            reaches = any(
                as_dict(action).get("type") == "navigate-page" and text(as_dict(action).get("targetPageId")) in keyboard_pages
                for raw in as_list(pages[0].get("buttons")) for action in as_list(as_dict(raw).get("actions"))
            )
            if not reaches:
                failures.append("The first page has no ABC button reaching the keyboard page.")
        if not as_dict(data.get("messageBar")).get("enabled"):
            failures.append("A keyboard needs an enabled messageBar so spelled words can be seen and spoken.")
    elif keyboard.get("enabled") is False and len(text(keyboard.get("omitReason"))) < 10:
        failures.append("literacy.keyboard is disabled without an omitReason.")

    # Colour means word class.
    display = as_dict(data.get("display"))
    scheme = text(display.get("colourScheme")) or "none"
    if text(display.get("visualProfile")) == "cvi" and scheme != "none":
        warnings.append("CVI profile should switch word-class colour coding off (colourScheme 'none').")
    if scheme != "none":
        for page in pages:
            for raw in as_list(page.get("buttons")):
                button = as_dict(raw)
                expected = hs.fill_for(text(button.get("wordClass")), scheme)
                actual = text(as_dict(button.get("style")).get("fillColour"))
                if expected and actual.lower() != expected.lower():
                    warnings.append(
                        f"{text(button.get('id'))}: fill {actual or 'none'} is not the {scheme} colour {expected} for "
                        f"'{text(button.get('wordClass'))}'; colour should mean word type, not decoration."
                    )

    # Community boards introduce the student's way of talking.
    settings = [text(value) for value in as_list(as_dict(data.get("audience")).get("settings"))]
    if "community" in settings and pages:
        if not any(text(as_dict(raw).get("lexiconId")) == "how-i-talk" for raw in as_list(pages[0].get("buttons"))):
            failures.append("Community board needs the 'How I talk' introduction on its first page.")

    # Partner card.
    card = as_dict(data.get("partnerCard"))
    if not card:
        warnings.append("No partnerCard: add 3-5 model words, wait time and comment examples for communication partners.")
    else:
        for bid in as_list(card.get("modelWords")):
            if text(bid) not in button_ids:
                failures.append(f"partnerCard model word '{bid}' is not a button on this board.")
        try:
            if int(card.get("waitSeconds", 0)) < 5:
                failures.append("partnerCard.waitSeconds must be at least 5.")
        except (TypeError, ValueError):
            failures.append("partnerCard.waitSeconds must be a whole number of seconds.")

    # Schedules refer to real steps on their own page.
    for page in pages:
        schedule = as_dict(page.get("schedule"))
        if not schedule:
            continue
        own = {text(as_dict(raw).get("id")) for raw in as_list(page.get("buttons"))}
        for bid in as_list(schedule.get("steps")):
            if text(bid) not in own:
                failures.append(f"{text(page.get('id'))}: schedule step '{bid}' is not a button on this page.")

    log = as_dict(data.get("evidenceLog"))
    if log.get("enabled") is True and not as_dict(data.get("evidencePlan")):
        warnings.append("evidenceLog is enabled without an evidencePlan saying what the log is for.")
    if not as_dict(data.get("speech")):
        warnings.append("No speech settings: boards should prefer an installed voice so speech works offline.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Agentic AAC Board IR JSON file.")
    parser.add_argument("json_file", type=Path)
    args = parser.parse_args()

    try:
        data = json.loads(args.json_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"FAIL: invalid JSON: {error}")
        return 1

    if not isinstance(data, dict):
        print("FAIL: top-level JSON value must be an object.")
        return 1

    failures, warnings = validate(data)
    for warning in warnings:
        print(f"WARN: {warning}")
    for failure in failures:
        print(f"FAIL: {failure}")

    if failures:
        return 1
    print(f"PASS: {args.json_file} satisfies the static AAC Board IR checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

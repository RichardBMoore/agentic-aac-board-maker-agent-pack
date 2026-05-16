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

    communication_functions = as_list(data.get("communicationFunctions"))
    for value in communication_functions:
        function = text(value)
        if function and function not in ALLOWED_FUNCTIONS:
            failures.append(f"Unknown top-level communication function '{function}'.")
    if communication_functions:
        agency_functions = {
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
        if not any(text(value) in agency_functions for value in communication_functions):
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
    intended = as_list(access.get("intended")) or as_list(as_dict(data.get("accessibility")).get("intendedAccess"))
    if not intended:
        warnings.append("No explicit intended access list found.")

    minimum_target = access.get("minimumTargetSizePx") or as_dict(data.get("accessibility")).get("minimumTargetSizePx")
    try:
        minimum_target_px = int(minimum_target) if minimum_target is not None else None
    except (TypeError, ValueError):
        minimum_target_px = None
        warnings.append("minimumTargetSizePx is not numeric.")

    pages = as_list(data.get("pages"))
    if not pages:
        failures.append("pages must be a non-empty array.")

    max_buttons_per_page = 0
    for page_index, raw_page in enumerate(pages, start=1):
        page = as_dict(raw_page)
        page_label = text(page.get("id")) or text(page.get("name")) or f"page {page_index}"
        buttons = as_list(page.get("buttons"))
        rows, columns = grid_size(page)
        if rows <= 0 or columns <= 0:
            failures.append(f"{page_label}: grid rows/columns must be positive.")
        if not buttons:
            failures.append(f"{page_label}: page has no buttons.")
        if rows and columns and len(buttons) > rows * columns:
            failures.append(f"{page_label}: has more buttons than declared grid cells.")
        max_buttons_per_page = max(max_buttons_per_page, len(buttons))

        for button_index, raw_button in enumerate(buttons, start=1):
            button = as_dict(raw_button)
            button_label = text(button.get("id")) or f"{page_label} button {button_index}"
            if not text(button.get("id")):
                failures.append(f"{button_label}: missing id.")
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

    dense_gaze_tested = bool(access.get("denseGazeTested") or data.get("denseGazeTested"))
    if profile in {"eye-gaze-dwell", "mouse-dwell"} and max_buttons_per_page > 9 and not dense_gaze_tested:
        failures.append("Eye-gaze/mouse-dwell profile has more than 9 buttons on a page without denseGazeTested=true.")
    if profile in {"eye-gaze-dwell", "mouse-dwell"} and minimum_target_px is not None and minimum_target_px < 120:
        failures.append("Eye-gaze/mouse-dwell profile should use minimumTargetSizePx >= 120.")
    if profile == "direct-selection" and minimum_target_px is not None and minimum_target_px < 44:
        failures.append("Direct-selection profile should not use minimumTargetSizePx below 44.")
    if profile in {"single-switch", "two-switch"} and max_buttons_per_page > 9:
        warnings.append("Switch-scanning board has more than 9 buttons on a page; confirm scan fatigue and pattern.")

    if content_button_count(pages) > 2 and not has_repair_route(pages):
        failures.append("Board has more than two content buttons but no repair/refusal/finished route.")

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

    return failures, warnings


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

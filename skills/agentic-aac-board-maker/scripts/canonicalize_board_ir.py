#!/usr/bin/env python3
"""Canonicalise legacy AAC Board IR data into renderer-independent IR 0.4.0."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "0.4.0"
FORMAT = "agentic-aac-board-ir"

STRING_ACTION_SHORTHANDS = {
    "speak": "speak-text",
    "speak-text": "speak-text",
    "speak-label": "speak-label",
    "log": "log-attempt",
    "log-attempt": "log-attempt",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def slug(value: Any, fallback: str) -> str:
    raw = text(value).lower() or fallback
    raw = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return raw or fallback


def gaze_intended(access: dict[str, Any]) -> bool:
    intended = {text(value).lower() for value in as_list(access.get("intended"))}
    return text(access.get("profile")) in {"eye-gaze-dwell", "mouse-dwell"} or bool(
        intended & {"eye-gaze-dwell", "mouse-dwell"}
    )


def canonical_action(action: Any, button_id: str, spoken: str, index: int) -> dict[str, Any] | None:
    if isinstance(action, dict):
        result = copy.deepcopy(action)
        action_type = text(result.get("type"))
        if not action_type:
            return None
        result["type"] = STRING_ACTION_SHORTHANDS.get(action_type, action_type)
        result.setdefault("id", f"act-{button_id}-{index + 1}")
        if result["type"] == "speak-text":
            result.setdefault("text", spoken)
        target = text(result.get("targetPageId")) or text(result.get("pageId"))
        if target and result["type"] in {"navigate-page", "next-page", "previous-page"}:
            result["targetPageId"] = target
            result.pop("pageId", None)
        return result
    action_type = STRING_ACTION_SHORTHANDS.get(text(action), text(action))
    if not action_type:
        return None
    result: dict[str, Any] = {"id": f"act-{button_id}-{index + 1}", "type": action_type}
    if action_type == "speak-text":
        result["text"] = spoken
    return result


def canonical_button(raw: Any, page_id: str, index: int) -> dict[str, Any]:
    button = as_dict(raw)
    label = text(button.get("label")) or f"Button {index + 1}"
    button_id = slug(button.get("id") or label, f"{page_id}-button-{index + 1}")
    spoken = (
        text(button.get("spokenText"))
        or text(button.get("speakText"))
        or text(button.get("audioCue"))
        or label
    )
    actions = [
        rendered
        for action_index, action in enumerate(as_list(button.get("actions")))
        if (rendered := canonical_action(action, button_id, spoken, action_index)) is not None
    ]
    if not actions:
        actions = [
            {"id": f"act-{button_id}-speak", "type": "speak-text", "text": spoken},
            {"id": f"act-{button_id}-log", "type": "log-attempt"},
        ]

    result: dict[str, Any] = {
        "id": button_id,
        "label": label,
        "role": text(button.get("role")) or "fringe",
        "function": text(button.get("function")) or "choose",
        "spokenText": spoken,
        "searchTerm": text(button.get("searchTerm")),
        "symbolId": button.get("symbolId") if button.get("symbolId") not in ("", 0) else None,
        "symbolSrc": text(button.get("symbolSrc")),
        "symbolLayout": text(button.get("symbolLayout")) or "label-bottom",
        "actions": actions,
    }
    optional_fields = (
        "symbolateSegments",
        "audioCue",
        "result",
        "type",
        "state",
        "position",
        "style",
        "font",
        "evidenceTag",
        "udl",
        "differentiation",
        "communicationPartnerCue",
    )
    for field in optional_fields:
        if field in button and button[field] not in (None, "", [], {}):
            result[field] = copy.deepcopy(button[field])
    return result


def canonical_page(raw: Any, index: int) -> dict[str, Any]:
    page = as_dict(raw)
    page_id = slug(page.get("id") or page.get("name"), f"page-{index + 1}")
    grid = as_dict(page.get("grid"))
    rows = to_int(grid.get("rows", page.get("gridRows")), 1)
    columns = to_int(grid.get("columns", page.get("gridColumns")), 1)
    result: dict[str, Any] = {
        "id": page_id,
        "name": text(page.get("name")) or f"Page {index + 1}",
        "pattern": text(page.get("pattern")) or "choice-board",
        "layout": "grid",
        "grid": {"rows": max(1, rows), "columns": max(1, columns)},
        "buttons": [canonical_button(button, page_id, button_index) for button_index, button in enumerate(as_list(page.get("buttons")))],
    }
    for field in ("margin", "backgroundColour", "backgroundImage"):
        if field in page and page[field] not in (None, ""):
            result[field] = copy.deepcopy(page[field])
    return result


def canonical_attribution(data: dict[str, Any]) -> list[dict[str, Any]]:
    entries = as_list(data.get("attribution")) or as_list(data.get("licences"))
    result: list[dict[str, Any]] = []
    for raw in entries:
        entry = as_dict(raw)
        source = text(entry.get("source"))
        licence = text(entry.get("licence")) or text(entry.get("license")) or text(entry.get("type"))
        if not source and not licence:
            continue
        rendered = {"source": source or "Unknown", "licence": licence or "Review required"}
        for field in ("attribution", "note", "url"):
            if text(entry.get(field)):
                rendered[field] = text(entry.get(field))
        result.append(rendered)
    if result:
        return result
    symbol_source = text(as_dict(data.get("symbolStrategy")).get("defaultSource")).lower()
    if "arasaac" in symbol_source or not symbol_source:
        return [
            {
                "source": "ARASAAC",
                "licence": "CC BY-NC-SA",
                "attribution": (
                    "The pictographic symbols used are the property of the Government of Aragon and have been "
                    "created by Sergio Palao for ARASAAC (https://arasaac.org), which distributes them under "
                    "Creative Commons License BY-NC-SA."
                ),
                "note": "Text fallback is retained when no reviewed pictogram is embedded.",
            }
        ]
    return [{"source": "Text only", "licence": "No external symbol assets embedded"}]


def default_system_fit() -> dict[str, str]:
    return {
        "reviewStatus": "team-input-needed",
        "existingSystem": "Confirm how this support sits alongside the student's established AAC system.",
        "vocabularyAndMotorPlan": "Confirm familiar vocabulary and stable locations before classroom use.",
        "symbolFamiliarity": "Confirm that each symbol or text representation is recognised and meaningful.",
        "accessCalibration": "Confirm access settings on the actual device with the student and team.",
        "positioningAndVision": "Confirm screen, mounting, seating, visual field, contrast and fatigue conditions.",
        "languageCultureVoice": "Confirm preferred language, culturally meaningful vocabulary and voice output.",
        "partnerSignals": "Confirm reliable yes/no, cancel, repair and partner-assisted signals.",
    }


def merged_defaults(defaults: dict[str, Any], value: Any) -> dict[str, Any]:
    return {**defaults, **copy.deepcopy(as_dict(value))}


def canonical_message_bar(value: Any) -> dict[str, Any] | None:
    raw = as_dict(value)
    if not raw:
        return None
    return {
        "enabled": bool(raw.get("enabled", True)),
        "placeholder": text(raw.get("placeholder")) or "Build your message here.",
        "speakControl": bool(raw.get("speakControl", False)),
        "clearControl": bool(raw.get("clearControl", False)),
        "undoControl": bool(raw.get("undoControl", False)),
    }


def canonicalize(data: dict[str, Any]) -> dict[str, Any]:
    """Return a new canonical IR 0.4.0 object without target-renderer aliases."""
    raw = copy.deepcopy(data)
    access_raw = as_dict(raw.get("access"))
    accessibility = as_dict(raw.get("accessibility"))
    settings = as_dict(raw.get("settings"))
    intended = as_list(access_raw.get("intended")) or as_list(accessibility.get("intendedAccess")) or ["touch", "keyboard"]
    profile = text(access_raw.get("profile")) or text(raw.get("accessMethod")) or "unspecified"
    access_seed = {"intended": intended, "profile": profile}
    uses_gaze = gaze_intended(access_seed)
    minimum_target = to_int(
        access_raw.get("minimumTargetSizePx", accessibility.get("minimumTargetSizePx")),
        120 if uses_gaze else 96,
    )
    if uses_gaze:
        minimum_target = max(120, minimum_target)
    dwell_raw = access_raw.get("dwellTimeMs", settings.get("dwellTimeMs"))
    dwell_time = to_int(dwell_raw, 1200) if uses_gaze else (to_int(dwell_raw, 1200) if dwell_raw is not None else None)
    visible_limit = to_int(access_raw.get("visibleTargetLimit"), 9 if uses_gaze else 16)
    if uses_gaze and access_raw.get("denseGazeTested") is not True:
        visible_limit = min(9, visible_limit)

    title = text(raw.get("title")) or text(raw.get("name")) or "AAC Board"
    audience_raw = as_dict(raw.get("audience"))
    symbol_strategy = copy.deepcopy(as_dict(raw.get("symbolStrategy")))
    symbol_strategy.setdefault("defaultSource", "ARASAAC search terms")
    symbol_strategy["textFallback"] = True
    symbol_strategy.setdefault("customMediaPolicy", "teacher-owned local media only unless explicitly approved")
    symbol_strategy.setdefault("reviewRequired", True)

    result: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "format": FORMAT,
        "id": slug(raw.get("id") or title, "aac-board"),
        "title": title,
        "purpose": text(raw.get("purpose")) or "Draft classroom communication support.",
        "audience": {
            "ageBand": text(audience_raw.get("ageBand")) or "unspecified",
            "tone": text(audience_raw.get("tone")) or "age-respectful",
            "locale": text(audience_raw.get("locale")) or "en-AU",
        },
        "access": {
            "intended": list(dict.fromkeys(text(value) for value in intended if text(value))),
            "profile": profile,
            "minimumTargetSizePx": minimum_target,
            "dwellTimeMs": dwell_time,
            "denseGazeTested": access_raw.get("denseGazeTested") is True,
            "visibleTargetLimit": visible_limit,
            "setupTargetLimit": to_int(access_raw.get("setupTargetLimit"), 3),
            "switchScanning": bool(access_raw.get("switchScanning", settings.get("switchScanning", False))),
            "scanSpeedMs": to_int(access_raw.get("scanSpeedMs", settings.get("scanSpeedMs")), 1400),
            "scanPattern": text(access_raw.get("scanPattern")) or text(settings.get("scanPattern")) or "linear",
            "scanOrder": text(access_raw.get("scanOrder")) or text(accessibility.get("scanOrder")) or "dom-order",
            "audioCues": bool(access_raw.get("audioCues", accessibility.get("audioCues", True))),
        },
        "display": {
            "orientation": text(as_dict(raw.get("display")).get("orientation")) or text(settings.get("orientation")) or "landscape",
            "width": to_int(as_dict(raw.get("display")).get("width", settings.get("width")), 1024),
            "height": to_int(as_dict(raw.get("display")).get("height", settings.get("height")), 768),
            "backgroundColour": text(as_dict(raw.get("display")).get("backgroundColour")) or text(settings.get("backgroundColour")) or "#f7fbff",
        },
        "studentControls": merged_defaults(
            {
                "startBoard": uses_gaze,
                "fullScreen": uses_gaze,
                "soundCheck": uses_gaze,
                "stopSpeechDuringPlayback": True,
                "teacherPanel": False,
            },
            raw.get("studentControls"),
        ),
        "communicationFunctions": list(dict.fromkeys(text(value) for value in as_list(raw.get("communicationFunctions")) if text(value))),
        "pages": [canonical_page(page, index) for index, page in enumerate(as_list(raw.get("pages")))],
        "teacherNotes": merged_defaults(
            {
                "modeling": "Model key words while speaking, wait, respond to communication and accept multimodal responses.",
                "evidence": "Observe communication and participation without treating access performance as curriculum judgement.",
                "customisation": "Review vocabulary, symbols and positions with the student and team before use.",
            },
            raw.get("teacherNotes"),
        ),
        "systemFit": merged_defaults(default_system_fit(), raw.get("systemFit")),
        "symbolStrategy": symbol_strategy,
        "privacy": {
            "level": text(as_dict(raw.get("privacy")).get("level")) or text(as_dict(raw.get("metadata")).get("privacyLevel")) or "anonymous",
            "containsSensitiveData": bool(as_dict(raw.get("privacy")).get("containsSensitiveData", False)),
        },
        "attribution": canonical_attribution(raw),
    }

    if not result["communicationFunctions"]:
        result["communicationFunctions"] = ["repair"]

    message_bar = canonical_message_bar(raw.get("messageBar"))
    if message_bar is not None:
        result["messageBar"] = message_bar

    for field in ("navigation", "sett", "udl", "differentiation", "participationBarriers", "evidencePlan", "variables"):
        if raw.get(field) not in (None, "", [], {}):
            result[field] = copy.deepcopy(raw[field])

    provenance = copy.deepcopy(as_dict(raw.get("provenance")))
    if text(raw.get("fixtureId")):
        provenance["fixtureId"] = text(raw.get("fixtureId"))
    if text(raw.get("sourcePrompt")):
        provenance["sourcePrompt"] = text(raw.get("sourcePrompt"))
    if provenance:
        result["provenance"] = provenance
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", type=Path)
    parser.add_argument("output_file", type=Path, nargs="?")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if the input is not already canonical.")
    args = parser.parse_args(argv)

    try:
        raw = json.loads(args.input_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot read IR: {error}", file=sys.stderr)
        return 1
    if not isinstance(raw, dict):
        print("FAIL: IR top-level value must be an object.", file=sys.stderr)
        return 1

    canonical = canonicalize(raw)
    if args.check:
        if raw != canonical:
            print(f"FAIL: {args.input_file} is not canonical IR {SCHEMA_VERSION}.")
            return 1
        print(f"PASS: {args.input_file} is canonical IR {SCHEMA_VERSION}.")
        return 0

    output = args.output_file or args.input_file
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(canonical, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote canonical IR {SCHEMA_VERSION}: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

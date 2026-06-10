#!/usr/bin/env python3
"""Render canonical AAC Board IR to Open AAC Studio-compatible JSON."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ARASAAC's required attribution names the author, owner, origin, and licence.
# See https://arasaac.org/terms-of-use — keep the licence unversioned ("CC BY-NC-SA")
# to match ARASAAC's own wording.
ARASAAC_ATTRIBUTION = (
    "The pictographic symbols used are the property of the Government of Aragon and have been "
    "created by Sergio Palao for ARASAAC (https://arasaac.org), that distributes them under "
    "Creative Commons License BY-NC-SA."
)


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


def slug(value: str, fallback: str) -> str:
    raw = text(value).lower() or fallback
    raw = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return raw or fallback


def now_iso() -> str:
    """Current UTC time, overridable via SOURCE_DATE_EPOCH for reproducible builds."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch is not None:
        try:
            return datetime.fromtimestamp(int(epoch), timezone.utc).isoformat().replace("+00:00", "Z")
        except (ValueError, OverflowError, OSError):
            pass
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def grid(page: dict[str, Any]) -> tuple[int, int]:
    grid_data = as_dict(page.get("grid"))
    rows = page.get("gridRows", grid_data.get("rows", 1))
    columns = page.get("gridColumns", grid_data.get("columns", 1))
    return max(1, to_int(rows, 1)), max(1, to_int(columns, 1))


def position(index: int, rows: int, columns: int) -> dict[str, float]:
    row = index // columns
    column = index % columns
    return {
        "x": round(column * (100 / columns), 4),
        "y": round(row * (100 / rows), 4),
        "width": round(100 / columns, 4),
        "height": round(100 / rows, 4),
    }


STRING_ACTION_SHORTHANDS = {
    "speak": "speak-text",
    "speak-text": "speak-text",
    "speak-label": "speak-label",
    "log": "log-attempt",
    "log-attempt": "log-attempt",
}


def action_list(button: dict[str, Any]) -> list[dict[str, Any]]:
    spoken = text(button.get("spokenText")) or text(button.get("speakText")) or text(button.get("audioCue")) or text(button.get("label"))
    button_slug = slug(text(button.get("id")), "button")
    result: list[dict[str, Any]] = []
    for action in as_list(button.get("actions")):
        if isinstance(action, dict):
            rendered = dict(action)
            # The bundled player reads action.pageId while the IR documents
            # targetPageId; emit both so either consumer navigates correctly.
            if text(rendered.get("type")) == "navigate-page":
                target = text(rendered.get("targetPageId")) or text(rendered.get("pageId"))
                if target:
                    rendered.setdefault("targetPageId", target)
                    rendered.setdefault("pageId", target)
                else:
                    print(
                        f"WARN: navigate-page action on button '{button_slug}' has no targetPageId; "
                        "navigation will be dead in the player.",
                        file=sys.stderr,
                    )
            result.append(rendered)
            continue
        action_name = text(action)
        if action_name == "navigate-page":
            print(
                f"WARN: string-form navigate-page on button '{button_slug}' carries no target page; "
                "use a dict action with targetPageId instead. Skipping.",
                file=sys.stderr,
            )
            continue
        if action_name in {"next-page", "previous-page", "mark-correct", "mark-incorrect"}:
            result.append({"id": f"act-{button_slug}-{action_name}", "type": action_name})
        elif action_name in STRING_ACTION_SHORTHANDS:
            rendered_type = STRING_ACTION_SHORTHANDS[action_name]
            rendered = {"id": f"act-{button_slug}-{rendered_type}", "type": rendered_type}
            if rendered_type == "speak-text":
                rendered["text"] = spoken
            result.append(rendered)
        elif action_name:
            print(f"WARN: unknown string action '{action_name}' on button '{button_slug}'; skipping.", file=sys.stderr)
    if result:
        return result
    result = [
        {"id": f"act-{button_slug}-speak", "type": "speak-text", "text": spoken},
        {"id": f"act-{button_slug}-log", "type": "log-attempt"},
    ]
    return result


DEFAULT_BUTTON_STYLE = {
    "borderColour": "#17212b",
    "borderWidth": 3,
    "borderStyle": "solid",
    "shape": "rounded-rect",
    "fillColour": "#ffffff",
    "gradientColour": None,
    "gradientType": "none",
}

DEFAULT_BUTTON_FONT = {
    "family": "Verdana",
    "size": 18,
    "bold": True,
    "italic": False,
    "colour": "#000000",
    "align": "centre",
}


def render_button(button: dict[str, Any], index: int, rows: int, columns: int) -> dict[str, Any]:
    label = text(button.get("label")) or "Button"
    button_id = slug(text(button.get("id")) or label, f"btn-{index + 1}")
    spoken = text(button.get("spokenText")) or text(button.get("speakText")) or text(button.get("audioCue")) or label
    symbol_layout = text(button.get("symbolLayout")) or "label-bottom"
    # Preserve the IR's semantic colour coding (repair red, navigation grey, ...)
    # by merging any per-button style/font over the defaults.
    style = {**DEFAULT_BUTTON_STYLE, **as_dict(button.get("style"))}
    font = {**DEFAULT_BUTTON_FONT, **as_dict(button.get("font"))}
    rendered = {
        "id": button_id,
        "type": text(button.get("type")) or "standard",
        "label": label,
        "role": text(button.get("role")),
        "function": text(button.get("function")),
        "spokenText": spoken,
        "symbolId": button.get("symbolId"),
        "symbolSrc": text(button.get("symbolSrc")),
        "searchTerm": text(button.get("searchTerm")) or label.lower(),
        "symbolLayout": symbol_layout,
        "symbolateSegments": as_list(button.get("symbolateSegments")),
        "position": as_dict(button.get("position")) or position(index, rows, columns),
        "style": style,
        "font": font,
        "state": text(button.get("state")) or "selectable",
        "audioCue": text(button.get("audioCue")) or spoken,
        "result": text(button.get("result")) or "selected",
        "actions": action_list(button),
    }
    for field in ("evidenceTag", "udl", "differentiation", "communicationPartnerCue"):
        if button.get(field):
            rendered[field] = button.get(field)
    return rendered


def preserved_ir_metadata(ir: dict[str, Any], access_profile: str) -> dict[str, Any]:
    """Keep IR 0.3 design metadata available without changing the app schema."""
    preserved: dict[str, Any] = {
        "accessProfile": access_profile,
        "purpose": text(ir.get("purpose")),
        "audience": as_dict(ir.get("audience")),
    }
    for field in ("sett", "udl", "differentiation", "participationBarriers", "evidencePlan", "symbolStrategy"):
        value = ir.get(field)
        if value:
            preserved[field] = value
    return preserved


def render(ir: dict[str, Any]) -> dict[str, Any]:
    created = now_iso()
    access = as_dict(ir.get("access"))
    accessibility = as_dict(ir.get("accessibility"))
    metadata = as_dict(ir.get("metadata"))
    privacy = as_dict(ir.get("privacy"))
    title = text(ir.get("title")) or text(ir.get("name")) or "AAC Board"
    activity_id = slug(text(ir.get("id")) or title, "activity")
    intended = as_list(access.get("intended")) or as_list(accessibility.get("intendedAccess")) or ["touch", "keyboard"]
    profile = text(access.get("profile"))
    dwell_profile = profile in {"eye-gaze-dwell", "mouse-dwell"}
    dwell_time = access.get("dwellTimeMs")
    if dwell_time is None:
        dwell_time = 1200 if dwell_profile else as_dict(ir.get("settings")).get("dwellTimeMs", 1200)

    pages: list[dict[str, Any]] = []
    for page_index, raw_page in enumerate(as_list(ir.get("pages")), start=1):
        page = as_dict(raw_page)
        rows, columns = grid(page)
        buttons = [
            render_button(as_dict(button), index, rows, columns)
            for index, button in enumerate(as_list(page.get("buttons")))
        ]
        pages.append(
            {
                "id": slug(text(page.get("id")) or text(page.get("name")), f"page-{page_index}"),
                "name": text(page.get("name")) or f"Page {page_index}",
                "pattern": text(page.get("pattern")),
                "layout": text(page.get("layout")) or "grid",
                "gridColumns": columns,
                "gridRows": rows,
                "margin": to_int(page.get("margin"), 10),
                "backgroundColour": text(page.get("backgroundColour")) or "#ffffff",
                "backgroundImage": page.get("backgroundImage"),
                "buttons": buttons,
            }
        )

    licences = as_list(ir.get("licences")) or as_list(ir.get("attribution")) or [
        {
            "source": "ARASAAC",
            "licence": "CC BY-NC-SA",
            "attribution": ARASAAC_ATTRIBUTION,
        }
    ]

    return {
        "schemaVersion": "0.1.0",
        "app": "Open AAC Studio",
        "id": activity_id,
        "name": title,
        "type": "interactive",
        "created": created,
        "modified": created,
        "settings": {
            "orientation": "landscape",
            "width": 1024,
            "height": 768,
            "speakLabels": True,
            "showLabels": True,
            "highlightColour": "#ffeb3b",
            "font": "Verdana",
            "fontSize": 18,
            "fontColour": "#000000",
            "backgroundColour": "#ffffff",
            "showStopButton": True,
            "dwellTimeMs": to_int(dwell_time, 1200),
            "switchScanning": bool(access.get("switchScanning", False)),
            "scanSpeedMs": to_int(access.get("scanSpeedMs"), 1400),
            "scanPattern": text(access.get("scanPattern")) or "linear",
        },
        "accessibility": {
            "intendedAccess": intended,
            "minimumTargetSizePx": to_int(
                access.get("minimumTargetSizePx") or accessibility.get("minimumTargetSizePx"),
                120 if dwell_profile else 96,
            ),
            "dwellSafe": dwell_profile or bool(accessibility.get("dwellSafe", False)),
            "scanOrder": text(access.get("scanOrder")) or text(accessibility.get("scanOrder")) or "dom-order",
            "audioCues": bool(access.get("audioCues", accessibility.get("audioCues", True))),
        },
        "pages": pages,
        "variables": as_dict(ir.get("variables")),
        "teacherNotes": as_dict(ir.get("teacherNotes")),
        "communicationFunctions": as_list(ir.get("communicationFunctions")),
        "metadata": {
            "tags": as_list(metadata.get("tags")) or ["aac", "agent-generated"],
            "level": text(metadata.get("level")),
            "curriculum": text(metadata.get("curriculum")),
            "privacyLevel": text(privacy.get("level")) or text(metadata.get("privacyLevel")) or "anonymous",
            "generatedFrom": "agentic-aac-board-ir",
            "sourceIrSchemaVersion": text(ir.get("schemaVersion")),
            "accessProfile": profile,
            "communicationFunctions": as_list(ir.get("communicationFunctions")),
            "ir": preserved_ir_metadata(ir, profile),
        },
        "licences": licences,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Agentic AAC Board IR to Open AAC Studio JSON.")
    parser.add_argument("ir_file", type=Path)
    parser.add_argument("output_file", type=Path)
    args = parser.parse_args()

    try:
        ir = json.loads(args.ir_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"FAIL: invalid IR JSON: {error}", file=sys.stderr)
        return 1

    if not isinstance(ir, dict):
        print("FAIL: IR JSON top-level value must be an object.", file=sys.stderr)
        return 1

    rendered = render(ir)
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(json.dumps(rendered, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

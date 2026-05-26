#!/usr/bin/env python3
"""Render canonical AAC Board IR to Open AAC Studio-compatible JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def slug(value: str, fallback: str) -> str:
    raw = text(value).lower() or fallback
    raw = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return raw or fallback


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def grid(page: dict[str, Any]) -> tuple[int, int]:
    grid_data = as_dict(page.get("grid"))
    rows = page.get("gridRows", grid_data.get("rows", 1))
    columns = page.get("gridColumns", grid_data.get("columns", 1))
    return max(1, int(rows)), max(1, int(columns))


def position(index: int, rows: int, columns: int) -> dict[str, float]:
    row = index // columns
    column = index % columns
    return {
        "x": round(column * (100 / columns), 4),
        "y": round(row * (100 / rows), 4),
        "width": round(100 / columns, 4),
        "height": round(100 / rows, 4),
    }


def action_list(button: dict[str, Any]) -> list[dict[str, Any]]:
    spoken = text(button.get("spokenText")) or text(button.get("speakText")) or text(button.get("audioCue")) or text(button.get("label"))
    result: list[dict[str, Any]] = []
    for action in as_list(button.get("actions")):
        if isinstance(action, dict):
            result.append(action)
        elif text(action) in {"next-page", "previous-page", "navigate-page", "mark-correct", "mark-incorrect"}:
            result.append({"id": f"act-{slug(text(button.get('id')), 'button')}-{text(action)}", "type": text(action)})
    if result:
        return result
    result = [
        {"id": f"act-{slug(text(button.get('id')), 'button')}-speak", "type": "speak-text", "text": spoken},
        {"id": f"act-{slug(text(button.get('id')), 'button')}-log", "type": "log-attempt"},
    ]
    return result


def render_button(button: dict[str, Any], index: int, rows: int, columns: int) -> dict[str, Any]:
    label = text(button.get("label")) or "Button"
    button_id = slug(text(button.get("id")) or label, f"btn-{index + 1}")
    spoken = text(button.get("spokenText")) or text(button.get("speakText")) or text(button.get("audioCue")) or label
    symbol_layout = text(button.get("symbolLayout")) or "label-bottom"
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
        "style": {
            "borderColour": "#17212b",
            "borderWidth": 3,
            "borderStyle": "solid",
            "shape": "rounded-rect",
            "fillColour": "#ffffff",
            "gradientColour": None,
            "gradientType": "none",
        },
        "font": {
            "family": "Verdana",
            "size": 18,
            "bold": True,
            "italic": False,
            "colour": "#000000",
            "align": "centre",
        },
        "state": text(button.get("state")) or "selectable",
        "audioCue": spoken,
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
    dwell_time = access.get("dwellTimeMs")
    if dwell_time is None:
        dwell_time = 1200 if profile in {"eye-gaze-dwell", "mouse-dwell"} else as_dict(ir.get("settings")).get("dwellTimeMs", 1200)

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
                "margin": int(page.get("margin", 10)),
                "backgroundColour": text(page.get("backgroundColour")) or "#ffffff",
                "backgroundImage": page.get("backgroundImage"),
                "buttons": buttons,
            }
        )

    licences = as_list(ir.get("licences")) or as_list(ir.get("attribution")) or [
        {
            "source": "ARASAAC",
            "licence": "CC BY-NC-SA",
            "attribution": "Pictograms by ARASAAC (Government of Aragon); confirm exact licence wording for publication.",
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
            "dwellTimeMs": int(dwell_time),
            "switchScanning": bool(access.get("switchScanning", False)),
            "scanSpeedMs": int(access.get("scanSpeedMs", 1400)),
            "scanPattern": text(access.get("scanPattern")) or "linear",
        },
        "accessibility": {
            "intendedAccess": intended,
            "minimumTargetSizePx": int(access.get("minimumTargetSizePx") or accessibility.get("minimumTargetSizePx") or 96),
            "dwellSafe": profile in {"eye-gaze-dwell", "mouse-dwell"} or bool(accessibility.get("dwellSafe", False)),
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

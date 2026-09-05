#!/usr/bin/env python3
"""Render canonical AAC Board IR to Open Board Format (.obf / .obz).

Open Board Format (https://www.openboardformat.org/, format string
"open-board-0.1") is the interoperability standard imported by CoughDrop,
Cboard, AsTeRICS Grid, OptiKey, PiCom, Pasco, and The Open Voice Factory.
Single-page boards render to a .obf JSON file; multi-page boards render to a
.obz zip (boards/<page>.obf files plus the required manifest.json).

Mapping notes:
- Button ids are always emitted as strings (the spec requires it; some apps
  emit numbers, but parsers are told to cast).
- label -> label; spokenText/speakText -> vocalization when it differs.
- style.fillColour/borderColour (hex) -> background_color/border_color rgb().
- next-page/previous-page/navigate-page actions -> load_board entries.
- speak-message -> ":speak", clear-message -> ":clear",
  remove-last-word -> ":backspace"; add-to-message is the OBF default
  behaviour (buttons append to the message window), so it needs no action.
- ARASAAC symbolId -> images[].url (static.arasaac.org) with a per-image
  CC BY-NC-SA license block naming the author Sergio Palao; symbolSrc
  data URIs -> images[].data. Embed real image data before offline use on
  school networks.
- Settings with no OBF equivalent travel as ext_aac_* extension attributes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

try:
    from canonicalize_board_ir import canonicalize
except ModuleNotFoundError:  # Supports importlib-based unit tests.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from canonicalize_board_ir import canonicalize

from output_layout import grid_slots

OBF_FORMAT = "open-board-0.1"

ARASAAC_LICENSE = {
    "type": "CC BY-NC-SA",
    "copyright_notice_url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "source_url": "https://arasaac.org",
    "author_name": "Sergio Palao / Government of Aragon (ARASAAC)",
    "author_url": "https://arasaac.org",
}

MESSAGE_ACTION_MAP = {
    "speak-message": ":speak",
    "clear-message": ":clear",
    "remove-last-word": ":backspace",
}

NAVIGATION_ACTIONS = {"navigate-page", "next-page", "previous-page"}


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


def hex_to_rgb(value: str) -> str:
    raw = text(value).lstrip("#")
    if re.fullmatch(r"[0-9a-fA-F]{3}", raw):
        raw = "".join(ch * 2 for ch in raw)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", raw):
        return ""
    red, green, blue = (int(raw[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgb({red}, {green}, {blue})"


def grid_size(page: dict[str, Any]) -> tuple[int, int]:
    grid_data = as_dict(page.get("grid"))
    rows = page.get("gridRows", grid_data.get("rows", 1))
    columns = page.get("gridColumns", grid_data.get("columns", 1))
    return max(1, to_int(rows, 1)), max(1, to_int(columns, 1))


def board_license(ir: dict[str, Any]) -> dict[str, Any]:
    for entry in as_list(ir.get("attribution")) or as_list(ir.get("licences")):
        entry = as_dict(entry)
        if "arasaac" in text(entry.get("source")).lower():
            return dict(ARASAAC_LICENSE)
        if entry.get("licence") or entry.get("license"):
            return {
                "type": text(entry.get("licence")) or text(entry.get("license")),
                "source_url": text(entry.get("url")),
                "author_name": text(entry.get("attribution")) or text(entry.get("source")),
            }
    return dict(ARASAAC_LICENSE)


def page_ids_in_order(ir: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for index, raw_page in enumerate(as_list(ir.get("pages")), start=1):
        page = as_dict(raw_page)
        ids.append(slug(text(page.get("id")) or text(page.get("name")), f"page-{index}"))
    return ids


def button_image(button: dict[str, Any], image_id: str) -> dict[str, Any] | None:
    symbol_src = text(button.get("symbolSrc"))
    if symbol_src.startswith("data:"):
        return {"id": image_id, "data": symbol_src, "content_type": symbol_src.split(";")[0].removeprefix("data:")}
    symbol_id = button.get("symbolId")
    if symbol_id is not None and re.fullmatch(r"\d+", str(symbol_id)):
        return {
            "id": image_id,
            "url": f"https://static.arasaac.org/pictograms/{symbol_id}/{symbol_id}_500.png",
            "content_type": "image/png",
            "license": dict(ARASAAC_LICENSE),
        }
    return None


def navigation_targets(button: dict[str, Any], page_order: list[str], page_index: int) -> str:
    """Resolve the target page id for a button's navigation action, if any."""
    for action in as_list(button.get("actions")):
        if isinstance(action, dict):
            action_type = text(action.get("type"))
            if action_type == "navigate-page":
                return text(action.get("targetPageId")) or text(action.get("pageId"))
            if action_type == "next-page" and page_index + 1 < len(page_order):
                return page_order[page_index + 1]
            if action_type == "previous-page" and page_index > 0:
                return page_order[page_index - 1]
        else:
            action_name = text(action)
            if action_name == "next-page" and page_index + 1 < len(page_order):
                return page_order[page_index + 1]
            if action_name == "previous-page" and page_index > 0:
                return page_order[page_index - 1]
    return ""


def render_board(ir: dict[str, Any], page: dict[str, Any], page_index: int, page_order: list[str], multi_page: bool) -> dict[str, Any]:
    rows, columns = grid_size(page)
    board_id = page_order[page_index]
    locale = text(as_dict(ir.get("audience")).get("locale")) or "en"

    buttons: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []
    order: list[list[str | None]] = [[None] * columns for _ in range(rows)]

    for index, (row, column, raw_button) in enumerate(grid_slots(page)):
        button = as_dict(raw_button)
        label = text(button.get("label")) or "Button"
        button_id = slug(text(button.get("id")) or label, f"btn-{index + 1}")
        spoken = text(button.get("spokenText")) or text(button.get("speakText")) or ""
        style = as_dict(button.get("style"))

        rendered: dict[str, Any] = {"id": button_id, "label": label}
        if spoken and spoken != label:
            rendered["vocalization"] = spoken
        background = hex_to_rgb(text(style.get("fillColour")))
        border = hex_to_rgb(text(style.get("borderColour")))
        if background:
            rendered["background_color"] = background
        if border:
            rendered["border_color"] = border

        target = navigation_targets(button, page_order, page_index)
        if target and multi_page:
            rendered["load_board"] = {"id": target, "path": f"boards/{target}.obf"}

        extra_actions: list[str] = []
        carried_actions: list[Any] = []
        for action in as_list(button.get("actions")):
            action_type = text(action.get("type")) if isinstance(action, dict) else text(action)
            if action_type in MESSAGE_ACTION_MAP:
                extra_actions.append(MESSAGE_ACTION_MAP[action_type])
            elif action_type in NAVIGATION_ACTIONS or action_type in {"speak-text", "speak-label", "add-to-message"}:
                continue  # navigation handled above; speech/add are OBF default behaviour
            elif action_type:
                carried_actions.append(action if isinstance(action, dict) else action_type)
        if extra_actions:
            rendered["action"] = extra_actions[0]
            if len(extra_actions) > 1:
                rendered["actions"] = extra_actions
        if carried_actions:
            rendered["ext_aac_actions"] = carried_actions

        role = text(button.get("role"))
        function = text(button.get("function"))
        if role:
            rendered["ext_aac_role"] = role
        if function:
            rendered["ext_aac_function"] = function

        image = button_image(button, f"img-{button_id}")
        if image:
            images.append(image)
            rendered["image_id"] = image["id"]

        buttons.append(rendered)
        if row < rows:
            order[row][column] = button_id

    access = as_dict(ir.get("access"))
    board: dict[str, Any] = {
        "format": OBF_FORMAT,
        "id": board_id,
        "locale": locale,
        "name": text(page.get("name")) or text(ir.get("title")) or text(ir.get("name")) or f"Page {page_index + 1}",
        "buttons": buttons,
        "grid": {"rows": rows, "columns": columns, "order": order},
        "images": images,
        "sounds": [],
        "license": board_license(ir),
        "ext_aac_source": {
            "generatedFrom": "agentic-aac-board-ir",
            "irId": text(ir.get("id")),
            "irSchemaVersion": text(ir.get("schemaVersion")),
        },
        "ext_aac_access": {
            "profile": text(access.get("profile")),
            "dwellTimeMs": access.get("dwellTimeMs"),
            "minimumTargetSizePx": access.get("minimumTargetSizePx"),
        },
    }
    description = text(ir.get("purpose"))
    if description and page_index == 0:
        board["description_html"] = description
    return board


def render_boards(ir: dict[str, Any]) -> list[dict[str, Any]]:
    ir = canonicalize(ir)
    pages = as_list(ir.get("pages"))
    page_order = page_ids_in_order(ir)
    multi_page = len(pages) > 1
    return [
        render_board(ir, as_dict(raw_page), index, page_order, multi_page)
        for index, raw_page in enumerate(pages)
    ]


def obz_manifest(boards: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "format": OBF_FORMAT,
        "root": f"boards/{boards[0]['id']}.obf",
        "paths": {
            "boards": {board["id"]: f"boards/{board['id']}.obf" for board in boards},
            "images": {},
            "sounds": {},
        },
    }


def zip_timestamp() -> tuple[int, int, int, int, int, int]:
    """Fixed zip entry timestamp; honours SOURCE_DATE_EPOCH for reproducibility."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch is not None:
        try:
            from datetime import datetime, timezone

            stamp = datetime.fromtimestamp(max(int(epoch), 315532800), timezone.utc)
            return (stamp.year, stamp.month, stamp.day, stamp.hour, stamp.minute, stamp.second)
        except (ValueError, OverflowError, OSError):
            pass
    return (2020, 1, 1, 0, 0, 0)


def write_obz(boards: list[dict[str, Any]], output: Path) -> None:
    stamp = zip_timestamp()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        entries = [("manifest.json", obz_manifest(boards))]
        entries += [(f"boards/{board['id']}.obf", board) for board in boards]
        for name, payload in entries:
            info = zipfile.ZipInfo(name, date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Agentic AAC Board IR to Open Board Format (.obf/.obz).")
    parser.add_argument("ir_file", type=Path)
    parser.add_argument("output_file", type=Path, help="Output path ending in .obf (single page) or .obz (any board)")
    args = parser.parse_args()

    try:
        ir = json.loads(args.ir_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"FAIL: invalid IR JSON: {error}", file=sys.stderr)
        return 1
    if not isinstance(ir, dict):
        print("FAIL: IR JSON top-level value must be an object.", file=sys.stderr)
        return 1

    boards = render_boards(ir)
    if not boards:
        print("FAIL: IR has no pages to render.", file=sys.stderr)
        return 1

    suffix = args.output_file.suffix.lower()
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    if suffix == ".obf":
        if len(boards) > 1:
            print("FAIL: multi-page boards must be rendered to .obz (zip with manifest).", file=sys.stderr)
            return 1
        args.output_file.write_text(json.dumps(boards[0], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    elif suffix == ".obz":
        write_obz(boards, args.output_file)
    else:
        print("FAIL: output file must end in .obf or .obz.", file=sys.stderr)
        return 1
    print(f"Wrote {args.output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

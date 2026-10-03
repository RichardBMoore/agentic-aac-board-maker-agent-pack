"""Shared house standards: layout addresses, word list, colour scheme and settings.

Used by apply_house_standards.py (to build boards), validate_board_ir.py (to
enforce them) and the renderers. Data lives in ../references/house-*.json so a
team can change one file and re-apply it to every board.
"""

from __future__ import annotations

import base64
import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
REFERENCES = SKILL_DIR / "references"
SYMBOL_DIR = SKILL_DIR / "assets" / "house-symbols"

NAVIGATION_ACTIONS = {"navigate-page", "next-page", "previous-page"}
HOUSE_STANDARDS_VERSION = "1.0.0"


@lru_cache(maxsize=None)
def load_layout() -> dict[str, Any]:
    return json.loads((REFERENCES / "house-layout.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def load_lexicon() -> dict[str, Any]:
    return json.loads((REFERENCES / "house-lexicon.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def load_settings() -> dict[str, Any]:
    return json.loads((REFERENCES / "house-settings.json").read_text(encoding="utf-8"))


def words() -> dict[str, dict[str, Any]]:
    return load_lexicon()["words"]


def normalise_label(value: str) -> str:
    """Compare labels without case, emoji, arrows or punctuation."""
    lowered = str(value or "").lower().replace("’", "'")
    lowered = re.sub(r"[^a-z0-9' ]+", " ", lowered)
    return " ".join(lowered.split())


@lru_cache(maxsize=None)
def _label_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for word_id, entry in words().items():
        for label in [entry["label"], *entry.get("aliases", [])]:
            key = normalise_label(label)
            if key:
                index.setdefault(key, word_id)
    return index


NON_WORD_CLASSES = {"letter", "ending"}


def lexicon_match(label: str, word_class: str | None = None) -> str | None:
    """Return the house word id whose label or alias matches this label (letters and endings never match)."""
    if word_class in NON_WORD_CLASSES:
        return None
    return _label_index().get(normalise_label(label))


def _position_index(keyword: str, size: int) -> int:
    if keyword == "first":
        return 1
    if keyword == "last":
        return size
    return math.ceil(size / 2)


def house_address(slot: str, rows: int, columns: int) -> tuple[int, int] | None:
    """1-based (row, column) address for a slot on a rows x columns grid, or None."""
    if rows < 2 or columns < 2:
        return None
    rule = load_layout()["slots"].get(slot)
    if rule is None:
        return None
    if slot == "different" and columns < 3:
        return None
    if slot in {"nav", "keyboard", "nav-back"} and rows < 3:
        return (1, columns) if slot == "nav" else (1, 1)
    return (_position_index(rule["row"], rows), _position_index(rule["column"], columns))


def reserved_addresses(rows: int, columns: int) -> dict[tuple[int, int], str]:
    result: dict[tuple[int, int], str] = {}
    for slot in load_layout()["slots"]:
        address = house_address(slot, rows, columns)
        if address is not None and address not in result:
            result[address] = slot
    return result


def action_types(button: dict[str, Any]) -> set[str]:
    return {
        str(action.get("type", "")) if isinstance(action, dict) else str(action)
        for action in button.get("actions", [])
    }


def slot_for_button(button: dict[str, Any]) -> str | None:
    """House slot a button must occupy, if any."""
    lexicon_id = button.get("lexiconId")
    if lexicon_id:
        entry = words().get(lexicon_id)
        return entry.get("slot") if entry else None
    kinds = action_types(button)
    if button.get("role") == "navigation" and kinds & NAVIGATION_ACTIONS:
        is_back = "previous-page" in kinds or str(button.get("label", "")).startswith("\u25c0")
        return "nav-back" if is_back else "nav"
    return None


def fill_for(word_class: str | None, scheme: str | None) -> str | None:
    if not word_class or not scheme or scheme == "none":
        return None
    schemes = load_settings()["colourSchemes"]
    return schemes.get(scheme, {}).get("fills", {}).get(word_class)


def cell_position(row: int, column: int, rows: int, columns: int) -> dict[str, float]:
    """Percentage position for a 1-based cell, matching output_layout.grid_slots."""
    return {
        "x": round((column - 1) * 100 / columns, 4),
        "y": round((row - 1) * 100 / rows, 4),
        "width": round(100 / columns, 4),
        "height": round(100 / rows, 4),
    }


def symbol_data_uri(symbol_id: int) -> str | None:
    path = SYMBOL_DIR / f"arasaac-{symbol_id}.png"
    if not path.exists():
        return None
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def ending_enabled_for(age_band: str) -> bool:
    band = str(age_band or "").lower()
    keys = load_settings()["literacy"]["wordEndings"]["enableForAgeBands"]
    return any(key in band for key in keys)

#!/usr/bin/env python3
"""Static checks for single-file eye-gaze HTML resources."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


class ElementCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag.lower(), {name.lower(): value or "" for name, value in attrs}))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def is_external(value: str) -> bool:
    if not value or value.startswith(("#", "data:", "blob:", "about:")):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} or value.startswith("//")


def class_list(attrs: dict[str, str]) -> set[str]:
    return set(attrs.get("class", "").split())


def find_css_block(css: str, selector: str) -> str:
    match = re.search(re.escape(selector) + r"\s*\{(?P<body>.*?)\}", css, re.DOTALL)
    return match.group("body") if match else ""


def resolve_px(css: str, block: str, property_name: str) -> int | None:
    match = re.search(property_name + r"\s*:\s*(?P<value>[^;]+);?", block)
    if not match:
        return None
    value = match.group("value").strip()
    direct = re.match(r"(?P<px>\d+)px$", value)
    if direct:
        return int(direct.group("px"))
    var_match = re.match(r"var\((?P<name>--[a-zA-Z0-9_-]+)\)$", value)
    if not var_match:
        return None
    variable = re.search(re.escape(var_match.group("name")) + r"\s*:\s*(?P<px>\d+)px", css)
    if not variable:
        return None
    return int(variable.group("px"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a single-file eye-gaze HTML tool.")
    parser.add_argument("html_file", type=Path)
    args = parser.parse_args()

    text = args.html_file.read_text(encoding="utf-8")
    collector = ElementCollector()
    collector.feed(text)

    failures: list[str] = []
    warnings: list[str] = []

    scripts_with_src = []
    links_with_href = []
    external_assets = []

    for tag, attrs in collector.elements:
        if tag == "script" and attrs.get("src"):
            scripts_with_src.append(attrs["src"])
        if tag == "link" and attrs.get("href"):
            links_with_href.append(attrs["href"])
        for attr in ("src", "href", "poster"):
            if is_external(attrs.get(attr, "")):
                external_assets.append(f"{tag}[{attr}]={attrs[attr]}")

    if scripts_with_src:
        failures.append("External script tags are not allowed in single-file gaze tools.")
    if links_with_href:
        failures.append("Link tags with href are risky for file:/// offline use; inline CSS instead.")
    if external_assets:
        failures.append("External assets found: " + ", ".join(external_assets[:5]))

    buttons = [(tag, attrs) for tag, attrs in collector.elements if tag == "button"]
    dwell_buttons = [(tag, attrs) for tag, attrs in buttons if "dwell-btn" in class_list(attrs)]
    if not buttons:
        failures.append("No button elements found.")
    if not dwell_buttons:
        warnings.append("No .dwell-btn buttons found.")

    missing_labels = [
        attrs.get("id") or attrs.get("class") or "(button)"
        for _, attrs in buttons
        if not attrs.get("aria-label") and not attrs.get("aria-labelledby")
    ]
    if missing_labels:
        failures.append(f"{len(missing_labels)} button(s) missing aria-label/aria-labelledby.")

    # Accept the canonical DwellManager class or any equivalent dwell controller
    # (a named class plus a timer-driven dwell start on pointer/mouse enter).
    has_dwell_controller = "class DwellManager" in text or (
        re.search(r"dwell", text, re.IGNORECASE)
        and "setTimeout" in text
        and ("pointerenter" in text or "mouseenter" in text)
    )
    if not has_dwell_controller:
        failures.append("No dwell controller found (DwellManager class or timer-based pointerenter dwell).")
    # Accept the conic-gradient ring or any visible animated dwell-progress indicator.
    has_dwell_progress = "conic-gradient" in text or re.search(
        r"dwell[-_]?progress[^}]*\}|@keyframes\s+dwell", text, re.IGNORECASE | re.DOTALL
    )
    if not has_dwell_progress:
        failures.append("No visible dwell progress indicator found (conic-gradient ring or animated dwell-progress fill).")
    if "pointerenter" not in text and "mouseenter" not in text:
        failures.append("No pointerenter or mouseenter dwell start handler found.")
    if "pointerleave" not in text and "mouseleave" not in text:
        failures.append("No pointerleave or mouseleave dwell cancellation handler found.")
    # Native buttons with click listeners are keyboard-operable (Enter/Space
    # fire click); a custom keydown Enter handler also satisfies this.
    has_click_activation = "addEventListener('click'" in text or 'addEventListener("click"' in text or "onclick" in text.lower()
    if not has_click_activation and ("keydown" not in text or "Enter" not in text):
        failures.append("No keyboard activation path found (click listener on native buttons or keydown Enter handler).")
    if "speechSynthesis" in text and "cancel()" not in text:
        warnings.append("Speech synthesis is used but no cancel/stop path was detected.")
    if "aria-live" not in text:
        warnings.append("No aria-live status region found.")
    if not re.search(r"@media\s*\(\s*forced-colors\s*:\s*active\s*\)", text):
        warnings.append("No Windows forced-colors support found.")

    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", text, flags=re.DOTALL | re.IGNORECASE))
    dwell_block = find_css_block(css, ".dwell-btn")
    if dwell_block:
        min_width = resolve_px(css, dwell_block, "min-width")
        min_height = resolve_px(css, dwell_block, "min-height")
        if min_width is not None and min_width < 120:
            failures.append(f".dwell-btn min-width is {min_width}px; use at least 120px.")
        if min_height is not None and min_height < 120:
            failures.append(f".dwell-btn min-height is {min_height}px; use at least 120px.")
        if min_width is None or min_height is None:
            warnings.append("Could not statically confirm .dwell-btn min-width and min-height.")
    else:
        warnings.append("Could not find a .dwell-btn CSS rule.")

    for message in warnings:
        print(f"WARN: {message}")
    for message in failures:
        print(f"FAIL: {message}")

    if failures:
        return 1
    print(f"PASS: {args.html_file} looks suitable for offline dwell-gaze review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

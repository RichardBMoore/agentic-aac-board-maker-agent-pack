#!/usr/bin/env python3
"""Static display-fit checks for single-file HTML on PRC-Saltillo Accent / EQ-managed Edge.

Checks that a file authored for a laptop will survive the real device viewport:
Windows display scaling, NuVoice Key Mode, the Empower browser and old Edge engines.

Usage:
  check_accent_display.py board.html
  check_accent_display.py board.html --profile keymode
  check_accent_display.py board.html --floor 1280x610 --chrome 120
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

PROFILES = {
    "mustfit": (1264, 600),   # maximised Edge on Accent 1400-30 at 150% scaling
    "fullscreen150": (1280, 720),
    "original1400": (1280, 800),
    "grace": (1024, 460),     # published minimum-width grace contract
    "keymode": (1180, 460),   # NuVoice Key Mode half-screen (grace floor)
    "empower": (1280, 600),   # Empower Accessible Web Browser
}

BANNED_CSS = [":has(", "@container", "subgrid"]
DEFAULT_GAP = 12
MIN_TARGET = 120
CHROME_PLAIN = 96
CHROME_MESSAGE_BAR = 166


class ElementCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag.lower(), {name.lower(): value or "" for name, value in attrs}))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def is_external(value: str) -> bool:
    if not value or value.startswith(("#", "data:", "blob:", "about:", "mailto:", "tel:", "javascript:")):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} or value.startswith("//")


def first_int(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text)
    return int(match.group(1)) if match else None


def grid_dimensions(text: str) -> list[tuple[int, int]]:
    """Collect (rows, columns) pairs from inline style/CSS variable declarations."""
    pairs: list[tuple[int, int]] = []
    for match in re.finditer(r"grid-rows\s*:\s*(\d+)\s*;?\s*(?:--)?grid-columns\s*:\s*(\d+)", text):
        pairs.append((int(match.group(1)), int(match.group(2))))
    for match in re.finditer(r"grid-columns\s*:\s*(\d+)\s*;?\s*(?:--)?grid-rows\s*:\s*(\d+)", text):
        pair = (int(match.group(2)), int(match.group(1)))
        if pair not in pairs:
            pairs.append(pair)
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a single-file HTML activity fits real Accent/EQ viewports.")
    parser.add_argument("html_file", type=Path)
    parser.add_argument("--profile", choices=sorted(PROFILES), default="mustfit",
                        help="named effective-viewport floor (default: mustfit 1264x600)")
    parser.add_argument("--floor", help="explicit WxH floor in CSS px, e.g. 1264x600 (overrides --profile)")
    parser.add_argument("--chrome", type=int, default=None,
                        help="page chrome height in px reserved above/around the grid (default: 96, or 166 with a message bar)")
    args = parser.parse_args()

    if args.floor:
        try:
            floor_w, floor_h = (int(part) for part in args.floor.lower().split("x"))
        except ValueError:
            print(f"FAIL: --floor must look like 1264x600, got {args.floor!r}")
            return 1
    else:
        floor_w, floor_h = PROFILES[args.profile]

    text = args.html_file.read_text(encoding="utf-8")
    collector = ElementCollector()
    collector.feed(text)

    failures: list[str] = []
    warnings: list[str] = []
    passes: list[str] = []

    # --- Document basics ---------------------------------------------------
    has_viewport = any(
        tag == "meta" and attrs.get("name", "").lower() == "viewport" and "width=device-width" in attrs.get("content", "")
        for tag, attrs in collector.elements
    )
    if has_viewport:
        passes.append("viewport meta with width=device-width present")
    else:
        failures.append('missing <meta name="viewport" content="width=device-width,initial-scale=1"> — scaled devices will misrender')

    has_charset = any(
        tag == "meta" and ("charset" in attrs or "utf-8" in attrs.get("content", "").lower())
        for tag, attrs in collector.elements
    )
    if has_charset:
        passes.append("charset declared")
    else:
        failures.append('missing <meta charset="utf-8">')

    lang = next((attrs.get("lang", "") for tag, attrs in collector.elements if tag == "html"), "")
    if lang.lower() == "en-au":
        passes.append('lang="en-AU"')
    else:
        warnings.append(f'html lang is {lang!r}; pack default is "en-AU"')

    # --- Self-contained ----------------------------------------------------
    externals: list[str] = []
    for tag, attrs in collector.elements:
        for attr in ("src", "href", "poster"):
            value = attrs.get(attr, "")
            if tag == "a" and attr == "href":
                continue
            if is_external(value):
                externals.append(f"<{tag} {attr}={value[:60]}>")
    externals.extend(f"css url({match[:60]})" for match in re.findall(r"url\(\s*['\"]?(https?://[^)'\"]+)", text))
    if externals:
        failures.append("external references (EQ filtering/offline devices will break them): " + "; ".join(externals[:5]))
    else:
        passes.append("no external network references")

    # --- Engine baseline ---------------------------------------------------
    for feature in BANNED_CSS:
        if feature in text:
            if "@supports" in text:
                warnings.append(f"{feature} present — confirm it is inside an @supports guard and non-load-bearing (old Accent Edge engines lack it)")
            else:
                failures.append(f"{feature} used without any @supports guard — layout will silently break on older Accent Edge engines")

    if re.search(r"\d+\s*dvh", text):
        if re.search(r"\d+\s*vh", text.replace("dvh", "")):
            passes.append("dvh paired with vh fallback")
        else:
            failures.append("dvh units used without a plain vh fallback line — blank sizing on older engines")

    if "100vw" in text:
        warnings.append("100vw used — includes scrollbar width on Windows and can cause horizontal overflow; prefer width:100%")

    if 'type="module"' in text or "type='module'" in text:
        warnings.append("module scripts — silently ignored by pre-2020 engines; use a classic script for the critical path")

    modern_js = len(re.findall(r"\?\.|\?\?", text))
    if modern_js:
        warnings.append(f"optional chaining/nullish operators found ({modern_js}) — fine on current Edge, a syntax error killing the whole script on very old engines; keep them out of the layout-critical path")

    if "<noscript" in text.lower():
        passes.append("noscript fallback present")
    else:
        warnings.append("no <noscript> fallback — a JS failure leaves a silent dead page; add a visible 'tell your teacher' line")

    # --- Fixed-size hazards -------------------------------------------------
    for match in re.finditer(r"(?<!max-)(?:min-)?width\s*:\s*(\d{4,})px", text):
        value = int(match.group(1))
        if value > floor_w:
            failures.append(f"fixed width {value}px exceeds the {floor_w}px floor — will overflow on the device (max-width caps are fine)")
    for match in re.finditer(r"(?<!max-)(?:min-)?height\s*:\s*(\d{3,})px", text):
        value = int(match.group(1))
        if value > floor_h:
            warnings.append(f"fixed height {value}px exceeds the {floor_h}px floor — check it can compress or paginate (max-height caps are fine)")

    # --- Fit maths ----------------------------------------------------------
    target = None
    body_attrs = next((attrs for tag, attrs in collector.elements if tag == "body"), {})
    if body_attrs.get("data-min-target"):
        try:
            target = int(body_attrs["data-min-target"])
        except ValueError:
            failures.append("data-min-target must be an integer number of CSS pixels")
    if target is None:
        target = first_int(r"--min-target\s*:\s*(\d+)px", text)
    if target is not None and target < MIN_TARGET:
        failures.append(
            f"declared minimum target is {target}px; Accent eye-gaze targets must be at least {MIN_TARGET}px"
        )
    gap = first_int(r"\.board-grid[^}]*?gap\s*:\s*(\d+)px", text) or first_int(r"--gap\s*:\s*(\d+)px", text) or DEFAULT_GAP
    chrome = args.chrome
    if chrome is None:
        chrome = CHROME_MESSAGE_BAR if "message-bar" in text else CHROME_PLAIN

    grids = grid_dimensions(text)
    if target and grids:
        worst: tuple[int, int, int, int] | None = None
        fit_failed = False
        for rows, cols in grids:
            needed_w = cols * target + (cols - 1) * gap + 24
            needed_h = rows * target + (rows - 1) * gap + chrome
            if worst is None or needed_h > worst[3] or needed_w > worst[2]:
                worst = (rows, cols, needed_w, needed_h)
            if needed_w > floor_w or needed_h > floor_h:
                fit_failed = True
                max_rows = max(1, (floor_h - chrome + gap) // (target + gap))
                max_cols = max(1, (floor_w - 24 + gap) // (target + gap))
                failures.append(
                    f"{rows}x{cols} grid at {target}px targets needs ~{needed_w}x{needed_h}px but the floor is "
                    f"{floor_w}x{floor_h} ({args.profile if not args.floor else 'custom'}) — use at most "
                    f"{max_rows} rows x {max_cols} columns per page, paginate, or reduce targets toward 120px (never below)"
                )
        if not fit_failed and worst:
            passes.append(
                f"fit maths OK: worst page {worst[0]}x{worst[1]} grid needs ~{worst[2]}x{worst[3]}px within {floor_w}x{floor_h} floor"
            )
    elif target and not grids:
        warnings.append("min-target found but no grid-rows/grid-columns declarations — fit maths skipped; verify layout manually at the floor viewport")
    else:
        warnings.append("no --min-target/data-min-target found — fit maths skipped; verify all targets are >=120px and the page fits the floor viewport")

    if re.search(r"minmax\(\s*var\(--min-target\)", text) and grids and target:
        passes.append("template minmax(var(--min-target),1fr) grid detected — fit maths above guarantees it cannot force overflow")

    # --- Report -------------------------------------------------------------
    print(f"Accent display check: {args.html_file.name} against {floor_w}x{floor_h} floor")
    for line in passes:
        print(f"  OK   {line}")
    for line in warnings:
        print(f"  WARN {line}")
    for line in failures:
        print(f"  FAIL {line}")
    print(f"Summary: {len(passes)} ok, {len(warnings)} warnings, {len(failures)} failures")
    if failures:
        print("Result: FAIL — fix the failures before handing this file to a student device.")
        return 1
    print("Result: PASS (static checks only — run browser tests and the on-device smoke test).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

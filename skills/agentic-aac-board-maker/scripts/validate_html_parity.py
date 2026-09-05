#!/usr/bin/env python3
"""Verify that rendered HTML, embedded IR and the shared runtime match source IR."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

try:
    from canonicalize_board_ir import canonicalize
except ModuleNotFoundError:  # Supports importlib-based unit tests.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from canonicalize_board_ir import canonicalize


from output_layout import grid_slots
from render_html import render

SCRIPT_DIR = Path(__file__).resolve().parent
RUNTIME_PATH = SCRIPT_DIR.parent / "assets" / "aac-board-runtime.js"


class BoardCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pages: list[str] = []
        self.presentation = []
        self.visible_labels = []
        self._in_label = False
        self.buttons: list[dict[str, str]] = []
        self.html_attrs: dict[str, str] = {}
        self.body_attrs: dict[str, str] = {}
        self._ir_depth = 0
        self._runtime_depth = 0
        self.ir_parts: list[str] = []
        self.runtime_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "span" and "label" in values.get("class", "").split():
            self._in_label = True
        if values.get("data-button-id"):
            self.presentation.append(("button", {key: values.get(key, "") for key in ("style", "data-symbol-layout", "aria-label")}))
        if tag == "img":
            self.presentation.append(("image", values))
        if tag == "html": self.html_attrs = values
        if tag == "body": self.body_attrs = values
        if values.get("data-page-id"): self.pages.append(values["data-page-id"])
        if values.get("data-button-id"):
            self.buttons.append({key: values.get(key, "") for key in ("data-button-id", "data-label", "data-spoken", "data-actions")})
        if tag == "script" and values.get("id") == "aac-board-ir": self._ir_depth = 1
        if tag == "script" and "data-aac-shared-runtime" in values: self._runtime_depth = 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "span": self._in_label = False
        if tag == "script":
            self._ir_depth = 0
            self._runtime_depth = 0

    def handle_data(self, data: str) -> None:
        if self._in_label: self.visible_labels.append(data)
        if self._ir_depth: self.ir_parts.append(data)
        if self._runtime_depth: self.runtime_parts.append(data)


def validate(source: dict[str, Any], html_text: str, runtime_source: str | None = None) -> list[str]:
    failures: list[str] = []
    canonical = canonicalize(source)
    try:
        expected_html = render(canonical, runtime_source=runtime_source)
    except (ValueError, TypeError) as error:
        return [f"HTML capability/layout error: {error}"]
    expected_collector = BoardCollector()
    expected_collector.feed(expected_html)
    collector = BoardCollector()
    collector.feed(html_text)
    if collector.presentation != expected_collector.presentation or collector.visible_labels != expected_collector.visible_labels:
        failures.append("HTML positions, styling, labels or symbol images differ from rendered IR")
    try:
        embedded = json.loads("".join(collector.ir_parts))
    except json.JSONDecodeError as error:
        return [f"embedded IR is missing or invalid: {error}"]
    if embedded != canonical:
        failures.append("embedded IR does not equal canonical source IR")
    expected_pages = [page["id"] for page in canonical["pages"]]
    if collector.pages != expected_pages:
        failures.append(f"HTML page order differs: expected {expected_pages}, got {collector.pages}")
    expected_buttons = [
        {"data-button-id": button["id"], "data-label": button["label"], "data-spoken": button["spokenText"], "data-actions": json.dumps(button["actions"], ensure_ascii=False, separators=(",", ":"))}
        for page in canonical["pages"] for _, _, button in grid_slots(page)
    ]
    actual_buttons = [
        {**button, "data-actions": html.unescape(button["data-actions"])} for button in collector.buttons
    ]
    if actual_buttons != expected_buttons:
        failures.append("HTML button ids, order, labels, spoken text or actions differ from canonical IR")
    dwell_enabled = canonical["access"]["profile"] in {"eye-gaze-dwell", "mouse-dwell"} or bool(
        {"eye-gaze-dwell", "mouse-dwell"} & set(canonical["access"]["intended"])
    )
    for field, expected in (
        ("data-access-profile", canonical["access"]["profile"]),
        ("data-dwell-enabled", str(dwell_enabled).lower()),
        ("data-min-target", str(canonical["access"]["minimumTargetSizePx"])),
        ("data-visible-target-limit", str(canonical["access"]["visibleTargetLimit"])),
        ("data-setup-target-limit", str(canonical["access"]["setupTargetLimit"])),
    ):
        if collector.body_attrs.get(field) != expected:
            failures.append(f"HTML {field} differs from canonical IR")
    runtime = runtime_source if runtime_source is not None else RUNTIME_PATH.read_text(encoding="utf-8")
    expected_hash = hashlib.sha256(runtime.encode("utf-8")).hexdigest()
    if collector.html_attrs.get("data-runtime-sha256") != expected_hash:
        failures.append("HTML runtime hash does not match the shared runtime")
    if "".join(collector.runtime_parts) != runtime:
        failures.append("embedded dwell runtime differs from the shared runtime")
    if len(re.findall(r"class=\"message-bar\"", html_text)) != int(bool(canonical.get("messageBar", {}).get("enabled"))):
        failures.append("HTML message bar presence differs from canonical IR")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ir_file", type=Path)
    parser.add_argument("html_file", type=Path)
    args = parser.parse_args(argv)
    try:
        source = json.loads(args.ir_file.read_text(encoding="utf-8"))
        html_text = args.html_file.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot read inputs: {error}")
        return 1
    failures = validate(source, html_text)
    for failure in failures: print(f"FAIL: {failure}")
    if failures: return 1
    print(f"PASS: {args.html_file} is in parity with {args.ir_file} and the shared runtime.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

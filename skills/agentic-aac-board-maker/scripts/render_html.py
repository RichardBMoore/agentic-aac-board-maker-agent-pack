#!/usr/bin/env python3
"""Render canonical AAC Board IR to deterministic, offline, single-file HTML."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from canonicalize_board_ir import canonicalize
except ModuleNotFoundError:  # Supports importlib-based unit tests.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from canonicalize_board_ir import canonicalize


from output_layout import grid_slots

SCRIPT_DIR = Path(__file__).resolve().parent
RUNTIME_PATH = SCRIPT_DIR.parent / "assets" / "aac-board-runtime.js"


def attr(value: Any) -> str:
    return html.escape(str(value), quote=True)


def json_attr(value: Any) -> str:
    return attr(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


def embedded_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False).replace("<", "\\u003c")


def css_colour(value: Any, fallback: str) -> str:
    candidate = str(value or "").strip()
    return candidate if re.fullmatch(r"#[0-9a-fA-F]{6}", candidate) else fallback


def control(control_id: str, label: str, classes: str = "", dwell_enabled: bool = True) -> str:
    class_name = f"dwell-btn setup-control {classes}".strip()
    dwell_attr = " data-dwell" if dwell_enabled else ""
    return (
        f'<button id="{attr(control_id)}" class="{attr(class_name)}" type="button" '
        f'data-control="{attr(control_id)}" data-student-target{dwell_attr} aria-label="{attr(label)}">'
        f'<span class="label">{html.escape(label)}</span><span class="dwell-progress" aria-hidden="true"></span></button>'
    )


def render_button(button: dict[str, Any], dwell_enabled: bool, row: int = 0, column: int = 0, scan_number: int = 1) -> str:
    symbol = ""
    source = str(button.get("symbolSrc") or "")
    if source.startswith("data:image/"):
        symbol = f'<img class="symbol" src="{attr(source)}" alt="" aria-hidden="true">'
    style = button.get("style", {})
    font = button.get("font", {})
    presentation = [f"grid-row:{row + 1}", f"grid-column:{column + 1}"]
    for key, css_key in (("fillColour", "background-color"), ("borderColour", "border-color")):
        if key in style:
            presentation.append(f"{css_key}:{css_colour(style[key], '#ffffff' if key == 'fillColour' else '#17212b')}")
    if "colour" in font:
        presentation.append(f"color:{css_colour(font['colour'], '#17212b')}")
    if "size" in font:
        presentation.append(f"font-size:{max(12, min(96, float(font['size'])))}px")
    if font.get("family") in {"Verdana", "Arial", "Tahoma", "sans-serif", "serif"}:
        presentation.append(f"font-family:{font['family']}")
    if "bold" in font:
        presentation.append(f"font-weight:{700 if font['bold'] else 400}")
    layout = button.get("symbolLayout", "label-bottom")
    if layout not in {"label-bottom", "label-top", "label-left", "label-right"}:
        raise ValueError(f"{button['id']}: unsupported HTML symbolLayout {layout}")
    dwell_attr = " data-dwell" if dwell_enabled else ""
    return (
        f'<button style="{attr(";".join(presentation))}" data-symbol-layout="{attr(layout)}" id="{attr(button["id"])}" class="dwell-btn board-button role-{attr(button["role"])}" type="button" '
        f'data-button-id="{attr(button["id"])}" data-label="{attr(button["label"])}" '
        f'data-spoken="{attr(button["spokenText"])}" data-actions="{json_attr(button["actions"])}" '
        f'data-student-target{dwell_attr} aria-label="{attr(button["label"])}">{symbol}'
        f'<span class="scan-number" aria-hidden="true">{scan_number}. </span><span class="label">{html.escape(button["label"])}</span><span class="dwell-progress" aria-hidden="true"></span></button>'
    )


def render_page(page: dict[str, Any], first: bool, dwell_enabled: bool, title: str, attribution: str) -> str:
    hidden = "" if first else " hidden"
    buttons = "\n".join(render_button(button, dwell_enabled, row, column, index + 1) for index, (row, column, button) in enumerate(grid_slots(page)))
    return (
        f'<section class="board-page" data-page-id="{attr(page["id"])}" aria-label="{attr(page["name"])}"{hidden}>'
        f'<h2 class="page-title">{html.escape(title if page["name"].lower() == "main" else page["name"])}</h2>'
        f'<div class="board-grid" style="--grid-rows:{page["grid"]["rows"]};--grid-columns:{page["grid"]["columns"]}">'
        f'{buttons}</div><p class="print-attribution">{html.escape(attribution)}</p></section>'
    )


def render(ir_input: dict[str, Any], runtime_source: str | None = None, paper: str = "A4", orientation: str = "landscape") -> str:
    ir = canonicalize(ir_input)
    if paper not in {"A4", "A3"} or orientation not in {"portrait", "landscape"}:
        raise ValueError("Print format must be A4/A3 portrait/landscape")
    if ir['access']['switchScanning'] or ir['access']['profile'] in {'single-switch', 'two-switch'} or {'single-switch', 'two-switch'} & set(ir['access']['intended']):
        raise ValueError("Standalone HTML does not implement switch scanning. Use an explicitly configured scanning player or a partner-assisted print board.")
    dwell_enabled = ir["access"]["profile"] in {"eye-gaze-dwell", "mouse-dwell"} or bool(
        {"eye-gaze-dwell", "mouse-dwell"} & set(ir["access"]["intended"])
    )
    runtime = runtime_source if runtime_source is not None else RUNTIME_PATH.read_text(encoding="utf-8")
    runtime_hash = hashlib.sha256(runtime.encode("utf-8")).hexdigest()
    controls = ir["studentControls"]
    setup_controls: list[str] = []
    if controls["startBoard"]:
        setup_controls.append(control("start", "Start board", "primary", dwell_enabled))
    if controls["fullScreen"]:
        setup_controls.append(control("full-screen", "Full screen", dwell_enabled=dwell_enabled))
    if controls["soundCheck"]:
        setup_controls.append(control("sound-check", "Sound check", dwell_enabled=dwell_enabled))
    setup_hidden = "" if controls["startBoard"] else " hidden"
    student_hidden = " hidden" if controls["startBoard"] else ""
    attribution = "; ".join(f'{entry["source"]}: {entry["licence"]}. {entry.get("attribution", "")} {entry.get("url", "")}' for entry in ir["attribution"])
    page_height_mm = {("A4", "landscape"): 210, ("A4", "portrait"): 297, ("A3", "landscape"): 297, ("A3", "portrait"): 420}[(paper, orientation)]
    pages = "\n".join(render_page(page, index == 0, dwell_enabled, ir["title"], attribution) for index, page in enumerate(ir["pages"]))
    message_bar = ""
    if ir.get("messageBar", {}).get("enabled"):
        placeholder = ir["messageBar"]["placeholder"]
        message_bar = (
            '<section class="message-bar" aria-label="Message bar">'
            f'<div id="message-text" class="message-text is-placeholder" role="status" aria-live="polite" data-placeholder="{attr(placeholder)}">'
            f'{html.escape(placeholder)}</div></section>'
        )
    notes = ir["teacherNotes"]
    attribution = "; ".join(f'{entry["source"]}: {entry["licence"]}. {entry.get("attribution", "")} {entry.get("url", "")}' for entry in ir["attribution"])
    background = css_colour(ir["display"].get("backgroundColour"), "#f7fbff")
    css = f"""
:root {{ --min-target: {ir['access']['minimumTargetSizePx']}px; --dwell-ms: {ir['access']['dwellTimeMs'] or 1200}ms; --ink:#17212b; --focus:#005fcc; --repair:#ffe3e3; }}
* {{ box-sizing:border-box; }}
html, body {{ margin:0; min-height:100%; font-family:Verdana,Arial,sans-serif; color:var(--ink); background:{attr(background)}; }}
body {{ min-height:100vh; }}
button {{ font:inherit; color:inherit; }}
[hidden] {{ display:none !important; }}
.skip-link {{ position:absolute; left:-9999px; }} .skip-link:focus {{ left:8px; top:8px; z-index:20; background:white; padding:8px; }}
.setup-screen, .speech-layer {{ min-height:100vh; display:grid; place-content:center; gap:20px; padding:24px; text-align:center; }}
.setup-controls {{ display:flex; flex-wrap:wrap; justify-content:center; gap:24px; }}
.student-layer {{ min-height:100vh; padding:12px; }}
.page-title {{ margin:0 0 8px; text-align:center; font-size:clamp(1.1rem,2.4vw,1.8rem); }}
.board-grid {{ min-height:calc(100vh - 154px); display:grid; grid-template-columns:repeat(var(--grid-columns), minmax(var(--min-target),1fr)); grid-template-rows:repeat(var(--grid-rows), minmax(var(--min-target),1fr)); gap:12px; }}
.message-bar + .board-page .board-grid, .message-bar ~ .board-page .board-grid {{ min-height:calc(100vh - 218px); }}
.message-bar {{ margin:0 auto 10px; max-width:1200px; min-height:60px; padding:10px 16px; border:3px solid var(--ink); border-radius:14px; background:white; font-size:clamp(1rem,2.2vw,1.5rem); }}
.is-placeholder {{ color:#58636e; }}
.dwell-btn {{ position:relative; overflow:hidden; min-width:var(--min-target); min-height:var(--min-target); border:4px solid var(--ink); border-radius:18px; background:#fff; padding:12px; font-size:clamp(1rem,2.5vw,1.6rem); font-weight:700; cursor:pointer; touch-action:manipulation; }}
.dwell-btn:focus-visible {{ outline:6px solid var(--focus); outline-offset:3px; }}
.role-repair {{ background:var(--repair); }} .role-navigation {{ background:#e8eef4; }}
.dwell-progress {{ position:absolute; inset:auto 0 0; height:10px; background:#ffbf00; transform:scaleX(0); transform-origin:left; }}
.is-dwelling .dwell-progress {{ animation:dwell-fill var(--dwell-ms) linear forwards; }}
.was-activated {{ filter:brightness(.82); }}
.board-button {{ display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; }}
.board-button[data-symbol-layout="label-top"] .label {{ order:-1; }}
.board-button[data-symbol-layout="label-left"] {{ flex-direction:row-reverse; }}
.board-button[data-symbol-layout="label-right"] {{ flex-direction:row; }}
.symbol {{ display:block; width:auto; max-width:65%; height:clamp(48px,14vh,180px); object-fit:contain; }}
.selected-message {{ min-height:48px; margin:0 0 10px; padding:8px; text-align:center; font-size:1.2rem; }}
.scan-number,.print-attribution {{ display:none; }}
.speech-layer {{ position:fixed; inset:0; z-index:10; background:{attr(background)}; }}
.speech-active #student-layer, .speech-active #setup-screen {{ visibility:hidden; }}
.stop-control {{ min-width:min(70vw,420px); min-height:min(55vh,320px); background:#ffe3e3; font-size:clamp(1.4rem,4vw,2.4rem); }}
.board-status {{ position:fixed; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); }}
.teacher-panel {{ display:none; margin:18px; padding:18px; border:2px solid #555; background:white; }}
body.teacher-mode .teacher-panel {{ display:block; }}
.attribution {{ font-size:.75rem; }}
@keyframes dwell-fill {{ to {{ transform:scaleX(1); }} }}
@media (max-width:760px) {{ .board-grid {{ gap:7px; }} .dwell-btn {{ padding:7px; }} }}
@media (forced-colors:active) {{ .dwell-btn {{ border-color:ButtonText; forced-color-adjust:auto; }} .dwell-progress {{ background:Highlight; }} }}
@page {{ size:{paper} {orientation}; margin:12mm; }}
@media print {{ .selected-message,.message-bar,.setup-screen,.speech-layer,.board-status {{ display:none !important; }} .student-layer,.teacher-panel {{ display:block !important; }} .board-page {{ break-after:page; break-inside:avoid; }} .teacher-panel {{ break-before:page; }} .scan-number {{ display:inline; position:absolute; top:5px; left:8px; font-size:12pt; }} .dwell-progress {{ display:none; }} .board-page[hidden] {{ display:block !important; }} .board-grid {{ min-height:0; height:{page_height_mm - 54}mm; }} .print-attribution {{ display:block; margin:6px 0 0; font-size:8pt; }} .dwell-btn {{ min-width:0; min-height:30mm; font-size:16pt; }} .symbol {{ height:20mm; }} .student-layer {{ min-height:0; padding:0; }} }}
"""
    return f"""<!doctype html>
<html lang="{attr(ir['audience']['locale'])}" data-runtime-sha256="{runtime_hash}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{html.escape(ir['title'])}</title><style>{css}</style></head>
<body data-access-profile="{attr(ir['access']['profile'])}" data-dwell-enabled="{str(dwell_enabled).lower()}" data-min-target="{ir['access']['minimumTargetSizePx']}" data-visible-target-limit="{ir['access']['visibleTargetLimit']}" data-setup-target-limit="{ir['access']['setupTargetLimit']}">
<a class="skip-link" href="#student-layer">Skip to board</a>
<section id="setup-screen" class="setup-screen" aria-label="Board setup"{setup_hidden}><h1>{html.escape(ir['title'])}</h1><p>Choose Start board when positioning and access are ready.</p><div class="setup-controls">{''.join(setup_controls)}</div></section>
<main id="student-layer" class="student-layer"{student_hidden}>{message_bar}<p id="selected-message" class="selected-message" aria-live="polite">Choose a message.</p>{pages}</main>
<section id="speech-layer" class="speech-layer" aria-label="Speech controls" hidden><button id="stop-speech" class="dwell-btn stop-control" type="button" data-control="stop-speech" data-student-target{' data-dwell' if dwell_enabled else ''} aria-label="Stop speech"><span class="label">Stop speech</span><span class="dwell-progress" aria-hidden="true"></span></button></section>
<div id="board-status" class="board-status" role="status" aria-live="polite">Board ready.</div>
<aside class="teacher-panel"><h2>Teacher notes</h2><p><strong>Model:</strong> {html.escape(notes['modeling'])}</p><p><strong>Evidence:</strong> {html.escape(notes['evidence'])}</p><p><strong>Customise:</strong> {html.escape(notes['customisation'])}</p><p class="attribution">{html.escape(attribution)}. Text fallback remains available. ARASAAC pictograms, when embedded, require their stated attribution.</p></aside>
<script id="aac-board-ir" type="application/json">{embedded_json(ir)}</script>
<script>if(new URLSearchParams(location.search).get("teacher")==="1")document.body.classList.add("teacher-mode");</script>
<!-- shared-runtime-sha256:{runtime_hash} -->
<script data-aac-shared-runtime>{runtime}</script>
</body></html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ir_file", type=Path)
    parser.add_argument("output_file", type=Path)
    parser.add_argument("--paper", choices=("A4", "A3"), default="A4")
    parser.add_argument("--orientation", choices=("portrait", "landscape"), default="landscape")
    args = parser.parse_args(argv)
    try:
        raw = json.loads(args.ir_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot read IR: {error}", file=sys.stderr)
        return 1
    if not isinstance(raw, dict):
        print("FAIL: IR top-level value must be an object.", file=sys.stderr)
        return 1
    try:
        output = render(raw, paper=args.paper, orientation=args.orientation)
    except (ValueError, TypeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(output, encoding="utf-8")
    print(f"Wrote {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
from render_partner_card import card_fragment

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


SYMBOL_PREFIX = "sym:"


def symbol_table(ir: dict[str, Any]) -> dict[str, str]:
    """Each distinct embedded image once, keyed in first-use order (keeps single-file boards small)."""
    table: dict[str, str] = {}
    for page in ir["pages"]:
        for button in page["buttons"]:
            source = str(button.get("symbolSrc") or "")
            if source.startswith("data:image/") and source not in table:
                table[source] = f"s{len(table) + 1}"
    return table


def compact_ir(ir: dict[str, Any], table: dict[str, str]) -> dict[str, Any]:
    """Embedded IR refers to the shared symbol definitions instead of repeating image data."""
    compact = json.loads(json.dumps(ir))
    for page in compact["pages"]:
        for button in page["buttons"]:
            source = str(button.get("symbolSrc") or "")
            if source in table:
                button["symbolSrc"] = SYMBOL_PREFIX + table[source]
    return compact


def symbol_defs(table: dict[str, str]) -> str:
    if not table:
        return ""
    symbols = "".join(
        f'<symbol id="sym-{key}" viewBox="0 0 300 300"><image href="{attr(source)}" width="300" height="300" preserveAspectRatio="xMidYMid meet"/></symbol>'
        for source, key in table.items()
    )
    return f'<svg class="symbol-defs" width="0" height="0" aria-hidden="true" focusable="false"><defs>{symbols}</defs></svg>'


def render_button(button: dict[str, Any], dwell_enabled: bool, row: int = 0, column: int = 0, scan_number: int = 1, schedule_step: bool = False, symbols: dict[str, str] | None = None) -> str:
    placement = f"grid-row:{row + 1};grid-column:{column + 1}"
    if button.get("hidden"):
        # Masked vocabulary keeps its address so nothing moves when it is revealed later.
        return f'<div class="masked-cell" style="{attr(placement)}" data-masked-id="{attr(button["id"])}" aria-hidden="true"></div>'
    symbol = ""
    source = str(button.get("symbolSrc") or "")
    if source.startswith("data:image/"):
        key = (symbols or {}).get(source)
        if key:
            symbol = f'<svg class="symbol" viewBox="0 0 300 300" aria-hidden="true" focusable="false"><use href="#sym-{key}"/></svg>'
        else:
            symbol = f'<img class="symbol" src="{attr(source)}" alt="" aria-hidden="true">'
    style = button.get("style", {})
    font = button.get("font", {})
    presentation = [placement]
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
    badge = '<span class="schedule-badge" aria-hidden="true"></span>' if schedule_step else ""
    word_class = button.get("wordClass", "")
    return (
        f'<button style="{attr(";".join(presentation))}" data-symbol-layout="{attr(layout)}" id="{attr(button["id"])}" class="dwell-btn board-button role-{attr(button["role"])}" type="button" '
        f'data-button-id="{attr(button["id"])}" data-label="{attr(button["label"])}" '
        f'data-spoken="{attr(button["spokenText"])}" data-actions="{json_attr(button["actions"])}" '
        f'data-function="{attr(button["function"])}" data-role="{attr(button["role"])}" data-word-class="{attr(word_class)}" '
        f'data-student-target{dwell_attr} aria-label="{attr(button["label"])}">{symbol}'
        f'<span class="scan-number" aria-hidden="true">{scan_number}. </span><span class="label">{html.escape(button["label"])}</span>{badge}<span class="dwell-progress" aria-hidden="true"></span></button>'
    )


def render_page(page: dict[str, Any], first: bool, dwell_enabled: bool, title: str, attribution: str, symbols: dict[str, str] | None = None) -> str:
    hidden = "" if first else " hidden"
    steps = set(page.get("schedule", {}).get("steps", []))
    cells = []
    scan_number = 0
    for row, column, button in grid_slots(page):
        if not button.get("hidden"):
            scan_number += 1
        cells.append(render_button(button, dwell_enabled, row, column, scan_number, button["id"] in steps, symbols))
    schedule_status = '<span id="schedule-status" class="schedule-status" aria-live="polite"></span>' if steps else ""
    return (
        f'<section class="board-page" data-page-id="{attr(page["id"])}" data-pattern="{attr(page["pattern"])}" aria-label="{attr(page["name"])}"{hidden}>'
        f'<h2 class="page-title">{html.escape(title if page["name"].lower() == "main" else page["name"])}{schedule_status}</h2>'
        f'<div class="board-grid" style="--grid-rows:{page["grid"]["rows"]};--grid-columns:{page["grid"]["columns"]}">'
        + "\n".join(cells)
        + f'</div><p class="print-attribution">{html.escape(attribution)}</p></section>'
    )


def teacher_control(name: str, label: str, pressed: bool | None = None, disabled: bool = False) -> str:
    pressed_attr = f' aria-pressed="{str(pressed).lower()}"' if pressed is not None else ""
    disabled_attr = " disabled" if disabled else ""
    return f'<button type="button" class="teacher-control" data-teacher-control="{attr(name)}" aria-label="{attr(label)}"{pressed_attr}{disabled_attr}>{html.escape(label)}</button>'


def symbol_summary(ir: dict[str, Any]) -> str:
    visible = [
        button for page in ir["pages"] for button in page["buttons"]
        if not button.get("hidden") and button.get("wordClass") not in {"letter", "ending"} and button.get("role") != "navigation"
    ]
    with_symbol = [button for button in visible if str(button.get("symbolSrc") or "").startswith("data:image/")]
    proposed = sum(1 for button in with_symbol if button.get("symbolStatus") == "proposed")
    approved = sum(1 for button in with_symbol if button.get("symbolStatus") == "approved")
    other = len(with_symbol) - proposed - approved
    text_only = len(visible) - len(with_symbol)
    parts = [f"{len(with_symbol)} of {len(visible)} word and message buttons show a symbol (letters and page buttons are text by design)"]
    if proposed:
        parts.append(f"{proposed} proposed by the agent and awaiting team review")
    if approved:
        parts.append(f"{approved} team-approved")
    if other:
        parts.append(f"{other} supplied with the board")
    parts.append(f"{text_only} text-only")
    return "; ".join(parts) + "."


def teacher_panel(ir: dict[str, Any], attribution: str) -> str:
    notes = ir["teacherNotes"]
    speech = ir.get("speech", {})
    preferred = speech.get("voiceName") or "none pinned: the board picks an installed voice for " + (speech.get("lang") or ir["audience"]["locale"])
    log = ir.get("evidenceLog", {"enabled": False, "consentNote": "Not configured."})
    if log.get("enabled"):
        log_controls = (
            '<div class="teacher-controls">'
            + teacher_control("log-start", "Record selections", pressed=False)
            + teacher_control("log-model", "Partner modelling", pressed=False)
            + teacher_control("log-export", "Download CSV")
            + teacher_control("log-clear", "Clear log")
            + "</div><p>Ctrl+Shift+M also switches partner modelling on and off. Nothing is saved after the page closes: download first.</p>"
        )
    else:
        log_controls = "<p>Selection logging is switched off for this board. The team can switch it on in the board settings (evidenceLog.enabled) once the purpose and consent are agreed.</p>"
    schedule = ""
    if any(page.get("schedule") for page in ir["pages"]):
        schedule = (
            '<section><h3>Schedule</h3><div class="teacher-controls">'
            + teacher_control("schedule-done", "Mark step done")
            + teacher_control("schedule-undo", "Undo last done")
            + "</div></section>"
        )
    return (
        '<aside id="teacher-panel" class="teacher-panel" aria-label="Teacher panel" aria-hidden="true">'
        '<div class="teacher-head"><h2 tabindex="-1">Teacher panel</h2>'
        + teacher_control("panel-close", "Close teacher panel")
        + "</div>"
        '<p class="teacher-help">Open with three quick taps on the board title, Ctrl+Shift+T, or by adding ?teacher=1 to the address. These controls are never student targets.</p>'
        f'<section><h3>Voice</h3><p id="voice-status">Voice: browser default.</p><p>Preferred voice: {html.escape(preferred)}. Installed voices keep working offline; Edge "Online (Natural)" voices need internet.</p></section>'
        + schedule
        + f'<section><h3>Selection log</h3><p>{html.escape(log.get("consentNote", ""))}</p>{log_controls}<div id="log-summary" aria-live="polite"></div></section>'
        + f"<section><h3>Symbols</h3><p>{html.escape(symbol_summary(ir))}</p></section>"
        + card_fragment(ir, 3)
        + f'<section><h3>Board notes</h3><p><strong>Model:</strong> {html.escape(notes["modeling"])}</p><p><strong>Evidence:</strong> {html.escape(notes["evidence"])}</p><p><strong>Customise:</strong> {html.escape(notes["customisation"])}</p></section>'
        + f'<p class="attribution">{html.escape(attribution)}. Text fallback remains available. ARASAAC pictograms, when embedded, require their stated attribution.</p></aside>'
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
    symbols = symbol_table(ir)
    pages = "\n".join(render_page(page, index == 0, dwell_enabled, ir["title"], attribution, symbols) for index, page in enumerate(ir["pages"]))
    message_bar = ""
    if ir.get("messageBar", {}).get("enabled"):
        placeholder = ir["messageBar"]["placeholder"]
        message_bar = (
            '<section class="message-bar" aria-label="Message bar">'
            f'<div id="message-text" class="message-text is-placeholder" role="status" aria-live="polite" data-placeholder="{attr(placeholder)}">'
            f'{html.escape(placeholder)}</div></section>'
        )
    stop_enabled = controls["stopSpeechDuringPlayback"]
    speech_column = ""
    if stop_enabled:
        speech_column = (
            '<div class="speech-column" role="group" aria-label="Speech controls">'
            f'<button id="stop-speech" class="dwell-btn stop-control" type="button" data-control="stop-speech" data-student-target{" data-dwell" if dwell_enabled else ""} aria-label="Stop speech">'
            '<span class="label">Stop speech</span><span class="dwell-progress" aria-hidden="true"></span></button></div>'
        )
    display = ir["display"]
    background = css_colour(display.get("backgroundColour"), "#f7fbff")
    highlight = css_colour(display.get("highlightColour"), "#FFD400")
    visual_profile = display.get("visualProfile", "standard")
    colour_scheme = display.get("colourScheme", "none")
    stop_column = f"calc(var(--min-target) + 12px)" if stop_enabled else "0px"
    css = f"""
:root {{ --min-target: {ir['access']['minimumTargetSizePx']}px; --dwell-ms: {ir['access']['dwellTimeMs'] or 1200}ms; --ink:#17212b; --focus:#005fcc; --repair:#ffe3e3; --highlight:{highlight}; --stop-column:{stop_column}; }}
* {{ box-sizing:border-box; }}
html, body {{ margin:0; min-height:100%; font-family:Verdana,Arial,sans-serif; color:var(--ink); background:{attr(background)}; }}
body {{ min-height:100vh; }}
button {{ font:inherit; color:inherit; }}
[hidden] {{ display:none !important; }}
.skip-link {{ position:absolute; left:-9999px; }} .skip-link:focus {{ left:8px; top:8px; z-index:20; background:white; padding:8px; }}
.setup-screen {{ min-height:100vh; display:grid; place-content:center; gap:20px; padding:24px; text-align:center; }}
.setup-controls {{ display:flex; flex-wrap:wrap; justify-content:center; gap:24px; }}
.student-layer {{ height:100vh; overflow:auto; padding:12px; display:flex; flex-direction:column; }}
.board-area {{ flex:1 1 0; min-height:0; display:grid; grid-template-columns:minmax(0,1fr) var(--stop-column); }}
.board-pages {{ display:flex; flex-direction:column; min-width:0; min-height:0; }}
.board-page {{ flex:1 1 0; min-height:0; display:flex; flex-direction:column; }}
.speech-column {{ display:flex; justify-content:flex-end; align-items:flex-start; }}
.stop-control {{ visibility:hidden; width:var(--min-target); background:#ffe3e3; font-size:clamp(1rem,2vw,1.4rem); }}
.speech-active .stop-control {{ visibility:visible; }}
.page-title {{ margin:0 0 8px; text-align:center; font-size:clamp(1.1rem,2.4vw,1.8rem); user-select:none; }}
.board-grid {{ flex:1 1 0; min-height:calc(var(--grid-rows) * var(--min-target) + (var(--grid-rows) - 1) * 12px); display:grid; grid-template-columns:repeat(var(--grid-columns), minmax(var(--min-target),1fr)); grid-template-rows:repeat(var(--grid-rows), minmax(var(--min-target),1fr)); gap:12px; }}
.message-bar {{ width:100%; margin:0 auto 10px; max-width:1200px; min-height:60px; padding:10px 16px; border:3px solid var(--ink); border-radius:14px; background:white; font-size:clamp(1rem,2.2vw,1.5rem); }}
.is-placeholder {{ color:#58636e; }}
.dwell-btn {{ position:relative; overflow:hidden; min-width:var(--min-target); min-height:var(--min-target); border:4px solid var(--ink); border-radius:18px; background:#fff; padding:12px; font-size:clamp(1rem,2.5vw,1.6rem); font-weight:700; cursor:pointer; touch-action:manipulation; }}
.dwell-btn:focus-visible {{ outline:6px solid var(--focus); outline-offset:3px; }}
.role-repair {{ background:var(--repair); }} .role-navigation {{ background:#e8eef4; }}
.dwell-progress {{ position:absolute; inset:auto 0 0; height:10px; background:#ffbf00; transform:scaleX(0); transform-origin:left; }}
.is-dwelling .dwell-progress {{ animation:dwell-fill var(--dwell-ms) linear forwards; }}
.was-activated {{ filter:brightness(.82); }}
.masked-cell {{ border:3px dashed transparent; border-radius:18px; }}
.board-button {{ display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; }}
.board-button[data-symbol-layout="label-top"] .label {{ order:-1; }}
.board-button[data-symbol-layout="label-left"] {{ flex-direction:row-reverse; }}
.board-button[data-symbol-layout="label-right"] {{ flex-direction:row; }}
.symbol {{ display:block; flex:1 1 0; min-height:0; width:100%; max-width:100%; max-height:180px; object-fit:contain; }}
.symbol-defs {{ position:absolute; width:0; height:0; overflow:hidden; }}
.selected-message {{ min-height:44px; margin:0 0 6px; padding:6px; text-align:center; font-size:clamp(1.1rem,2.2vw,1.5rem); font-weight:700; }}
.schedule-status {{ margin-left:.6em; font-size:.75em; font-weight:400; }}
.schedule-badge {{ display:inline-block; padding:2px 10px; border-radius:999px; background:var(--ink); color:#fff; font-size:.8em; }}
.schedule-badge:empty {{ display:none; }}
.is-now {{ border-width:8px; }} .is-next {{ border-style:dashed; }}
.is-done .label {{ text-decoration:line-through; }} .is-done {{ color:#3d4a55; }}
.scan-number,.print-attribution {{ display:none; }}
.board-status {{ position:fixed; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); }}
.indicator {{ position:fixed; top:6px; left:8px; z-index:15; padding:4px 10px; border-radius:999px; background:#17212b; color:#fff; font-size:.9rem; pointer-events:none; }}
#modelling-indicator {{ left:auto; right:8px; background:#5b2a86; }}
.teacher-panel {{ display:none; padding:18px; border:2px solid #555; background:white; color:#17212b; }}
body.teacher-mode .teacher-panel {{ display:block; position:fixed; top:0; right:0; bottom:0; z-index:30; width:min(480px,100vw); overflow:auto; box-shadow:-6px 0 18px rgba(0,0,0,.25); }}
.teacher-head {{ display:flex; justify-content:space-between; align-items:center; gap:12px; }}
.teacher-controls {{ display:flex; flex-wrap:wrap; gap:8px; }}
.teacher-control {{ padding:8px 12px; border:2px solid #17212b; border-radius:8px; background:#fff; cursor:pointer; }}
.teacher-control[aria-pressed="true"] {{ background:#17212b; color:#fff; }}
.teacher-panel table {{ border-collapse:collapse; margin-top:8px; }} .teacher-panel th, .teacher-panel td {{ border:1px solid #888; padding:3px 8px; text-align:left; }}
.attribution {{ font-size:.75rem; }}
body[data-visual-profile="cvi"] {{ background:#000; color:#fff; }}
body[data-visual-profile="cvi"] .dwell-btn {{ background:#000 !important; color:#fff !important; border-color:#fff; }}
body[data-visual-profile="cvi"] .dwell-btn:focus-visible, body[data-visual-profile="cvi"] .is-dwelling {{ border-color:var(--highlight); outline:6px solid var(--highlight); }}
body[data-visual-profile="cvi"] .dwell-progress {{ background:var(--highlight); height:14px; }}
body[data-visual-profile="cvi"] .symbol {{ background:#fff; border-radius:12px; padding:6px; }}
body[data-visual-profile="cvi"] .board-grid {{ gap:24px; }}
body[data-visual-profile="cvi"] .message-bar {{ background:#000; color:#fff; border-color:#fff; }}
body[data-visual-profile="cvi"] .is-placeholder {{ color:#cfcfcf; }}
@keyframes dwell-fill {{ to {{ transform:scaleX(1); }} }}
@media (max-width:760px) {{ .board-grid {{ gap:7px; }} .dwell-btn {{ padding:7px; }} }}
@media (forced-colors:active) {{ .dwell-btn {{ border-color:ButtonText; forced-color-adjust:auto; }} .dwell-progress {{ background:Highlight; }} }}
@page {{ size:{paper} {orientation}; margin:12mm; }}
@media print {{ .selected-message,.message-bar,.setup-screen,.speech-column,.board-status,.indicator,.teacher-controls,.teacher-head button,.teacher-help,.schedule-status,.schedule-badge {{ display:none !important; }} .board-area {{ display:block; }} .student-layer {{ display:block !important; }} .student-layer,.teacher-panel {{ display:block !important; position:static !important; width:auto !important; box-shadow:none !important; }} .board-page {{ break-after:page; break-inside:avoid; }} .teacher-panel {{ break-before:page; }} .scan-number {{ display:inline; position:absolute; top:5px; left:8px; font-size:12pt; }} .dwell-progress {{ display:none; }} .dwell-btn:focus-visible {{ outline:none; }} .board-page[hidden] {{ display:block !important; }} .board-grid {{ min-height:0; height:{page_height_mm - 54}mm; }} .print-attribution {{ display:block; margin:6px 0 0; font-size:8pt; }} .dwell-btn {{ min-width:0; min-height:30mm; font-size:16pt; }} .symbol {{ flex:none; height:20mm; }} .student-layer {{ height:auto; min-height:0; overflow:visible; padding:0; }} }}
"""
    return f"""<!doctype html>
<html lang="{attr(ir['audience']['locale'])}" data-runtime-sha256="{runtime_hash}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{html.escape(ir['title'])}</title><style>{css}</style></head>
<body data-access-profile="{attr(ir['access']['profile'])}" data-dwell-enabled="{str(dwell_enabled).lower()}" data-min-target="{ir['access']['minimumTargetSizePx']}" data-visible-target-limit="{ir['access']['visibleTargetLimit']}" data-setup-target-limit="{ir['access']['setupTargetLimit']}" data-visual-profile="{attr(visual_profile)}" data-colour-scheme="{attr(colour_scheme)}">
{symbol_defs(symbols)}
<a class="skip-link" href="#student-layer">Skip to board</a>
<section id="setup-screen" class="setup-screen" aria-label="Board setup"{setup_hidden}><h1 class="setup-title">{html.escape(ir['title'])}</h1><p>Choose Start board when positioning and access are ready.</p><div class="setup-controls">{''.join(setup_controls)}</div></section>
<main id="student-layer" class="student-layer"{student_hidden}><span id="recording-indicator" class="indicator" hidden>&#9679; Recording</span><span id="modelling-indicator" class="indicator" hidden>Partner modelling</span>{message_bar}<p id="selected-message" class="selected-message" aria-live="polite">Choose a message.</p><div class="board-area"><div class="board-pages">{pages}</div>{speech_column}</div></main>
<div id="board-status" class="board-status" role="status" aria-live="polite">Board ready.</div>
{teacher_panel(ir, attribution)}
<script id="aac-board-ir" type="application/json">{embedded_json(compact_ir(ir, symbols))}</script>
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

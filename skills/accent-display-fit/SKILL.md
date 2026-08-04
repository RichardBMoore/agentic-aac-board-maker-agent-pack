---
name: accent-display-fit
description: Make single-file HTML student activities display correctly on PRC-Saltillo Accent devices (800/1000/1400, NuVoice or Empower) and on EQ-managed Microsoft Edge. Use when a file looks right on a laptop but is cut off, oversized, scrolling or off-screen on the Accent, when planning viewport- and scaling-safe layout, or when delivering HTML via OneDrive/SharePoint/USB on the Education Queensland network. Owns effective-viewport maths (Windows display scaling, NuVoice Key Mode, Empower browser chrome), fit-first CSS rules, a conservative feature baseline, delivery routes and display QA. Pair with eyegaze-dwell-html for dwell mechanics and agentic-aac-board-maker for AAC vocabulary.
---

# Accent Display Fit

This skill owns one problem: a file that renders correctly on a teacher laptop but breaks on the student's Accent or EQ-managed Edge. It does not choose vocabulary (see `../agentic-aac-board-maker/SKILL.md`) or own dwell mechanics (see `../eyegaze-dwell-html/SKILL.md`). Apply this skill to every student-facing HTML build for an Accent or EQ device, and when QA-ing a file that "doesn't display correctly".

## Why Files Break On The Accent

1. **Windows display scaling.** The Accent 1400-30 has a 14 in 1920 x 1080 screen. Windows commonly recommends 150% scaling for a panel in this class; at that planning assumption the browser viewport is about **1280 x 720 CSS px** — minus browser chrome. Check the real device rather than treating 150% as a PRC-set default. Files authored and tested at 1920 x 1080 overflow, clip or force scroll.
2. **Older hardware is smaller.** The original Accent 1400 (2013) is 1280 x 800 native. Accent 1000-series and 800-series units differ again. Never assume one resolution.
3. **The browser window is not the screen.** NuVoice has no built-in browser; browsing uses Windows Edge (Integrated Feature Pack). In NuVoice Key Mode the computer window shrinks to **half-screen or less**. The Empower Accessible Web Browser keeps two toolbar rows on screen. Non-fullscreen Edge loses ~110 px to tabs and address bar.
4. **Zoom drift.** The Empower browser exposes Zoom In/Out buttons and Edge remembers page zoom. Layouts must survive 67–150% zoom without breaking.
5. **Old engines exist.** An Accent that has been offline since unlock may run a years-old Edge. Cutting-edge CSS/JS silently produces a broken or blank layout there.

Read `references/accent-device-field-guide.md` for the sourced device facts.

## Effective Viewport, Not Native Resolution

Design and test against the CSS viewport the student's browser actually gets:

| Setup | Effective CSS viewport (approx.) |
| --- | --- |
| Accent 1400-30, Edge fullscreen, 150% scaling | 1280 x 720 |
| Accent 1400-30, Edge maximised (not fullscreen) | 1280 x ~610 |
| Original Accent 1400, Edge fullscreen | 1280 x 800 (100% scaling) |
| NuVoice Key Mode computer window | half screen or less — plan for ~1180 x 460 |
| Empower Accessible Web Browser | ~1280 x ~600 (two toolbar rows retained) |

Two floors govern every build:

- **Must-fit floor 1264 x 600:** all student content and controls visible, no scrolling, targets at full size.
- **Grace floor 1024 x 460:** no horizontal scroll, setup controls still reachable and ≥120 px; content may paginate.

If the intended student's device and scaling are known, design for that exact effective viewport instead — but still pass the floors, because settings drift.

## Display Contract

- One self-contained file. No CDN, webfont, or symbol API: EQ's web filter and offline devices both break external references. Verdana/Arial/system fonts only.
- Include `<meta charset="utf-8">` and `<meta name="viewport" content="width=device-width,initial-scale=1">`.
- No fixed page width or height in px. Layout uses fr, %, minmax() and clamp(); images use max-width/max-height percentages with `object-fit:contain`.
- **Fit maths must pass at the must-fit floor.** For a grid: `cols x target + (cols-1) x gap + horizontal padding <= 1264` and `rows x target + (rows-1) x gap + page chrome <= 600` (page chrome = title + message bar + padding; ~96 px, ~166 px with a message bar). When the maths fails, put fewer cells on each page and paginate — never shrink targets below 120 px and never allow student-mode scroll.
- Pair viewport heights: declare `min-height:100vh;` immediately followed by `min-height:100dvh;`. Never derive element sizes from an assumed 1080/1200 px screen.
- Feature baseline: the static layout must render without `:has()`, `@container`, `subgrid`, or CSS nesting; guard anything newer than ~2020 Chromium behind `@supports`. The page must show its layout and a readable message even if JavaScript fails.
- No horizontal scroll at any supported size; no vertical scroll in student mode.

Implementation patterns, the fit formula and the banned/guarded feature table are in `references/display-fit-rules.md`.

## Interaction Reality On Real Accents

- NuVoice eye tracking (NuEye/Look) drives the **Windows pointer**, with OS-level dwell (default 1.0 s) that fires real clicks through a post-select menu. Click activation is therefore first-class on-device, not a fallback; page hover-dwell is an enhancement layered on top.
- Page dwell and OS dwell can double-fire. Keep the canonical runtime's single-activation suppression; never add a second timer path.
- Agree with the student's team which layer owns dwell (page hover-dwell vs NuVoice Windows dwell) and set the page dwell time accordingly rather than guessing.
- The Empower browser navigates by Select Link and scroll buttons, so every target must stay a semantic `<button>`/link (already pack law).

## Delivery On The EQ Network

OneDrive and SharePoint **do not render HTML files** — links force a download or show raw source in preview. A shared link alone is not a working delivery. Use one of the routes in `references/eq-delivery-playbook.md`: download-then-open from `file:///` in Edge, USB transfer (a USB drive ships with every Accent), or IT-hosted intranet. The Empower browser cannot download files at all, so Empower devices need USB or a hosted URL. The playbook covers Mark of the Web, EQ filtering, fullscreen policy and a teacher handover checklist.

## QA Gate

A build is not done until:

1. `python3 skills/accent-display-fit/scripts/check_accent_display.py <file.html>` passes (add `--profile grace`, `--profile keymode` or `--profile empower` when those device paths are in scope).
2. `npm run test:accent` passes — real browser checks at the effective viewports above (`browser-tests/accent-display.spec.mjs`; point it at a new file with `ACCENT_QA_FILE`).
3. The existing gates still pass: `check_eye_gaze_html.py`, parity checks and the Playwright board suite.
4. A five-minute on-device smoke test on the actual student setup: open via the intended delivery route; check Settings > Display for the real scaling factor; confirm fullscreen, no scroll, every target visible and reachable, dwell and click both activate exactly once.

## Handoff Caveat

Viewport figures here are evidence-based defaults, not guarantees. Scaling, NuVoice layout, browser version and mounting vary per device. Call the file a draft until it has been opened on the student's own Accent, via the real delivery route, with the student's access method.

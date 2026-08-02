---
name: eyegaze-dwell-html
description: Build or QA single-file HTML when eye gaze, mouse dwell, dwell buttons, PRC-Saltillo Accent devices, or Microsoft Edge file/offline gaze use is explicitly required. Owns dwell cancellation, progress, fullscreen, target accounting and device interaction mechanics; it does not choose AAC vocabulary or curriculum evidence. Pair with agentic-aac-board-maker only when the task is an AAC board.
---

# Eye Gaze And Dwell HTML

Use for explicit gaze/dwell implementation and QA. For AAC vocabulary, board grammar, agency and system fit, start with `../agentic-aac-board-maker/SKILL.md`; this skill owns only the interaction/access layer.

## Required Build Path

For AAC boards in this pack:

1. Create canonical IR 0.4.0 with an `eye-gaze-dwell`/`mouse-dwell` profile or intended method.
2. Render with `../agentic-aac-board-maker/scripts/render_html.py`.
3. Do not paste or invent another DwellManager. The only runtime source is `../agentic-aac-board-maker/assets/aac-board-runtime.js`.
4. Verify with `../agentic-aac-board-maker/scripts/validate_html_parity.py`, `../build-aac-student-supports/scripts/check_eye_gaze_html.py` and the Playwright browser suite.

For a non-AAC custom dwell activity, reuse the same runtime/interaction contract or deliberately extract a reusable renderer around it. Do not fork one-off timer logic into every file.

## Device Context

- Eye tracking commonly presents as a Windows pointer; test pointer enter/leave, not touch alone.
- PRC-Saltillo Accent browser access depends on device configuration; test the actual Accent/Edge setup rather than assuming desktop results transfer.
- Student-use files must work offline/from `file:///` unless the user explicitly accepts hosting.
- Use Australian English by default and retain keyboard/click fallbacks for staff and alternative access.

Read `../build-aac-student-supports/references/eye-gaze-and-switch.md` for access design and `../build-aac-student-supports/references/eye-gaze-html-tools.md` for offline/Edge constraints.

## Interaction Contract

- Semantic native buttons; no canvas-only target field.
- Minimum 120×120 px active targets; prefer 200 px+ when the screen/task permits.
- Pointer enter starts one timer; pointer leave, pointer cancel and focus loss cancel immediately.
- Visible progress and visible keyboard focus; no reliance on colour alone.
- One activation per completed dwell and short suppression of the follow-on synthetic click.
- No drag, long gaze sequence, single-dwell destructive action or hidden tiny control.
- TTS errors are announced; active speech exposes one gaze-sized Stop Speech target.

## Total Active-Target Accounting

Count all simultaneously active student controls—not just choice cells.

- Setup phase: Start board, Full screen and Sound check only; default maximum three.
- Board phase: vocabulary, repair, navigation and any message utility controls together; conservative untested gaze maximum nine.
- Speech phase: hide/inert setup and board; Stop Speech is the sole active target.
- Teacher/settings controls do not remain in ordinary student mode.

The canonical runtime exposes `window.AACBoard.auditVisibleTargets()`. Treat an over-limit result as a build failure.

## Fullscreen

- Provide a gaze-sized Full screen setup control and leave the board usable when it is blocked.
- Ordinary Edge requires transient user activation; a JavaScript dwell timer may not qualify. Announce click/Enter/OS-dwell/F11 fallback honestly.
- Managed Edge policy or kiosk deployment is an IT decision; a page cannot grant itself that authority.
- Setup controls disappear after Start board so they do not remain accidental gaze targets.

## Real QA

Static inspection is insufficient. At minimum verify:

- real pointer enter → leave cancels and enter → dwell activates once;
- click and native keyboard activation;
- setup/board/speech target counts and physical dimensions;
- fullscreen rejection state;
- Stop Speech isolation;
- navigation/message behaviour where present;
- no page/console errors, serious accessibility violations or external runtime dependencies;
- intended classroom/device-sized viewports and, before relying on it, the actual student/device/mount/browser environment.

The repository Playwright suite provides baseline Accent 1000-sized, Accent 1400-sized and classroom-laptop viewports. Viewport names are QA profiles, not claims that every device is configured to that pixel size.

## Handoff Caveat

Call the result a draft until access calibration, dwell time, target layout, reliable cancellation, positioning, vision/fatigue and partner signals have been tried with the student and team on the real setup.

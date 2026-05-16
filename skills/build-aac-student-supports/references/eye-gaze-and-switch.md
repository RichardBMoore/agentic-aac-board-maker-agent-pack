# Eye Gaze, Dwell, And Switch Access

Use this reference for eye-gaze, dwell, switch scanning, PRC-Saltillo Accent, Microsoft Edge, offline school network, or accidental-activation work.

For single-file Accent/Edge HTML implementation details, read `eye-gaze-html-tools.md`. For copyable CSS, JavaScript, modal, and layout snippets, read `templates.md`.

## Operating Assumptions

- Eye gaze usually behaves like a mouse pointer. Build for pointer hover/enter/leave and focus, not touch-only events.
- A page opened from `file:///` cannot rely on service workers, module imports from remote CDNs, or many browser APIs that require a secure origin.
- On locked-down school networks, assume no CDN and intermittent access to symbol APIs. Inline critical CSS and JS for single-file resources.
- Exact AAC device specs change by model. Do not hardcode one screen size; use responsive layout and test the actual target viewport when available.
- Eye gaze is tiring. Keep sessions short, avoid clutter, and make rest/stop options available.

## Dwell Behaviour

Required dwell behaviour:

1. Start dwell on pointer or mouse entry.
2. Show visible progress while dwelling.
3. Cancel immediately on pointer or mouse leave.
4. Activate only after the dwell threshold completes.
5. Prevent repeated accidental activation of the same target until the pointer leaves or a short guard period passes.
6. Provide visible and optional spoken completion feedback.

Use keyboard focus as a strong focus indicator. Use Enter/Space for keyboard activation. Only start dwell on focus when the activity deliberately needs keyboard-dwell behaviour.

Good timing defaults:

- Confident gaze user: 600 to 800 ms.
- Default classroom starting point: 800 to 1200 ms.
- Accidental activation risk: 1000 to 1500 ms.
- Confirmation step: around 600 ms.
- Avoid going below 500 ms or above 1500 ms unless the student/team specifically needs it.

## Target And Layout Rules

- Start with 120 px minimum width and height for primary gaze buttons.
- Use 150 to 200 px cells when the board has few choices and the screen can support it.
- Keep at least 20 px between gaze targets where practical.
- If large targets cause scrolling, reduce headings, toolbars, margins, and decorative content before shrinking targets.
- Prefer one central interaction area. Avoid tiny clustered controls near primary choices.
- Use stable dimensions with grid tracks, aspect ratios, and min/max sizes so hover, focus, and dwell states do not move the layout.

## Single-File HTML Pattern

For a portable student support, create one `.html` file with:

- Inline CSS and JS.
- No CDN, external fonts, or remote libraries.
- A data block or JavaScript object for activity content.
- Semantic `<button>` elements for student choices.
- `aria-live` status for spoken/visible feedback.
- Keyboard navigation with Tab and Enter/Space at minimum. Arrow navigation is useful for grid boards.
- A Stop Speech button when speech synthesis is used.
- A teacher/settings area that can be hidden or locked for student mode.

Avoid:

- `touchstart` as the only activation path.
- Pointer-down activation for student choices.
- Drag-only or gesture-only interactions.
- Auto-fullscreen assumptions. Browsers require user gesture or managed kiosk policy.

## Switch Scanning

Start with linear scanning:

- Highlight one available target at a time in DOM order.
- Provide Start/Stop Scan, Step, Select, and scan speed.
- Use Space or Enter for select, `S` for step where appropriate, and Escape to stop.
- Announce or cue the current item only if it helps the student and does not become noisy.

Add row-column scanning when there are more than about 8 to 12 choices:

- First scan rows.
- Select a row.
- Then scan cells within that row.
- After selection, return to row phase.

Scan states must be visually strong and not depend on colour alone.

## High-Stakes Actions

Require confirmation for:

- Submit
- Reset
- Delete
- Clear Data
- Export/send
- Leave activity

Use a confirm screen, a second dwell, or an undo path. Do not let one accidental hover erase work or submit a final answer.

## Verification

Manually test:

- Pointer enter starts dwell and pointer leave cancels it.
- Keyboard focus starts dwell only if intended, and blur cancels it.
- Click/tap activation still works if dwell is off.
- Re-select guard prevents repeated firing while gaze remains on the same target.
- Switch scanning can start, step, select, and stop.
- Target size and spacing remain usable at the target viewport.
- Important content is not hidden below the fold in classroom mode.

# Partner-Assisted Scanning Print Board

Generated from proof-of-concept fixture: `partner-assisted-print` / "Make a printable partner-assisted scanning board for help, stop, different, finished, and choices."

## Files

- `partner-assisted-scanning-print-board.ir.json` - canonical AAC Board IR 0.5.0 source of truth (house standards applied).
- `partner-assisted-scanning-print-board.html` - single-file offline HTML board with print stylesheet and teacher panel.
- `partner-card.html` - one-page card for communication partners.
- `partner-assisted-scanning-print-board.open-aac-studio.json` - Open AAC Studio-compatible export.
- `partner-assisted-scanning-print-board.obz` - Open Board Format export.
- `teacher-notes.md` - teacher notes, evidence/customisation notes and caveats.

## Expected outputs covered

- `aac-board-ir`
- `printable-board`
- `partner-script`

## Required fixture checks addressed

- `scan-order`
- `black-and-white-readable`
- `partner-wait-confirm`
- `attribution`
- `house-standards`
- `partner-card`
- `keyboard-route`

## How the board works

- **Talk** (3x3): Yes, No, Stop, ABC, More time, Choices ▶, Help, Different, Finished.
- **Choices** (3x3): Choice A, Choice B, ◀ Talk, Core words ▶, Help.

The house standards tool added a **Core words** page (I, want, don't, like, go, more) that builds messages in the message bar, a **Word endings** page (-s, -ing, -ed, with Undo and Start again) and an **ABC keyboard** (QWERTY letter groups, then letters; Speak, Delete and Help on the keyboard page). Talking pages link forward with the right-middle button and back with the left-middle button; ABC sits left-middle on the first page.

- **House words:** Help is bottom-left on every page; Different is bottom-middle wherever it appears; Undo is bottom-middle wherever it appears; Finished is bottom-right wherever it appears; Stop is top-right wherever it appears; Speak is top-right wherever it appears; ABC is left-middle of the first page. Page buttons: ▶ forward is right-middle, ◀ back is left-middle. Stop speech appears at the right edge while the board is talking. Each house word says the same message on every board.
- **Speech:** the board stays visible while it speaks; Stop speech appears at the right edge; a new selection interrupts.
- **Colour:** fills follow the Modified Fitzgerald Key by word type (for example green actions, blue describing words, pink social words, red help/stop words).

## Access

- Intended access: partner-assisted-scanning, print, touch, keyboard, mouse (profile `partner-assisted-scanning`).
- At most 16 active targets per page; minimum target size 132 px.
- Dwell: not used; dwell re-arms only after the pointer leaves.
- Keyboard: Tab plus Enter/Space; Escape cancels dwell or stops speech.
- Print: browser print shows every page with scan numbers and a teacher/partner-card page.

## Communication purpose

A printable partner-assisted scanning board with clear scan order, wait/confirm script, help, stop, different, finished and choice messages.

## Symbols

16 of 20 different word and message buttons show a symbol; 16 of these were proposed by the agent and await team review. Letters and page buttons are text by design. Text-only words: Choice A, Choice B, don't, Space.

## Caveat

This is a draft classroom support. Review with the teaching/SLP/OT team and test on the actual student device, browser, access method and school environment before relying on it.

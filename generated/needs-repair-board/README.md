# Secondary Needs and Communication Repair Board

Generated from proof-of-concept fixture: `needs-repair-board` / "Make a respectful needs and communication repair board for a secondary student."

## Files

- `secondary-needs-repair-board.ir.json` - canonical AAC Board IR 0.5.0 source of truth (house standards applied).
- `secondary-needs-repair-board.html` - single-file offline HTML board with print stylesheet and teacher panel.
- `partner-card.html` - one-page card for communication partners.
- `secondary-needs-repair-board.open-aac-studio.json` - Open AAC Studio-compatible export.
- `secondary-needs-repair-board.obz` - Open Board Format export.
- `teacher-notes.md` - teacher notes, evidence/customisation notes and caveats.

## Expected outputs covered

- `aac-board-ir`
- `html-or-printable-board`
- `teacher-notes`

## Required fixture checks addressed

- `age-respectful`
- `repair-language`
- `privacy-safe`
- `not-behaviour-control`
- `house-standards`
- `partner-card`
- `keyboard-route`
- `core-words`

## How the board works

- **I need** (3x3): Break, Wait, I feel unwell, ABC, I need privacy, Sort it out ▶, Help, Too loud, Finished.
- **Sort it out** (3x3): Say it another way, Not that, I disagree, ◀ I need, Can I choose?, Core words ▶, Help, Different.

The house standards tool added a **Core words** page (I, want, don't, like, go, more) that builds messages in the message bar, a **Word endings** page (-s, -ing, -ed, with Undo and Start again) and an **ABC keyboard** (QWERTY letter groups, then letters; Speak, Delete and Help on the keyboard page). Talking pages link forward with the right-middle button and back with the left-middle button; ABC sits left-middle on the first page.

- **House words:** Help is bottom-left on every page; Different is bottom-middle wherever it appears; Undo is bottom-middle wherever it appears; Finished is bottom-right wherever it appears; Speak is top-right wherever it appears; ABC is left-middle of the first page. Page buttons: ▶ forward is right-middle, ◀ back is left-middle. Stop speech appears at the right edge while the board is talking. Each house word says the same message on every board.
- **Speech:** the board stays visible while it speaks; Stop speech appears at the right edge; a new selection interrupts.
- **Colour:** fills follow the Modified Fitzgerald Key by word type (for example green actions, blue describing words, pink social words, red help/stop words).

## Access

- Intended access: touch, keyboard, mouse, eye-gaze-dwell (profile `mixed-access`).
- At most 9 active targets per page; minimum target size 132 px.
- Dwell: 1100 ms; dwell re-arms only after the pointer leaves.
- Keyboard: Tab plus Enter/Space; Escape cancels dwell or stops speech.
- Print: browser print shows every page with scan numbers and a teacher/partner-card page.

## Communication purpose

An age-respectful two-page needs and communication repair board that lets a secondary student request support, privacy, clarification, a break, different choices or communication repair without behaviour-control framing. Help stays on every page and no page exceeds nine targets.

## Symbols

21 of 23 different word and message buttons show a symbol; 21 of these were proposed by the agent and await team review. Letters and page buttons are text by design. Text-only words: don't, Space.

## Caveat

This is a draft classroom support. Review with the teaching/SLP/OT team and test on the actual student device, browser, access method and school environment before relying on it.

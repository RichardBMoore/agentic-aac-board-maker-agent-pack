# Choose a shape

Generated from proof-of-concept fixture: `symbol-shape-choice` / ""

## Files

- `symbol-shape-choice.ir.json` - canonical AAC Board IR 0.5.0 source of truth (house standards applied).
- `symbol-shape-choice.html` - single-file offline HTML board with print stylesheet and teacher panel.
- `partner-card.html` - one-page card for communication partners.
- `symbol-shape-choice.open-aac-studio.json` - Open AAC Studio-compatible export.
- `symbol-shape-choice.obf` - Open Board Format export.
- `teacher-notes.md` - teacher notes, evidence/customisation notes and caveats.

## Expected outputs covered



## Required fixture checks addressed



## How the board works

- **Main** (2x3): Circle, Square, Triangle, Help, Different, Star.

No literacy pages: Early choice board smaller than 3x3; spelling and core words stay on the student's main system.

- **House words:** Help is bottom-left on every page; Different is bottom-middle on every page. Stop speech appears at the right edge while the board is talking. Each house word says the same message on every board.
- **Speech:** the board stays visible while it speaks; Stop speech appears at the right edge; a new selection interrupts.
- **Colour:** fills follow the Modified Fitzgerald Key by word type (for example green actions, blue describing words, pink social words, red help/stop words).

## Access

- Intended access: eye-gaze-dwell, mouse, keyboard, touch (profile `eye-gaze-dwell`).
- At most 9 active targets per page; minimum target size 150 px.
- Dwell: 1000 ms; dwell re-arms only after the pointer leaves.
- Keyboard: Tab plus Enter/Space; Escape cancels dwell or stops speech.
- Print: browser print shows every page with scan numbers and a teacher/partner-card page.

## Communication purpose

Illustrative symbol-rendering fixture: choose a shape, request help or something different. Team review is needed for learner familiarity.

## Symbols

6 of 6 different word and message buttons show a symbol; 2 of these were proposed by the agent and await team review. Letters and page buttons are text by design. Text-only words: none.

## Caveat

This is a draft classroom support. Review with the teaching/SLP/OT team and test on the actual student device, browser, access method and school environment before relying on it.

# Morning Routine Expressive Visual Schedule

Generated from proof-of-concept fixture: `visual-schedule-expressive` / "Make a morning routine visual schedule with expressive options."

## Files

- `morning-routine-expressive-schedule.ir.json` - canonical AAC Board IR 0.5.0 source of truth (house standards applied).
- `morning-routine-expressive-schedule.html` - single-file offline HTML board with print stylesheet and teacher panel.
- `partner-card.html` - one-page card for communication partners.
- `morning-routine-expressive-schedule.open-aac-studio.json` - Open AAC Studio-compatible export.
- `morning-routine-expressive-schedule.obz` - Open Board Format export.
- `teacher-notes.md` - teacher notes, evidence/customisation notes and caveats.

## Expected outputs covered

- `aac-board-ir`
- `visual-schedule`
- `teacher-notes`

## Required fixture checks addressed

- `schedule-order`
- `wait-help-change`
- `not-full-aac-claim`
- `house-standards`
- `partner-card`
- `keyboard-route`
- `schedule-states`

## How the board works

- **Morning routine** (3x3): Arrive, Bag away, Morning job, ABC, Group time, Talk about it ▶, Help, What's next?, Finished.
- **Talk about it** (3x3): Wait, Change, I like it, ◀ Morning routine, I don't like it, Core words ▶, Help.

The house standards tool added a **Core words** page (I, want, don't, like, go, more) that builds messages in the message bar and an **ABC keyboard** (QWERTY letter groups, then letters; Speak, Delete and Help on the keyboard page). Talking pages link forward with the right-middle button and back with the left-middle button; ABC sits left-middle on the first page.

- **House words:** Help is bottom-left on every page; Finished is bottom-right wherever it appears; Speak is top-right wherever it appears; ABC is left-middle of the first page. Page buttons: ▶ forward is right-middle, ◀ back is left-middle. Stop speech appears at the right edge while the board is talking. Each house word says the same message on every board.
- **Speech:** the board stays visible while it speaks; Stop speech appears at the right edge; a new selection interrupts.
- **Colour:** fills follow the Modified Fitzgerald Key by word type (for example green actions, blue describing words, pink social words, red help/stop words).
- **Schedule:** steps show Now ▶, Next and Done ✓. Finished marks the current step done; adults can mark or undo steps in the teacher panel.

## Access

- Intended access: touch, keyboard, mouse, eye-gaze-dwell (profile `mixed-access`).
- At most 9 active targets per page; minimum target size 132 px.
- Dwell: 1100 ms; dwell re-arms only after the pointer leaves.
- Keyboard: Tab plus Enter/Space; Escape cancels dwell or stops speech.
- Print: browser print shows every page with scan numbers and a teacher/partner-card page.

## Communication purpose

A visual schedule that shows morning routine order while preserving expressive options for waiting, help, change, finished and student comments.

## Symbols

18 of 20 different word and message buttons show a symbol; 18 of these were proposed by the agent and await team review. Letters and page buttons are text by design. Text-only words: don't, Space.

## Caveat

This is a draft classroom support. Review with the teaching/SLP/OT team and test on the actual student device, browser, access method and school environment before relying on it.

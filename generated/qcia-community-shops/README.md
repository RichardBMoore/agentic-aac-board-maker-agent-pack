# QCIA Community Access: Going to the Shops

Generated from proof-of-concept fixture: `qcia-community-shops` / "Create a QCIA community access board for going to the shops."

## Files

- `qcia-community-shops.ir.json` - canonical AAC Board IR 0.5.0 source of truth (house standards applied).
- `qcia-community-shops.html` - single-file offline HTML board with print stylesheet and teacher panel.
- `partner-card.html` - one-page card for communication partners.
- `qcia-community-shops.open-aac-studio.json` - Open AAC Studio-compatible export.
- `qcia-community-shops.obz` - Open Board Format export.
- `teacher-notes.md` - teacher notes, evidence/customisation notes and caveats.

## Expected outputs covered

- `aac-board-ir`
- `single-file-html-or-resource-pack`
- `printable`
- `teacher-evidence-note`

## Required fixture checks addressed

- `qcia-evidence`
- `safety-language`
- `help-route`
- `privacy-note`
- `house-standards`
- `partner-card`
- `keyboard-route`
- `core-words`
- `community-intro`

## How the board works

- **Shop talk** (3x3): How I talk, Hello, Stop, ABC, Where is it?, Choosing ▶, Help, Wait, Goodbye.
- **Choosing** (3x3): I want to buy this, Too expensive, Stop, ◀ Shop talk, Yes, At the counter ▶, Help, Wait, No.
- **At the counter** (3x3): Ready to pay, That's all, Thank you, ◀ Choosing, Yes, Core words ▶, Help, Wait, No.

The house standards tool added a **Core words** page (I, want, don't, like, go, more) that builds messages in the message bar, a **Word endings** page (-s, -ing, -ed, with Undo and Start again) and an **ABC keyboard** (QWERTY letter groups, then letters; Speak, Delete and Help on the keyboard page). Talking pages link forward with the right-middle button and back with the left-middle button; ABC sits left-middle on the first page.

- **House words:** Help is bottom-left on every page; Undo is bottom-middle wherever it appears; Stop is top-right wherever it appears; Speak is top-right wherever it appears; ABC is left-middle of the first page. Page buttons: ▶ forward is right-middle, ◀ back is left-middle. Stop speech appears at the right edge while the board is talking. Each house word says the same message on every board.
- **Speech:** the board stays visible while it speaks; Stop speech appears at the right edge; a new selection interrupts.
- **Colour:** fills follow the Modified Fitzgerald Key by word type (for example green actions, blue describing words, pink social words, red help/stop words).
- **How I talk:** the first button introduces the student's way of talking to unfamiliar people.

## Access

- Intended access: touch, keyboard, mouse, eye-gaze-dwell (profile `mixed-access`).
- At most 9 active targets per page; minimum target size 132 px.
- Dwell: 1100 ms; dwell re-arms only after the pointer leaves.
- Keyboard: Tab plus Enter/Space; Escape cancels dwell or stops speech.
- Print: browser print shows every page with scan numbers and a teacher/partner-card page.

## Communication purpose

A community access AAC board that supports practical shopping communication, safety/help language, and teacher evidence notes for QCIA-style participation.

## Symbols

21 of 25 different word and message buttons show a symbol; 21 of these were proposed by the agent and await team review. Letters and page buttons are text by design. Text-only words: Too expensive, That's all, don't, Space.

## Caveat

This is a draft classroom support. Review with the teaching/SLP/OT team and test on the actual student device, browser, access method and school environment before relying on it.

# Year 7 Hero Speech Sentence Builder

Generated from proof-of-concept fixture: `curriculum-sentence-builder` / "Make a Year 7 English hero speech sentence-builder board."

## Files

- `year7-hero-speech-sentence-builder.ir.json` - canonical AAC Board IR 0.5.0 source of truth (house standards applied).
- `year7-hero-speech-sentence-builder.html` - single-file offline HTML board with print stylesheet and teacher panel.
- `partner-card.html` - one-page card for communication partners.
- `year7-hero-speech-sentence-builder.open-aac-studio.json` - Open AAC Studio-compatible export.
- `year7-hero-speech-sentence-builder.obz` - Open Board Format export.
- `teacher-notes.md` - teacher notes, evidence/customisation notes and caveats.

## Expected outputs covered

- `aac-board-ir`
- `sentence-builder-resource`
- `teacher-notes`

## Required fixture checks addressed

- `opinion`
- `because`
- `rehearse-or-speak`
- `repair-option`
- `house-standards`
- `partner-card`
- `keyboard-route`
- `core-words`

## How the board works

- **My hero** (3x3): My hero is…, a firefighter, Speak, ABC, I think they are, Reasons ▶, Help, Undo, brave.
- **Reasons** (3x3): because, they help others, Speak, ◀ My hero, For example…, Core words ▶, Help, Undo, they rescue people.

The house standards tool added a **Core words** page (I, want, don't, like, go, more) that builds messages in the message bar, a **Word endings** page (-s, -ing, -ed, with Undo and Start again) and an **ABC keyboard** (QWERTY letter groups, then letters; Speak, Delete and Help on the keyboard page). Talking pages link forward with the right-middle button and back with the left-middle button; ABC sits left-middle on the first page.

- **House words:** Help is bottom-left on every page; Undo is bottom-middle wherever it appears; Speak is top-right on every page; ABC is left-middle of the first page. Page buttons: ▶ forward is right-middle, ◀ back is left-middle. Stop speech appears at the right edge while the board is talking. Each house word says the same message on every board.
- **Speech:** the board stays visible while it speaks; Stop speech appears at the right edge; a new selection interrupts.
- **Colour:** fills follow the Modified Fitzgerald Key by word type (for example green actions, blue describing words, pink social words, red help/stop words).

## Access

- Intended access: touch, keyboard, mouse, eye-gaze-dwell (profile `mixed-access`).
- At most 9 active targets per page; minimum target size 132 px.
- Dwell: 1100 ms; dwell re-arms only after the pointer leaves.
- Keyboard: Tab plus Enter/Space; Escape cancels dwell or stops speech.
- Print: browser print shows every page with scan numbers and a teacher/partner-card page.

## Communication purpose

A two-page sentence-builder board for a Year 7 English hero speech. The student adds words to a sentence bar, speaks the whole sentence, and uses opinion, reason, evidence, and repair language to rehearse a short spoken text.

## Symbols

16 of 20 different word and message buttons show a symbol; 16 of these were proposed by the agent and await team review. Letters and page buttons are text by design. Text-only words: My hero is…, For example…, don't, Space.

## Caveat

This is a draft classroom support. Review with the teaching/SLP/OT team and test on the actual student device, browser, access method and school environment before relying on it.

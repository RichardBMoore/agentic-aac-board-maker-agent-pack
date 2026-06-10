# Year 7 Hero Speech Sentence Builder

Generated from proof-of-concept fixture: `curriculum-sentence-builder` / "Make a Year 7 English hero speech sentence-builder board."

## Files

- `year7-hero-speech-sentence-builder.ir.json` - canonical AAC Board IR source of truth.
- `year7-hero-speech-sentence-builder.html` - single-file offline HTML student/player draft with a sentence bar, two pages, and a print stylesheet.
- `year7-hero-speech-sentence-builder.open-aac-studio.json` - Open AAC Studio-compatible renderer output created from the IR.
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

## How the board works

This is a genuine two-page sentence builder, not a single grid of words.

- **Sentence bar:** word buttons add to a running sentence shown at the top of the screen and speak the single word for feedback.
- **Speak sentence:** reads the whole built sentence aloud (present on both pages).
- **Undo / Start again:** Undo removes the last word; Start again clears the bar so the student can revise without losing agency.
- **Two pages, nine targets each:** Page 1 is sentence starters/connectives (My hero is, I think, because, For example, and also); Page 2 is describing words (brave, kind, helps others, never gives up) plus Undo, so the most recent word can be repaired on either page. Navigation buttons cross between them, so a gaze or switch user never faces more than nine targets at once.

## Access

- Intended access: touch, keyboard, mouse, eye-gaze-dwell.
- Density: nine targets per page (gaze-safe), navigation between pages instead of one dense grid.
- Minimum target size: 132 px.
- Dwell default: 1100 ms.
- Keyboard: Tab plus Enter/Space activates; Escape cancels dwell/speech.
- Print: use the browser print command; the print stylesheet shows both pages with headings.

## Communication purpose

A two-page sentence-builder board for a Year 7 English hero speech. The student adds words to a sentence bar, speaks the whole sentence, and uses opinion, reason, evidence, and repair language to rehearse a short spoken text.

## Teacher notes

- **Modelling:** Model a complete sentence chain across both pages: My hero is … brave … because … helps others, then press Speak sentence. Accept partial sentences as valid drafting or rehearsal.
- **Curriculum:** Supports Year 7 English speaking/listening by giving access to opinion, reasoning and evidence language for a short hero speech.
- **Customisation:** Replace the describing words and add the hero's name (as a word button or spoken after "My hero is") to match the class text, film, novel or local hero being studied.
- **Repair:** Keep Undo, Start again and Help please available so the student can fix or restart the sentence without losing agency.
- **Use:** Use for planning, rehearsal or supported oral presentation. Do not treat the board as the student's full expressive system.

## Caveat

This is a draft classroom support. Review with the teaching/SLP/OT team and test on the actual student device, browser, access method and school environment before relying on it.

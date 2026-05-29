# Secondary Needs and Communication Repair Board

Generated from proof-of-concept fixture: `needs-repair-board` / "Make a respectful needs and communication repair board for a secondary student."

## Files

- `secondary-needs-repair-board.ir.json` - canonical AAC Board IR source of truth.
- `secondary-needs-repair-board.html` - single-file offline HTML student/player draft with two pages and a print stylesheet.
- `secondary-needs-repair-board.open-aac-studio.json` - Open AAC Studio-compatible renderer output created from the IR.
- `teacher-notes.md` - teacher notes, evidence/customisation notes and caveats.

## Layout

Two gaze-safe pages with navigation between them, so no page shows more than nine targets:

- **Page 1 - I need:** Help please, I need a break, Wait, I feel unwell, I need privacy, Too loud, Finished, and a navigation button to page 2.
- **Page 2 - Sort it out:** Help please, Say it another way, Not that, Different, I disagree, Can I choose?, and a navigation button back to page 1.

Help please appears on both pages so support is never more than one selection away. All twelve self-advocacy and repair messages from the original single-page draft are preserved.

## Expected outputs covered

- `aac-board-ir`
- `html-or-printable-board`
- `teacher-notes`

## Required fixture checks addressed

- `age-respectful`
- `repair-language`
- `privacy-safe`
- `not-behaviour-control`

## Access

- Intended access: touch, keyboard, mouse, eye-gaze-dwell.
- Minimum target size: 132 px.
- Dwell default: 1100 ms.
- Keyboard: Tab plus Enter/Space. Escape cancels dwell/speech.
- Print: use the browser print command; the HTML includes a print stylesheet.

## Communication purpose

An age-respectful two-page needs and repair board that lets a secondary student request support, privacy, clarification, a break, different choices or communication repair without behaviour-control framing.

## Teacher notes

- **Modelling:** Model the board neutrally during calm moments, including how to move between the two pages. Treat selections as communication, not behaviour compliance.
- **Age Respectful:** Language is plain and secondary-appropriate. Avoid childish praise, token language or public commentary about private needs.
- **Privacy:** Do not log sensitive health, behaviour or family details in the file. Use separate approved school processes for confidential notes.
- **Repair:** Honour repair messages such as Not that, Different, Say it another way and Wait before repeating demands.
- **Use:** Use as a support for needs and communication repair, not as a behaviour-control board or replacement AAC system.

## Caveat

This is a draft classroom support. Review with the teaching/SLP/OT team and test on the actual student device, browser, access method and school environment before relying on it.

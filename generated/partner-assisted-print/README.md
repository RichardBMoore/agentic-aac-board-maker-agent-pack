# Partner-Assisted Scanning Print Board

Generated from proof-of-concept fixture: `partner-assisted-print` / "Make a printable partner-assisted scanning board for help, stop, different, finished, and choices."

## Files

- `partner-assisted-scanning-print-board.ir.json` - canonical AAC Board IR source of truth.
- `partner-assisted-scanning-print-board.html` - single-file offline HTML student/player draft with print stylesheet.
- `partner-assisted-scanning-print-board.open-aac-studio.json` - Open AAC Studio-compatible renderer output created from the IR.
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

## Access

- Intended access: partner-assisted-scanning, print, touch, keyboard, mouse.
- Minimum target size: 132 px.
- Dwell default: 1200 ms.
- Keyboard: Tab plus Enter/Space. Escape cancels dwell/speech.
- Print: use the browser print command; the HTML includes a print stylesheet.

## Communication purpose

A printable partner-assisted scanning board with clear scan order, wait/confirm script, help, stop, different, finished and choice messages.

## Teacher notes

- **Partner Script:** Partner says each option slowly in numbered order, waits, watches for the agreed signal, then confirms: I saw you choose __. Is that right?
- **Scan Order:** Scan left to right, top to bottom: 1 Help, 2 Stop, 3 Different, 4 Finished, 5 Choice A, 6 Choice B, 7 Yes, 8 No, 9 More time.
- **Wait Confirm:** Pause long enough for the student to respond. If unsure, repeat the scan or offer Yes/No confirmation without rushing.
- **Print:** Print in black and white if needed. Strong borders, large labels and numbered order are included for readability.
- **Attribution:** If adding symbols, record the symbol source and licence. Text-only printing is usable without symbols.

## Caveat

This is a draft classroom support. Review with the teaching/SLP/OT team and test on the actual student device, browser, access method and school environment before relying on it.

# Open AAC Studio Prototype

> Naming note: the user-facing name is "Open AAC Studio" (renamed from "Open Boardmaker" to avoid the Tobii Dynavox trademark). Internal identifiers - the folder name, `BoardmakerData` globals, `open-boardmaker.*` localStorage keys, and service-worker cache names - keep the historical name so existing saved boards still load.


Static, offline-friendly AAC board maker and player built from `boardmaker-clone-spec.md`.

## Run

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Open:

- Editor: http://127.0.0.1:4173/index.html
- Player: http://127.0.0.1:4173/player.html

## Current Classroom Slice

- Create/edit grid activities.
- Use classroom builder presets for quick boards.
- Undo/redo editor changes.
- Check board readiness before playing or printing.
- See an offline readiness banner for app cache and symbol-cache status.
- Use local word prediction while writing button labels.
- Convert labels into Symbolate-style word+symbol button content.
- Load starter templates.
- Search ARASAAC symbols online.
- Upload teacher-owned custom images.
- Save/load the current activity locally.
- Save reusable activities to the local library.
- Export/import JSON.
- Print boards with attribution.
- Play activities with mouse, touch, keyboard, dwell, TTS, linear switch scanning, and row-column switch scanning.
- Add per-button animation, media, variable, and conditional actions.
- Apply action presets for common classroom behaviours such as correct answer, wrong answer, score increment, and conditional next page.
- Switch player contrast between standard, high contrast, black-and-white, and yellow-on-black modes.
- Launch a laptop-first classroom player mode with lock, size presets, and full-screen support.
- Use skip links, labelled landmarks, synced page titles, announced dwell values, and a high-visibility dwell ring for access users.
- Keep compact boards at a 120px gaze-safe button floor unless a dense board intentionally needs more cells.
- Use curated high-contrast button fill and border swatches in the editor.
- Prepare ARASAAC symbols into an IndexedDB offline cache before a lesson.
- Install or deploy the player as a fullscreen PWA that launches directly to classroom mode.
- Save local student access profiles.
- Clear all local student profiles and session logs from the player.
- Log anonymous or student-specific attempts and export current activity results as CSV or a session report.

## Starter Templates

- Yes No Choice
- Choice Board 9
- Visual Schedule
- First Then
- Animal Book Reader
- Quiz 4

## Notes

Core use is local-first and does not require accounts. ARASAAC search and fresh ARASAAC image loads need internet; already loaded app files and browser-cached assets keep working offline through the service worker when served over localhost.

Browser security prevents any normal web page from forcing fullscreen on load, even on a managed school network. Use the `Start Classroom` button, browser kiosk mode, or the included PWA manifest (`display: fullscreen`, start URL `player.html?classroom=1`) for Education Queensland or similar managed deployments. Allowlist `https://api.arasaac.org` if staff need live symbol search on the school network.

See `DEPLOYMENT.md` for the classroom launch and pre-lesson checklist.

# Bundled Open Boardmaker Asset

The skill includes a reusable classroom editor/player prototype at:

`assets/open-boardmaker-classroom-pack/`

Use it when the user wants a Boardmaker-style local classroom tool, starter templates, offline symbol preparation, printable boards, a player mode, or a concrete codebase to adapt.

## Contents

- `index.html`: Editor.
- `player.html`: Student/classroom player.
- `css/editor.css`, `css/player.css`, `css/print.css`: Editor, player, and print styles.
- `js/data.js`: Activity schema defaults, local library, profiles, session logs, CSV export.
- `js/access.js`: Dwell controller and switch scanner.
- `js/player.js`: Student player rendering, TTS, lock/classroom mode, profiles, logs.
- `js/symbols.js`: ARASAAC search and IndexedDB symbol caching.
- `js/actions.js`: Speak, log, navigation, variables, conditional actions.
- `templates/*.json`: Yes/no, 9-choice board, first-then, visual schedule, book reader, quiz.
- `manifest.webmanifest` and `sw.js`: PWA and app shell caching when served from localhost.

## Local Trial

From a copy of the asset directory:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Open:

- Editor: `http://127.0.0.1:4173/index.html`
- Player: `http://127.0.0.1:4173/player.html`
- Classroom player: `http://127.0.0.1:4173/player.html?classroom=1`

## Patterns To Preserve

- Local-first operation with no accounts.
- JSON import/export for activities.
- Anonymous mode by default.
- Optional local student profiles.
- Clear Data path for shared devices.
- Dwell with visible progress and pointer-leave cancellation.
- Keyboard fallback.
- Linear and row-column switch scanning.
- TTS with Stop Speech.
- High contrast modes.
- Printable attribution.
- Offline readiness banner and symbol-cache preparation.

## When Adapting

- Copy the asset into the target project before modifying it.
- Remove unused editor features if building a one-off student resource.
- Preserve attribution and license fields when using ARASAAC symbols.
- Keep teacher controls separate from student/player controls.
- If launching from `file:///`, remember that service workers will not run. Prefer a single-file resource or local server/PWA setup.
- If a board is gaze-heavy, use the large AAC size and keep boards at 16 buttons or fewer unless the student/team has tested denser layouts.

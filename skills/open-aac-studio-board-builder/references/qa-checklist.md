# Open AAC Studio QA Checklist

Use this checklist before telling Richard a board or board-building workflow is ready.

## Data Integrity

- [ ] JSON parses without error.
- [ ] `schemaVersion`, `app`, `id`, `name`, `settings`, `accessibility`, `pages`, `metadata`, and `licences` are present.
- [ ] IDs are stable and do not contain private student information.
- [ ] Button positions fit the declared grid.
- [ ] Each button has a short label and at least speak/log actions unless intentionally silent.
- [ ] Multi-page navigation has stable Back/Next/Finished behaviour.

## Communication Quality

- [ ] Board supports at least one real communication function beyond labelling.
- [ ] Repair/agency vocabulary is present where appropriate.
- [ ] Labels are age-respectful and not infantilising.
- [ ] Curriculum boards include participation language such as think, because, help, question, choose, compare, explain, or reflect.
- [ ] Assessment boards avoid making the student only guess adult-selected answers.

## Access

- [ ] Intended access method is explicit.
- [ ] Target size is appropriate: 96px ordinary minimum, 120–200px for gaze-heavy boards.
- [ ] No routine scrolling is required in student/classroom mode for gaze boards.
- [ ] Visual order, DOM order, focus order, and scan order align.
- [ ] Keyboard activation works with Tab + Enter/Space.
- [ ] Dwell starts on pointer entry, shows progress, activates once, and cancels on leave.
- [ ] Switch scanning can start, step, select, and stop.
- [ ] High contrast and visible focus states are strong.
- [ ] Colour is not the only signal.

## Symbols And Media

- [ ] Text labels still work if images fail.
- [ ] ARASAAC or custom image attribution is included.
- [ ] No proprietary Boardmaker/PCS assets are copied.
- [ ] Custom photos are teacher-owned/local or explicitly approved.
- [ ] Remote URLs are avoided unless needed and trusted.
- [ ] Symbols can be prepared/cached before class where internet may fail.

## Classroom Safety

- [ ] Student/player mode is separate from teacher/editor controls.
- [ ] Destructive actions require confirmation or are not exposed in student mode.
- [ ] TTS can be stopped.
- [ ] Logging is minimal and anonymous by default.
- [ ] Export/print output does not reveal sensitive information.
- [ ] The board remains usable without internet, TTS, colour, or fine pointer precision.

## Verification Commands

Run local server when using the app:

```sh
cd skills/build-aac-student-supports/assets/open-boardmaker-classroom-pack
python3 -m http.server 4173 --bind 127.0.0.1
```

Then open:

- Editor: `http://127.0.0.1:4173/index.html`
- Player: `http://127.0.0.1:4173/player.html`
- Classroom player: `http://127.0.0.1:4173/player.html?classroom=1`

If producing a single-file gaze HTML instead, also run the checker from `build-aac-student-supports` when practical:

```sh
python3 skills/build-aac-student-supports/scripts/check_eye_gaze_html.py <file.html>
```

# SCORM Launch And Testing

## What SCORM is here

SCORM is a **packaging and runtime standard**, not hosting. A SCORM ZIP is the activity plus an `imsmanifest.xml` that tells the LMS what to launch. Canvas (QLearn) has a SCORM tool, an LTI app that the institution must enable. When it is enabled, a **SCORM** link appears in the course menu. A crossed-out eye means students cannot see the link, but teachers can still use it. Canvas supports SCORM 1.2 and SCORM 2004 (2nd–4th editions). A package can be imported **as a page**, a graded assignment or an ungraded assignment. The import type cannot be changed later. Deleting an item in the SCORM tool removes it from every place it appears in the course. Sources: Instructure guides "How do I import SCORM files as a page?" and "…as an assignment?", checked 21 October 2026.

A course showing a SCORM link proves only that the tool is exposed. It does **not** prove that upload is permitted for your role, that imports succeed, or that EQ policy approves active scripts for student use. Those are the things the first test records.

## What `build_scorm.py` produces

```text
imsmanifest.xml              SCORM 1.2 manifest: one organisation, one item, one SCO
index.html                   the original activity + one line loading the bridge
scorm/scorm12-bridge.js      LMSInitialize on open, LMSFinish on leave; nothing else
scorm/fullscreen-toggle.js   --fullscreen-toggle only: one Full screen / Exit full screen button; nothing else
licences/ARASAAC-symbols-LICENCE.md   when the board embeds ARASAAC symbols
package-info.json            source sha256, layout, bridge settings, extra pages, how to verify
<other pages>.html           multi-page activities only (--page): each gets the bridge, one session across pages
assets/inline-*.js|css       split layout only
```

- **No data leaves the activity.** The bridge never calls `LMSSetValue` unless the package was built with `--report-completion`, and even then only `cmi.core.lesson_status = completed`. Selections, messages and logs stay in the browser tab. Some players record a launch status of their own when a session closes; that is the LMS, not the activity.
- **Graceful outside an LMS.** Opened from a file, the bridge finds no API and the board behaves exactly like the standalone file (`window.AACScorm.status().mode === "standalone"`).
- **Deterministic.** The same input gives the same ZIP on the same Python/zlib build. `validate_scorm.py --source` proves the launch page is the original file plus only the bridge line.
- **Split layout safety.** The split layout keeps every attribute (ids, media) and leaves JSON data blocks inline. It refuses (use inline instead) inline scripts marked `async`/`defer`, `<style>` blocks with an `id` that a script could rewrite, and `<style>`/`<script>` inside `<svg>`, `<math>`, `<template>`, `<noscript>`, `<title>` or `<textarea>`, where moving them would change behaviour. Inline `style="…"` attributes stay in place; a player that forbids inline styles would ignore them. The board stayed usable in the strict-CSP browser test.
- **Schema files.** The official SCORM 1.2 `.xsd` files are not bundled by default; Canvas and most players import without them. Add `--schemas-dir` if a player demands them.

## What can block features inside the player

| Feature | Why it might not work in QLearn | What the board does | How to test |
| --- | --- | --- | --- |
| Fullscreen | Every frame between QLearn and the activity must allow full screen for the next frame's address. QLearn's player (Rustici, `syd.scorm.canvaslms.com`) allows it for its content frame. A page that embeds the tool must use `allow="fullscreen *"`, because the launch changes the frame's address (see below). The page QLearn creates on import does not allow it | Boards announce "Full screen was blocked. The board is still ready to use." and stay usable. With `--fullscreen-toggle`, one ⛶ button fills the screen and comes back, and it is hidden where full screen is not allowed | Press it in Student View and on the device |
| Speech (text-to-speech) | Needs installed voices and a user action first (Start board counts). Usually allowed in frames | Prefers installed en-AU voices; reports failures in the status line | Sound check, then a symbol |
| Microphone / dictation | Each frame needs `allow="microphone"` plus permission; browser speech recognition may send audio to a cloud service | Not used by the current boards | Treat as unavailable until proven; always keep a non-speech route |
| Eye gaze (page dwell) | Works when the gaze cursor moves the Windows pointer over the frame | Dwell, cancel and re-arm run in the frame | Hover/dwell on the real Accent |
| OS dwell click (NuVoice) | Real clicks; should work | Click activation is first-class | Dwell-click each target |
| Keyboard | Focus must be inside the frame first (click once or Tab into it) | Native buttons; visible focus | Tab and Enter in Student View |
| Inline scripts | A strict player Content Security Policy can block inline `<script>`/`<style>` | Blank or unstyled page | Re-upload the `--layout split` package |
| Screen size | QLearn's menus take space; the frame is smaller than the window | The board needs 960 × 600 px of frame at full target size (browser-tested) | Note whether anything scrolls or is cut off |
| Saving progress | No storage is used; each launch starts fresh | Nothing to lose | — |

## Full screen toggle (`--fullscreen-toggle [POSITION]`)

Adds one line after the bridge line that loads `scorm/fullscreen-toggle.js`. The validator still proves the activity is otherwise byte-for-byte unchanged.

- **One compact button** (52 px square, the ⛶ icon). The words "Full screen" or "Exit full screen" appear while it is hovered, looked at or focused, and are also its accessible name. A status message announces each change. Escape also comes back.
- **What goes full screen.** Inside a same-site player (QLearn's), it makes the player's activity frame full screen, so a multi-page activity stays full screen while moving between its pages. Opened on its own, it uses the page itself.
- **No dead button.** If no frame chain allows full screen, the button is not shown.
- **Never in the activity's way.** Presses on the button are handled first and kept away from the activity, so a dwell, switch-scan or click guard can neither block it nor react to it. After a mouse, touch or dwell-click press, focus returns to where it was, so game keys keep working. It hides when printing. It sends and stores nothing.
- **Position:** `top-right` (default), `top-left`, `top-center`, `middle-right`, `middle-left`, `bottom-right`, `bottom-left` or `bottom-center`. Pick the spot that covers none of the activity's own controls. Check the opening screen *and* the screens in use, at lesson-embed size (about 674 × 760) and full size. `middle-right` is easiest to find in a tall embed.
- **Leave it off** when an activity already has a complete full screen toggle (one that enters *and* exits), such as the arcade games. Two buttons for one job only confuses.

## Embedding a SCORM tool inside a lesson page

"Import as page" gives a page whose body is one `<iframe>` to `/courses/<id>/external_tools/retrieve?borderless=true&url=…/packages/<n>/launch`. The same iframe placed in a lesson shows the tool there. Write it as:

```html
<iframe title="Rule Lab" src="/courses/<id>/external_tools/retrieve?borderless=true&amp;url=https%3A%2F%2F…%2Flaunch" width="100%" height="760" style="width: 100%; height: 760px; border: 0; display: block;" loading="lazy" allow="fullscreen *; microphone *; clipboard-write *; autoplay *" allowfullscreen="true"></iframe>
```

The `*` matters: without it, full screen, copy buttons and the microphone are refused inside the tool. Use `%2F%2F` in the `url=` value. The API returns it damaged; see `canvas-allowlist-and-limitations.md`. Students' saved work lives in that browser for the player's address under QLearn, so the embedded tool and the imported page share it.

If fullscreen or space is the blocker, there are two options. Discuss them with the QLearn administrator first; neither is automated here. One is importing as an assignment and ticking "Load This Tool In A New Tab", which gives a full browser tab. The other is a separately approved hosted/LTI tool.

## Automated evidence in this repository

`browser-tests/scorm-package.spec.mjs` builds both layouts fresh and serves them inside a pretend course page → SCORM player → wrapper → content frame chain, with the API two frames up and the player on a different origin from the course page. It checks:

- one `LMSInitialize`, one `LMSFinish` and no data writes;
- Start board, touch/click, dwell, Stop speech;
- no requests outside the package;
- the board fits a 960 × 600 frame at full target size;
- fullscreen blocked by the course page is announced and harmless;
- the inline layout fails under `script-src 'self'; style-src 'self'` while the split layout works;
- the packaged file still works standalone.

These are **simulations**. They do not replace the upload test in `references/teacher-scorm-upload-guide.md` or a trial on the student's device.

## Updating a package

Re-run `build_scorm.py`, upload the new ZIP as a new import, check it, then delete the old item from the SCORM tool, which removes it everywhere. Keep the previous ZIP as the recovery copy.

---
name: qlearn-accessibility
description: "Use when a teacher wants accessible learning inside QLearn (Education Queensland's Canvas LMS) rather than as a downloaded file: (a) turning an existing QLearn page into an accessible, Canvas-safe UNPUBLISHED working copy via the Canvas REST API, or (b) packaging an existing validated standalone HTML/AAC/eye-gaze activity as a SCORM 1.2 ZIP for the teacher to upload through the course's SCORM tool. Owns the Canvas HTML allowlist, the SCORM packager/validator, least-privilege QLearn API access with the token kept in the OS password vault, and the teacher upload/test guide. Never publishes, never edits the original page, never reads student data."
license: MIT
metadata:
  hermes:
    tags: [qlearn, canvas-lms, scorm, accessibility, wcag, eye-gaze, aac, education-queensland]
    related_skills: [agentic-aac-board-maker, eyegaze-dwell-html, accent-display-fit, richard-school-resource-workflow]
---

# QLearn Accessibility

Accessibility should be part of the learning activity, not an extra file students have to find. This skill gets accessible content **into** QLearn by two routes and is honest about what each route can and cannot do.

It extends the pack; it does not replace anything. Boards are still designed and rendered by `../agentic-aac-board-maker/SKILL.md` (canonical IR → `render_html.py`). Gaze mechanics stay with `../eyegaze-dwell-html/SKILL.md`; device fit stays with `../accent-display-fit/SKILL.md`.

## Pick the output target first

| Target | Use for | What works | What does not |
| --- | --- | --- | --- |
| `canvas_page` | Text, instructions, links, images, tables, video embeds in an ordinary QLearn page | Headings, contrast, larger text and line spacing, big link targets, tables, Canvas media, iframes | Any script: dwell, buttons that do things, speech, sentence building. Canvas strips `<script>`, `<style>`, event handlers and form controls on save |
| `scorm` | An existing interactive HTML/AAC/eye-gaze activity students should use inside QLearn | The unchanged activity (dwell, touch, keyboard, speech, navigation) inside the SCORM player's frame | Guaranteed fullscreen, microphone/speech recognition, or every device: all depend on the player, browser and EQ policy and must be tested |
| `standalone` | Offline/USB/Accent delivery | Everything the pack already does | Living inside QLearn |

Do not put broken controls on a Canvas page. If a feature needs JavaScript, label it as SCORM-dependent and use the `scorm` target.

`references/canvas-allowlist-and-limitations.md` lists exactly what Canvas keeps. `references/architecture-decision.md` records why the design is additive.

## Non-negotiables

- **Never publish** anything and never send notifications. Everything is created unpublished. Treat published pages as read-only: to change one, make a new copy titled `… [WORKING FILE]`.
- **Never change the original page.** Only create new unpublished pages or update pages that are both unpublished and titled `[WORKING FILE]`.
- **Ask the teacher before every write**, and before deleting anything (this skill's client cannot delete; the teacher deletes in QLearn).
- **Course content only:** pages, modules, assignment/quiz descriptions, discussion topics, files. Never read students, enrolments, submissions, grades, discussion replies, messages or analytics. `scripts/canvas_client.py` only reads an allowlist of course-content addresses on the two QLearn hosts, so everything else is refused. Anything read is sent to the AI provider.
- **The token never passes through the agent.** It lives in the OS password vault (`keyring`, service `qlearn-token`, account `qlearn`) and is read by code at request time. Never ask for it, print it, log it, write it to a file, put it in a package or paste it into chat. If a teacher pastes it into chat, do not use it: tell them to delete it in QLearn (Account → Settings → Approved Integrations) and make a new one.
- **Keep every word, link and image** unless the teacher says otherwise. Restyling is presentation only. If something cannot survive Canvas, stop and ask; never drop it silently.
- **No identifiable student information** in packages, fixtures, logs, file names or the public repository. Use anonymous slugs.
- **Read back after every change** and report exactly what survived.
- Australian English.

`references/qlearn-approval-and-privacy.md` covers approvals and data handling.

## Workflow A: accessible, Canvas-safe working copy of a QLearn page

1. **Find it (read-only).** `python3 scripts/canvas_client.py courses`, then `pages COURSE_ID`. Confirm the course and page with the teacher. Course ids come from the API, never guessed from a URL.
2. **Fetch the body.** `python3 scripts/canvas_client.py get-page COURSE_ID PAGE_URL --out original.html`.
3. **Convert.** `python3 scripts/render_canvas_safe.py original.html accessible.html --report report.json`. It keeps only allowlisted HTML/CSS, copies simple `<style>` rules inline, fixes heading order under the page title, replaces low-contrast colours, enlarges small text and stand-alone links, and checks that every word, link, image and media item survived. Content hidden with `display:none`, script-only buttons that went somewhere, and colours it changed are reported for the teacher. Exit 2 means **NEEDS TEACHER** items (missing alt text, base64 images, unsupported embeds, form fields): resolve them with the teacher; never invent alt text.
4. **Show the teacher** a local preview of `accessible.html` and the CHANGED / CHECK / NEEDS TEACHER summary. Wait for an explicit yes.
5. **Create the unpublished copy** only after that yes: `python3 scripts/canvas_client.py create-working-copy COURSE_ID PAGE_URL accessible.html --confirm --saved-out saved.html`. The client posts `published: false`, titles it `<original title> [WORKING FILE]`, reads it back and stops loudly if it is somehow published.
6. **Verify what survived.** `python3 scripts/compare_saved_canvas_page.py accessible.html saved.html --source original.html`. Report lost content as a failure and stripped styles as warnings. Do not call the copy validated if any FAIL remains.
7. **Hand over** the QLearn link, the summary, and `references/accessibility-acceptance-checks.md` items the teacher must check by eye or with students (colour meaning, reading order, keyboard and screen-reader pass).

Further edits go to the same working copy with `update-working-copy … --confirm` (refused for published or unmarked pages). The teacher publishes, swaps it into modules and deletes old versions in QLearn.

## Workflow B: SCORM-packaged interactive activity

1. **Start from a validated standalone file.** For AAC boards, that means the pack's normal path: IR, house standards, `render_html.py`, parity and the browser suite. Never hand-edit a rendered board to package it.
2. **Package.** `python3 scripts/build_scorm.py board.html dist/board.scorm12.zip`. The launch page is the original file plus one line loading `assets/scorm12-bridge.js` (copied into the package as `scorm/scorm12-bridge.js`). The bridge only calls `LMSInitialize` and `LMSFinish`, never sends selections, messages or scores, and does nothing outside an LMS. `--report-completion` (off by default) marks the activity completed when opened. The ZIP is deterministic for a given Python build.
3. **Validate.** The builder runs `scripts/validate_scorm.py` automatically. Run it yourself on any third-party package: `python3 scripts/validate_scorm.py package.zip --source board.html`. It checks the manifest, ZIP hygiene, that every asset resolves inside the package, that nothing loads from the internet, that there are no tokens or API endpoints, the IR privacy flags, and (with `--source`) byte-for-byte equivalence with the original.
4. **Backup layout.** If the activity is blank or unstyled inside QLearn, the player's Content Security Policy is probably blocking inline scripts. Rebuild with `--layout split`: scripts and styles move into files with every attribute kept, and the builder refuses the few cases where moving would change behaviour (async/defer inline scripts, named style blocks, styles or scripts inside SVG, maths or templates). `browser-tests/scorm-package.spec.mjs` proves the split layout runs under `script-src 'self'; style-src 'self'`.
5. **Teacher uploads and tests.** Give the teacher `references/teacher-scorm-upload-guide.md` (upload as a page, preview, student view, device checklist, results sheet). The agent does not automate SCORM import: a Files API upload is not a SCORM import.
6. **Record real outcomes.** Do not claim fullscreen, speech, microphone or eye-gaze work in QLearn until the results sheet says so on the student's real device. `references/scorm-launch-and-testing.md` explains what can block each one.

## Scripts

- `scripts/canvas_client.py`: least-privilege QLearn client (keyring token, two hard-coded QLearn hosts, allowlisted course-content reads, unpublished working-file writes only, `--confirm`).
- `scripts/render_canvas_safe.py`: accessible Canvas-safe restyle with a preservation inventory.
- `scripts/compare_saved_canvas_page.py`: what Canvas kept after saving.
- `scripts/build_scorm.py`: deterministic SCORM 1.2 packager (`inline` or `split` layout).
- `scripts/validate_scorm.py`: SCORM 1.2 package validator and source-equivalence proof.
- `templates/scorm12_manifest.xml`, `templates/accessible_canvas_page.html`, `templates/canvas-safe-styles.json`: editable templates and the house page look (contrast-checked).

## Verification in this repository

`tests/test_scorm_packaging.py`, `tests/test_canvas_safe.py` and `tests/test_canvas_client.py` (stubbed API, synthetic fixtures), `browser-tests/scorm-package.spec.mjs` (nested-frame LMS harness, cross-origin fullscreen block, strict CSP), and the `check_pack.py` release gate (packages every generated board and scans the repository for secrets).

## Handoff caveat

Packaging and validation prove the files are correct; they do not prove QLearn's SCORM player, EQ browser policy or the student's Accent will allow fullscreen, speech or gaze inside the frame. Call every QLearn delivery a draft until the teacher's upload test and an on-device trial with the student and team are recorded.

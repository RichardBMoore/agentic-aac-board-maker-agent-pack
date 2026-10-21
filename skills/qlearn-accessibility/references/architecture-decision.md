# Architecture Decision: QLearn Accessibility Extension

Status: proposed on branch `feature/qlearn-accessibility-scorm` (21 October 2026). Version 0.10.0.

## Audit of the existing pack (real files, 0.9.0)

- **Skills (7):** `agentic-aac-board-maker` (canonical IR 0.5.0, house standards, deterministic renderers), `eyegaze-dwell-html`, `accent-display-fit`, `build-aac-student-supports`, `open-aac-studio-board-builder`, `icp-backwards-mapping-assessment`, `richard-school-resource-workflow`. Both plugin manifests expose `./skills/`, so a new folder is picked up without manifest restructuring.
- **One shared runtime.** `skills/agentic-aac-board-maker/assets/aac-board-runtime.js` (543 lines) is embedded verbatim by `render_html.py`; `validate_html_parity.py` enforces HTML/IR/runtime parity. The runtime makes **no network calls and uses no browser storage**. It finds its data with `document.getElementById("aac-board-ir")`. Fullscreen uses `requestFullscreen()` with an announced fallback.
- **Generated boards (7)** are single self-contained files (75–415 KB): inline `<style>`, an inline JSON IR block, the inline runtime, base64 symbols, and no inline event handlers.
- **QA:** `scripts/check_pack.py` (140 release checks), 108 unit tests, 96 Playwright tests across three viewport projects plus the Accent display spec, CI with check-pack/browser/plugin-validate jobs, a PostToolUse validation hook and the `aac-board-qa` reviewer agent.
- **Baseline before any change (21 October 2026):** release check exit 0, 108/108 unit tests, 96/96 browser tests.

## Decisions

1. **Additive skill.** New `skills/qlearn-accessibility/`. No changes to existing skills, the runtime, renderers, schema, hooks or generated fixtures.
2. **Wrap the rendered output instead of adding a renderer branch.** A SCORM package's launch page is the rendered board's exact bytes plus one `<script>` line before `</body>`. Packaging therefore cannot change board behaviour: `validate_scorm.py --source` reverses it byte-for-byte, and the packaged page still passes `validate_html_parity.py`. Any standalone activity (not only IR boards) can be packaged the same way.
3. **SCORM 1.2 first.** Canvas supports 1.2 and 2004. 1.2 is the simplest, most widely supported runtime, and this proof of concept needs no tracking data.
4. **Minimal bridge, no data.** `LMSInitialize`/`LMSFinish` only. Completion is opt-in and never sends answers, messages or logs. With no LMS present the bridge does nothing.
5. **Two layouts.** `inline` is closest to the tested file. `split` moves inline CSS/JS into files for players with a strict Content Security Policy; it is browser-tested under `script-src 'self'; style-src 'self'`.
6. **Output-target contract.** `canvas_page` (static, allowlisted, restyled, preservation-checked), `scorm` (interactive, packaged), `standalone` (unchanged existing output). LTI/hosted delivery is deferred until tests show SCORM is insufficient **and** EQ approves.
7. **Least privilege in code.** The QLearn client refuses student endpoints, foreign hosts, publishing, deleting and any write except creating/updating unpublished working copies, and needs explicit confirmation. The token comes from the OS vault at call time.
8. **Repository conventions over the handoff's suggested layout.** Tests live in the top-level `tests/` and `browser-tests/` folders (discovered by CI) rather than inside the skill.

## Consequences and limits

- SCORM import is a **manual teacher step**. No supported API for Canvas's SCORM LTI is assumed, and a Files API ZIP upload is not a SCORM import.
- Fullscreen, speech, microphone and gaze inside QLearn's real player and EQ-managed browsers are **unverified** until the teacher's upload test and an on-device trial.
- Official SCORM `.xsd` files are not bundled; `--schemas-dir` adds them if a player requires them.
- Canvas page restyling cannot add interactivity; interactive needs are routed to SCORM.

## Next phases

- **Phase 1 (now):** teacher uploads the gaze-choice package to a sandbox course and fills in the results sheet.
- **Phase 2:** read-only fetch of one real page → `render_canvas_safe.py` → teacher preview → unpublished `[WORKING FILE]` copy → `compare_saved_canvas_page.py`.
- **Phase 3:** agent UX for batches (dry-run and diff), module placement suggestions, version tracking and rollback notes.
- **Phase 4 (only if SCORM falls short):** a precise request to EQ ICT / the QLearn administrator for an approved LTI or hosted route.

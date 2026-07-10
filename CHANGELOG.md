# Changelog

All notable changes to this project will be documented in this file.

## 0.5.0 - 2026-07-08

Platform-feature and symbol-pipeline release.

- ARASAAC symbol pipeline: new `skills/agentic-aac-board-maker/scripts/fetch_arasaac_symbols.py` fills IR buttons with real pictograms via the free ARASAAC API (deterministic best-match selection preferring exact keyword and AAC-flagged pictograms), setting `symbolId` and embedding `symbolSrc` as a base64 data URI so boards stay single-file and offline-capable after a one-time fetch. Refuses to run without the required ARASAAC attribution in the IR; misses and download failures keep the text fallback and are reported per button. Supports `--ids-only`, `--overwrite`, `--locale`, `--resolution` (300/500/2500) and an optional download cache. Overwrite mode clears stale embedded image data when a replacement image is intentionally omitted or cannot be downloaded. 13 focused symbol tests; 56 tests total.
- Claude Code hooks: `hooks/hooks.json` registers a `PostToolUse` hook (`hooks/validate_board_outputs.py`) that auto-runs the IR validator on written `*.ir.json` and the strict eye-gaze checker on written dwell HTML, surfacing failures back to the agent (exit 2) so QA no longer depends on the agent remembering to run it. Relative paths resolve against the hook payload working directory, while missing validators, launch failures, and timeouts fail closed. Thirteen deterministic hook tests cover routing and failure behavior.
- Claude Code subagent: `agents/aac-board-qa.md`, an independent fresh-eyes QA reviewer (validators first, then rubric/anti-pattern review; review-only, never edits) with an always-on "not testable here" honesty section.
- Marketplace install: `.claude-plugin/marketplace.json` makes the repo a single-plugin marketplace so `/plugin marketplace add` + `/plugin install` work, enabling clean version updates.
- Skill routing: `build-aac-student-supports` and `eyegaze-dwell-html` descriptions now say which sibling skill owns end-to-end board generation vs dwell HTML mechanics, reducing wrong-skill triggering when all six descriptions are loaded together.
- Release gate: new `check_release_metadata` check enforces version consistency across both plugin manifests, the marketplace entry, and the CHANGELOG; parses hooks.json and syntax-checks referenced hook scripts; and requires name/description frontmatter on shipped agents.
- CI: test matrix covers Python 3.10 and 3.12; strict Claude plugin validation is a blocking release gate using Node.js 20 and a pinned Claude Code CLI version.

## 0.4.1 - 2026-06-10

Completes every item from 0.4.0's "Known follow-ups" list.

- Generated HTML interaction pass (all six boards): one-time Sound check control with spoken-feedback error handling (Chromium/Edge block `speechSynthesis` until user activation, which hover-only eye-gaze never grants); assistive-technology clicks (`event.detail === 0`) now activate buttons; an 800 ms post-dwell click-suppression window prevents dwell+click double activation; the redundant custom Enter/Space keydown branch is gone (native buttons fire click); consistent `prefers-reduced-motion` dwell rendering everywhere.
- `partner-assisted-print` no longer auto-activates on hover: all dwell machinery is removed from the HTML and IR, honouring the board's own `dwellSafe: false` partner-assisted design.
- Classroom-pack player implements the message-bar actions (`add-to-message`, `speak-message`, `remove-last-word`, `clear-message`) with the accumulator reset on load, so sentence-builder exports now work end to end; in-page branding finished its "Open AAC Studio" rename (internal storage keys keep the historical name for saved-board compatibility, noted in the asset README).
- Eye-gaze template and `templates.md`: the global post-activation cooldown no longer swallows the next dwell on a different button (the `eyegaze-dwell-html` SKILL.md snippet got the same fix); the confirmation modal moves focus in and back out, cancels on Escape, ignores background activations while open, and the `templates.md` snippet now ships its previously missing CSS. The template and `templates.md` snippet also adopt the plain click listener already documented in `eyegaze-dwell-html`: the `event.detail !== 0` guard (which silently dropped synthesised assistive-technology clicks) and the redundant custom Enter/Space keydown branch are gone, with Escape keeping its cancel-dwell role.
- README now explicitly documents the pack as both Codex-ready and Claude Code-ready, including the separate `.codex-plugin/` and `.claude-plugin/` manifests and shared namespaced skill usage.
- Docs: QCIA headings renamed to QCAA's five official curriculum organisers (CT, CCE, LR, PLD, VTA); "Other Open Symbol Sources" added (Mulberry, Sclera, OpenMoji, Global Symbols; Smarty Symbols flagged proprietary) with the ARASAAC `resolution=2500` print tip; teacher intake asks for an age band; single-file HTML requirements gained aria-live / Sound check / Label-in-Name / reduced-motion / focus-not-obscured bullets; `source-notes.md` cites the pictogram terms page (arasaac.org/terms-of-use) instead of the tutorial-materials page; `open-aac-studio-schema.md` documents the actual renderer output fields, the message-bar actions, and the private-prototype disambiguation (OBF is the interoperable path).

## 0.4.0 - 2026-06-10

Whole-pack audit and upgrade: every change below traces to an independently verified finding or to current-source research (Codex plugin spec, Open Board Format spec, ARASAAC terms, PRC-Saltillo NuVoice documentation, WCAG 2.2).

### Added

- Open Board Format export: new `skills/agentic-aac-board-maker/scripts/render_obf.py` renders the canonical IR to `.obf` (single page) or `.obz` (multi-page, with manifest), importable by CoughDrop, Cboard, AsTeRICS Grid, OptiKey, PiCom, and Pasco. Every generated pack now ships an OBF export, navigation maps to `load_board`, message-bar actions map to `:speak`/`:clear`/`:backspace`, ARASAAC images carry per-image CC BY-NC-SA license blocks, and unsupported settings travel as `ext_aac_*` attributes.
- `.claude-plugin/plugin.json` so the pack installs as a first-class plugin in Claude Code as well as Codex (Codex reads both manifests; Claude reads only its own). README documents the namespaced invocation (`$agentic-aac-board-maker:<skill-name>`).
- Release gate now verifies shipped `.open-aac-studio.json` and `.obf`/`.obz` exports byte-match a fresh render of their IR (timestamps normalised; renderers honour `SOURCE_DATE_EPOCH`), requires `teacher-notes.md` per generated pack, runs the strict eye-gaze checker on every generated dwell HTML, checks WCAG 2.5.3 Label-in-Name on button aria-labels, resolves dwell target sizes from CSS instead of substring matching, checks Codex's 64-char name / 1024-char description skill limits and the 3x128-char `defaultPrompt` ceiling, and scans every markdown file for broken reference paths.
- Validator: duplicate page ids and board-wide duplicate button ids now fail; `navigate-page` actions must target a real page; `denseGazeTested` must be boolean `true` (truthy strings no longer lift the gaze density limit); gaze/dwell profiles must declare a numeric `minimumTargetSizePx` >= 120 (the missing/zero bypass is closed); declared-vs-realised `communicationFunctions` drift and `messageBar`/action inconsistencies now warn.
- Renderer: preserves per-button `style`/`font` from the IR (semantic colour coding no longer lost in exports), preserves a distinct `audioCue`, emits both `targetPageId` and `pageId` on `navigate-page` for player compatibility, accepts `"speak"`/`"log"` string shorthands, defaults `minimumTargetSizePx` to 120 for dwell profiles, and no longer crashes on non-numeric grid/margin/dwell values.
- Bundled classroom-pack player reads `targetPageId` on navigation (matching the documented IR contract), and its service worker scopes runtime caching to same-origin requests (opaque cross-origin ARASAAC responses were costing ~7 MB of quota each). Implementing the message-bar actions in the player remains a known follow-up; the renderer and OBF export already handle them.
- Test suite grew from 11 to 30 tests: validator regression cases for every new rule, renderer style/audioCue/navigation/determinism tests, real CLI subprocess tests, and OBF structure/round-trip tests.

### Changed

- Generated HTML fixtures: aria-labels verified to contain the visible label text (WCAG 2.5.3 Label in Name, now enforced by the release gate; the Speak-sentence labels were corrected). Known follow-ups documented for a future pass: a one-time Sound check control (Chromium/Edge block `speechSynthesis` until user activation, which hover-only eye-gaze never grants), removing the `event.detail !== 0` click guard that blocks assistive-technology clicks, a post-dwell click-suppression window, and consistent `prefers-reduced-motion` dwell rendering.
- `curriculum-sentence-builder`: Undo is now available on both pages (one example adjective gave way), so the most likely error - a wrong word added on page 2 - is repairable without wiping the sentence.
- `gaze-choice-2x2`: now ships teacher-notes.md (required by the release gate), and its README/IR claim only the communication functions its buttons actually realise.
- ARASAAC attribution (symbol-strategy reference, skeleton template, renderer default, all six fixture IRs and exports) now uses ARASAAC's required wording naming the author Sergio Palao, owner Government of Aragon, origin, and unversioned CC BY-NC-SA; README gains an MIT-vs-symbol-licence note (generated boards embedding pictograms stay CC BY-NC-SA and must not be sold).
- Dwell guidance harmonised across all skills to one canonical statement: start 800-1200 ms (800 ms matches the PRC-Saltillo NuVoice factory default for Accent eye tracking, now cited), 1000-1500 ms for accidental-activation risk, below 800 ms for confident users only, outside 500-1500 ms a team/SLP decision; dwell time should be teacher-adjustable at runtime.
- Eye-gaze guidance: the 9-target page limit is documented as a conservative starting default (with the 200 px+ gaze-target research), WCAG citations corrected (2.4.13 marked AAA with 1.4.11 as the AA basis; 2.5.7 Dragging Movements and 2.4.11 Focus Not Obscured added), and the high-contrast palette clarified for text vs non-text use.
- `eyegaze-dwell-html` code patterns made safe: the section 8 confirmation pattern no longer constructs a DwellManager per call (the stale `onConfirm` closures re-fired earlier answers); it now uses one manager, a single pending callback, focus management, and Escape-to-cancel. Audio cues are documented as opt-in.
- Classroom-pack web-app manifest renamed (its `short_name` was literally Tobii Dynavox's "Boardmaker" trademark; now "Open AAC Studio" / "AAC Studio"). Renaming the remaining in-page "Open Boardmaker" branding is a known follow-up; internal storage keys keep the historical name for compatibility.
- Skill metadata: all six `agents/openai.yaml` starter prompts drop the unnamespaced `$skill` mentions that break under plugin namespacing; the two yaml files missing `brand_color`/`policy` gained them; the ICP skill's display name matches its actual name.
- Docs accuracy sweep: agent-workflow's Phase 3 skeleton is valid JSON with the validator-required fields; role/function enums match the validator everywhere ("ask" not "question", "regulate-rest"); the QA rubric's gaze red flag matches the enforced 9-target rule; examples match the shipped fixtures (both the rebuilt sentence builder and the real qcia-community-shops vocabulary); `aac-board-ir.md` documents the 0.4.0 validator/renderer rules and the OBF export; the Autism Speaks citation is replaced with NCAEP/AFIRM and behaviour-control framing removed; the dead ACARA student-diversity link is fixed; "non-verbal" replaced with "non-speaking"; machine-specific paths removed from the QA checklist; CI pins Python 3.12 with read-only permissions.

## 0.3.0 - 2026-05-29

- Rebuilt the `curriculum-sentence-builder` proof of concept as a genuine two-page sentence builder: a running sentence/message bar, Speak sentence / Undo / Start again controls, and `navigation` buttons. It now delivers the multi-page and rehearse/speak behaviour the evaluation fixtures already expected, instead of speaking single words in isolation.
- Split the `needs-repair-board` proof of concept into two gaze-safe pages (no more than nine targets each) with navigation and Help on every page, preserving all twelve self-advocacy and repair messages. This removes a dense 12-target grid that contradicted the eye-gaze density guidance.
- Closed a gaze-density validation gap in `validate_board_ir.py`: boards that list `eye-gaze-dwell`/`mouse-dwell` in `access.intended` under a non-gaze profile (for example `mixed-access`) now warn when a page exceeds nine targets without `denseGazeTested`, matching the anti-patterns and access-density evidence. Added a `mixed_gaze_dense` regression fixture and test.
- These two generated examples are the first to exercise multi-page navigation and the renderer's `next-page`/`previous-page` actions, so the regression fixtures now cover navigation as well as single-page boards.
- Documented the optional `messageBar` and `navigation` IR objects and the multi-page density rule in `aac-board-ir.md`, and aligned `skills/agentic-aac-board-maker/references/examples.md` with the shipped sentence builder.

## 0.2.0 - 2026-05-25

- Added `icp-backwards-mapping-assessment` for ICP backwards maps, adapted assessments, rubrics, evidence packages, teaching sequences, and moderation notes.
- Refreshed `build-aac-student-supports` from the Inclusive Education Toolkit plugin.
- Refreshed `eyegaze-dwell-html` with the current single-file dwell HTML guidance for PRC-Saltillo Accent devices and Education Queensland network constraints.
- Updated plugin metadata and README coverage for ICP and broader inclusive education workflows.

## 0.1.0 - 2026-05-16

- Prepared the Agentic AAC Board Maker pack as a private GitHub working repo.
- Added Codex plugin metadata, skill folders, generated proof-of-concept resources, validation scripts, and GitHub release checks.
- Kept generated boards as regression fixtures for AAC Board IR validation and Open AAC Studio rendering.
- Added privacy guidance for de-identified classroom resource drafting.

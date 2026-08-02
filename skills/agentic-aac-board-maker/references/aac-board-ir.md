# AAC Board Intermediate Representation

AAC Board IR is the renderer-independent source of truth created before HTML, Open AAC Studio JSON, OBF/OBZ or print output. It forces the resource to state communication purpose, access, system fit, button semantics, repair, symbols, privacy and evidence before visual rendering.

## Version And Schema

Canonical output is `schemaVersion: "0.4.0"` with `format: "agentic-aac-board-ir"`. Validate it with `references/aac-board-ir.schema.json`.

Legacy 0.2/0.3 inputs remain readable through:

```sh
python3 scripts/canonicalize_board_ir.py legacy.ir.json canonical.ir.json
```

Canonicalisation removes renderer aliases such as `app`, top-level `name`, `settings`, `accessibility`, page `gridRows/gridColumns`, `metadata` and `licences`. Renderers also canonicalise legacy input internally, but committed/new IR files must already be canonical (`--check`).

## Required Shape

Use `templates/board-json-skeleton.json` as the complete editable starter. Canonical IR requires:

- safe `id`, `title`, `purpose`, audience age/tone/locale;
- access methods/profile, target size, dwell/scan settings and total visible/setup target limits;
- display and student-control configuration;
- declared communication functions;
- pages with canonical `grid.rows/columns` and globally unique button ids;
- each button's label, role, function, spoken text, search term, symbol fields/layout and action objects;
- teacher notes and `systemFit` review fields;
- symbol strategy with text fallback and review policy;
- privacy and attribution.

Optional SETT, UDL, differentiation, participation barriers and evidence-plan metadata are strongly expected for curriculum/QCIA resources.

## Controlled Values

Access profiles:

- `direct-selection`, `eye-gaze-dwell`, `mouse-dwell`, `single-switch`, `two-switch`;
- `partner-assisted-print`, `partner-assisted-scanning`, `print-only`, `keyboard`, `mixed-access`, `unspecified`.

Button roles:

- `core`, `fringe`, `repair`, `navigation`, `comment`, `question`, `sentence`, `evidence`, `teacher`.

Communication functions:

- `initiate`, `request`, `refuse`, `choose`, `comment`, `ask`, `answer`, `sequence`, `explain`, `repair`, `reflect`, `socialise`, `navigate`, `regulate-rest`.

Canonical actions are objects with a stable id and one of:

- speech/logging: `speak-text`, `speak-label`, `log-attempt`;
- navigation: `navigate-page`, `next-page`, `previous-page`;
- message building: `add-to-message`, `speak-message`, `remove-last-word`, `clear-message`;
- evidence: `mark-correct`, `mark-incorrect`.

String `"speak"`/`"log"` forms are legacy input only. New canonical output uses action objects.

## Total Active-Target Rules

Density means every simultaneously active student target—not declared grid cells and not vocabulary buttons alone. Count setup, navigation, message, speech and other utility controls whenever active.

- Gaze/dwell defaults to 2×2, 2×3 or 3×3; no more than nine active board targets unless `denseGazeTested` is boolean `true` after actual device testing.
- Gaze/dwell requires `minimumTargetSizePx >= 120`, an integer dwell time and immediate pointer-leave/focus-loss cancellation.
- Setup is a separate phase with `setupTargetLimit` (three by default).
- During speech, the canonical HTML renderer hides/inerts other student targets so Stop Speech is the only active target.
- Switch boards start with small predictable sets; larger sets require fatigue-aware scanning design.
- Direct-selection defaults to 3×3; 4×4 is appropriate only when access supports it.

The semantic validator compares page target totals with `visibleTargetLimit`. Browser QA reads the live `window.AACBoard.auditVisibleTargets()` result so hidden/active state is verified rather than inferred from grid size.

## System Fit

`systemFit` prevents a generated board from pretending to be a complete student system. Record:

- review status (`team-input-needed`, `team-reviewed`, `student-trialled`);
- relationship to the established AAC/low-tech system;
- familiar vocabulary and stable motor/location patterns;
- symbol/text/photo familiarity;
- access calibration and reliable cancellation;
- screen, mount, seating, vision, contrast and fatigue;
- language, culture and speech voice;
- reliable partner-interpreted yes/no, repair and refusal signals.

Keep unresolved items explicit and test them with the student/team on the actual setup.

## Multi-Page And Message Behaviour

Use navigation-role/function buttons with explicit actions. `navigate-page` must name a real `targetPageId`; next/previous actions follow page order. Keep repair/help reachable on each page.

Sentence builders use a top-level `messageBar` plus real message actions. The bar displays the current message; controls can be board buttons so gaze pages do not silently gain extra active targets.

## Symbol Review

`searchTerm` is a query, not an approved semantic match. Recommended workflow:

```sh
python3 scripts/fetch_arasaac_symbols.py board.ir.json --review-out symbol-review.json
# reviewer records approvedSymbolId choices from the companion contact sheet
python3 scripts/fetch_arasaac_symbols.py board.ir.json --apply-review symbol-review.json --out board.reviewed.ir.json
```

Review meaning, student familiarity, culture, language and visual recognisability. Leave `approvedSymbolId` null to keep text fallback. `--auto-select` is an explicit opt-in, not the default.

## Renderer Mapping And Integrity

### Single-file HTML

Generate with:

```sh
python3 scripts/render_html.py board.ir.json board.html
python3 scripts/validate_html_parity.py board.ir.json board.html
```

The deterministic HTML contains:

- the complete canonical IR payload;
- semantic buttons and exact button/action metadata;
- inline/offline CSS and the exact shared `assets/aac-board-runtime.js`;
- keyboard, click, dwell, message, navigation, TTS/Stop Speech and target-audit behaviour;
- teacher/attribution content outside normal student mode plus print styling.

Never hand-edit generated HTML. Change IR or the shared runtime and re-render. Parity and byte-drift checks fail if HTML labels/actions/pages, embedded IR or runtime differ.

### Open AAC Studio JSON

`scripts/render_open_aac_studio.py` maps title/name, access/settings, grid aliases and attribution/licences only in the target export. IR roles/functions and extended design metadata are preserved where the target supports them.

### Open Board Format

`scripts/render_obf.py` writes `.obf` for one page or `.obz` for multiple pages. Navigation maps to `load_board`; message actions map to supported OBF commands; ARASAAC ids carry attribution/licence information.

## Validation Failures

Fail IR that has malformed/duplicate ids, missing required semantic fields, empty/overfull grids, dangling navigation, incompatible gaze target size/density, no repair route on a substantive board, noun/quiz-only design without agency, absent privacy/attribution, or total active targets above the declared limit.

Warnings still require review before claiming the resource is student-ready—for example thin SETT/UDL/evidence metadata, declared/realised communication-function drift or an untested intended gaze path.

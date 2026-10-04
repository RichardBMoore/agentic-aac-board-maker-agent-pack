# Agentic AAC Board Maker Agent Pack

Agentic AAC Board Maker is a Codex- and Claude Code-ready skill pack for generating draft AAC boards and classroom communication resources from teacher intent.

The project turns hidden board-making judgement into agent-readable rules: communication rights, core and fringe vocabulary, access methods, symbol strategy, curriculum/QCIA translation, privacy, offline classroom constraints, and release QA.

## Vision

Teacher intent in; evidence-informed, accessible AAC draft resource out.

This is not "AI inside a board maker." It is a workflow for AI as the draft board maker, governed by explicit AAC, access, curriculum, and privacy rules. Human educator, SLP, OT, family, and student judgement still sit above classroom use.

## What This Repository Contains

```text
agentic-aac-board-maker-agent-pack/
  .claude-plugin/            Claude Code plugin manifest and marketplace listing
  .codex-plugin/             Codex plugin manifest
  agents/                    Claude Code subagents (independent board QA reviewer)
  hooks/                     Claude Code hooks (auto-validate boards on write)
  .github/workflows/         GitHub validation workflow
  generated/                 Proof-of-concept boards and regression fixtures
  scripts/                   Repository validation script
  skills/                    Skill folders exposed by the plugin
  browser-tests/             Real interaction/device-viewport Playwright QA
  tests/                     IR/schema/renderer/parity/symbol/evaluation unit tests
```

The main skill is:

```text
skills/agentic-aac-board-maker/SKILL.md
```

It coordinates the core workflow:

```text
teacher intent
  -> communication functions
  -> canonical AAC Board IR
  -> house standards (fixed places for key words, shared word list, spelling/core-word pages, symbols, colour, partner card)
  -> deterministic HTML, print, partner card, Open AAC Studio JSON, OBF/OBZ, or resource pack
  -> schema + parity + browser + fresh-output QA
```

## Quick Start

Install development checks, then run the release gate:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
npm ci
.venv/bin/python scripts/check_pack.py
```

Canonicalise legacy IR and verify canonical 0.5.0 output:

```sh
python3 skills/agentic-aac-board-maker/scripts/canonicalize_board_ir.py legacy.ir.json board.ir.json
python3 skills/agentic-aac-board-maker/scripts/canonicalize_board_ir.py board.ir.json --check
```

Apply house standards (idempotent; `--check` for release gates):

```sh
python3 skills/agentic-aac-board-maker/scripts/apply_house_standards.py board.ir.json
python3 skills/agentic-aac-board-maker/scripts/apply_house_standards.py board.ir.json --check
```

Render the one-page communication partner card:

```sh
python3 skills/agentic-aac-board-maker/scripts/render_partner_card.py board.ir.json partner-card.html
```

Review the house symbol set once as a team:

```sh
python3 skills/agentic-aac-board-maker/scripts/review_house_symbols.py --review-out house-symbol-review.json
python3 skills/agentic-aac-board-maker/scripts/review_house_symbols.py --apply-review house-symbol-review.decisions.json
```

Validate a generated AAC Board IR:

```sh
python3 skills/agentic-aac-board-maker/scripts/validate_board_ir.py generated/qcia-community-shops/qcia-community-shops.ir.json
```

Render Open AAC Studio-compatible JSON from an IR file:

```sh
python3 skills/agentic-aac-board-maker/scripts/render_open_aac_studio.py generated/qcia-community-shops/qcia-community-shops.ir.json /tmp/qcia-community-shops.open-aac-studio.json
```

Render and parity-check deterministic offline HTML:

```sh
python3 skills/agentic-aac-board-maker/scripts/render_html.py board.ir.json board.html
python3 skills/agentic-aac-board-maker/scripts/validate_html_parity.py board.ir.json board.html
```

Generate ARASAAC candidates for review, then apply only approved choices:

```sh
python3 skills/agentic-aac-board-maker/scripts/fetch_arasaac_symbols.py board.ir.json --review-out symbol-review.json
python3 skills/agentic-aac-board-maker/scripts/fetch_arasaac_symbols.py board.ir.json --apply-review symbol-review.json --out board.reviewed.ir.json
```

Export an Open Board Format board from an IR file:

```sh
python3 skills/agentic-aac-board-maker/scripts/render_obf.py generated/qcia-community-shops/qcia-community-shops.ir.json /tmp/qcia-community-shops.obf
```

Generated packs now ship `.obf`/`.obz` files importable by CoughDrop, Cboard, AsTeRICS Grid, and OptiKey.

Run unit, fresh-output and installed-Chrome interaction tests:

```sh
.venv/bin/python -m unittest discover -s tests
.venv/bin/python skills/agentic-aac-board-maker/scripts/evaluate_fresh_output.py generated
npm run test:browser:chrome
```

## Install In Claude Code

The repo doubles as a single-plugin marketplace (`.claude-plugin/marketplace.json`), so it can be installed and updated with the plugin manager:

```text
/plugin marketplace add <path-or-git-url-of-this-repo>
/plugin install agentic-aac-board-maker@agentic-aac-board-maker-marketplace
```

Installing the plugin also activates two automation layers that standalone skill copies do not have:

- A `PostToolUse` hook that automatically runs the IR validator on any written `*.ir.json` and the strict eye-gaze checker on any written dwell HTML, feeding failures straight back to the agent for repair.
- An `aac-board-qa` subagent for independent fresh-eyes QA of a generated board before it is presented as a draft.

## Codex And Claude Code Use

The repository root is the plugin folder for both supported agent hosts:

- Codex reads `.codex-plugin/plugin.json`.
- Claude Code reads `.claude-plugin/plugin.json`.
- Both manifests expose the same shared skill folders under `./skills/`.

Install or check out the whole repository folder so the manifest, skills, scripts, templates, generated examples, and tests stay together. In plugin-aware agents that namespace skills, use the pack name with the skill name, for example `$agentic-aac-board-maker:agentic-aac-board-maker` or `$agentic-aac-board-maker:eyegaze-dwell-html`.

## Standalone Skill Use

Each skill folder also remains usable on its own:

- `agentic-aac-board-maker` - main workflow for direct AI-generated AAC boards and resource packs.
- `open-aac-studio-board-builder` - Open AAC Studio and Boardmaker-style compatibility layer.
- `build-aac-student-supports` - broader AAC, symbol, print, offline HTML, QCIA, and classroom access patterns.
- `eyegaze-dwell-html` - single-file eye-gaze and dwell-activated HTML support, including fullscreen-first launch and managed Edge/EQ deployment guidance.
- `accent-display-fit` - display fidelity on real Accent devices and EQ-managed Edge: effective-viewport maths (Windows scaling, NuVoice Key Mode, Empower browser), fit-first layout rules, conservative engine baseline, OneDrive/USB delivery routes, and a display-fit validator.
- `icp-backwards-mapping-assessment` - ICP backwards mapping, adapted assessment, rubrics, moderation notes, and evidence design.
- `richard-school-resource-workflow` - Richard's broader school-resource workflow context.

## What 0.9.0 changes in the boards

- Speech keeps the board visible; Stop speech sits at the right edge; a resting gaze no longer cuts off or repeats the student's message; new selections interrupt.
- Help, Different, Finished, Stop/Speak, page buttons and ABC have permanent places on every board, and recurring words always say the same thing.
- Every board (except tiny early-choice boards, which record why) reaches a spelling keyboard, core words and, for older students, word endings.
- House words carry symbols from a proposed house set the team reviews once; colour means word type; a CVI profile is available.
- Each board ships with a partner card; community boards open with How I talk; speech prefers installed voices; an opt-in selection log separates student selections from partner models; schedules show Now / Next / Done.

See `skills/agentic-aac-board-maker/references/house-standards.md`.

## Output quality in 0.8.0

Native touch/keyboard activation works independently of dwell. Standalone HTML rejects switch-scanning configurations; use a verified scanning player for those requests. Symbol-review sheets support offline previews and downloadable revision-bound decisions. HTML/OBF preserve aligned grid cells; print supports A4/A3 portrait/landscape and scan numbers. See `skills/agentic-aac-board-maker/references/output-quality.md` for capabilities and acceptance checks.

## Generated Examples

The `generated/` folder is intentionally kept in the repo. These examples are demonstrations and golden regression fixtures. The release check validates canonical IR against JSON Schema, fresh-renders HTML/Open AAC Studio/OBF outputs, and enforces HTML/IR/shared-runtime parity. `evaluate_fresh_output.py` separately checks new candidate generations so golden fixtures cannot mask weak new output.

Included proof-of-concept examples (each folder also has `partner-card.html`):

- `gaze-choice-2x2` - simple 2x3 eye-gaze choice board with symbols; keyboard omitted with a recorded reason (early choice board).
- `qcia-community-shops` - QCIA community access board: Shop talk and Paying pages, How I talk introduction, ABC keyboard, core words, word endings and an example opt-in selection log.
- `curriculum-sentence-builder` - Year 7 hero speech sentence builder: starters and hero words linked forward and back, a message bar, core words, word endings and an ABC keyboard so the student can spell their own hero.
- `visual-schedule-expressive` - morning routine with Now / Next / Done states, Finished moving the schedule on, and a Talk about it page.
- `needs-repair-board` - respectful needs and repair board for a secondary student; two gaze-safe pages plus core words, word endings and keyboard.
- `partner-assisted-print` - printable partner-assisted scanning board (Talk and Choices pages) with the generated pages printable for partner-assisted spelling.
- `symbol-shape-choice` - original embedded geometric symbols for offline rendering QA; learner familiarity remains unverified.

All examples follow the house standards: the same house words sit in the same places and say the same messages on every board.

## Non-Negotiables

- Do not treat this as clinical AAC assessment or a replacement for SLP/OT/team judgement.
- Do not copy proprietary Boardmaker/PCS assets.
- Do not reduce AAC to quiz answering or adult compliance.
- Preserve student agency: initiate, refuse, repair, comment, ask, choose, answer, explain, stop, and finish where appropriate.
- Match board density and interaction style to the access method.
- Keep privacy and offline classroom use in mind.
- Use open/free symbols or teacher-owned media with attribution. The bundled house symbols are ARASAAC pictograms under CC BY-NC-SA (not MIT); keep attribution and do not sell boards that embed them.
- Keep the canonical AAC Board IR as the source of truth and apply house standards before rendering.
- Review symbol candidates with the student/team; do not treat search ranking as semantic approval.
- Prefer fullscreen student mode for eye gaze; use the page's gaze-safe launcher normally and EQ-managed Edge policy or kiosk deployment when fullscreen must be automatic or enforced.
- Run QA before claiming a board is ready even as a draft.

## Privacy And Release Status

This repository contains only de-identified examples and should remain free of real student names, diagnoses, behaviour records, medical details, family details, school IDs, or unnecessary site-specific information.

Generated resources are draft classroom supports. Review them with the relevant education and allied-health team, test with the actual student, device, access method, browser, and classroom environment, and adjust locally before relying on them.

## Useful Review Path

1. `skills/agentic-aac-board-maker/SKILL.md`
2. `skills/agentic-aac-board-maker/references/evidence-base.md`
3. `skills/agentic-aac-board-maker/references/research-map.md`
4. `skills/agentic-aac-board-maker/references/house-standards.md`
5. `skills/agentic-aac-board-maker/references/agent-workflow.md`
6. `skills/agentic-aac-board-maker/references/aac-board-ir.md`
7. `skills/agentic-aac-board-maker/references/board-grammar.md`
8. `skills/agentic-aac-board-maker/references/access-methods.md`
9. `skills/agentic-aac-board-maker/references/curriculum-qcia-translation.md`
10. `skills/agentic-aac-board-maker/references/qa-rubric.md`
11. `skills/icp-backwards-mapping-assessment/SKILL.md`

## License

MIT. See `LICENSE`.

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
  -> deterministic HTML, print, Open AAC Studio JSON, OBF/OBZ, or resource pack
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

Canonicalise legacy IR and verify canonical 0.4.0 output:

```sh
python3 skills/agentic-aac-board-maker/scripts/canonicalize_board_ir.py legacy.ir.json board.ir.json
python3 skills/agentic-aac-board-maker/scripts/canonicalize_board_ir.py board.ir.json --check
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

## Generated Examples

The `generated/` folder is intentionally kept in the repo. These examples are demonstrations and golden regression fixtures. The release check validates canonical IR against JSON Schema, fresh-renders HTML/Open AAC Studio/OBF outputs, and enforces HTML/IR/shared-runtime parity. `evaluate_fresh_output.py` separately checks new candidate generations so golden fixtures cannot mask weak new output.

Included proof-of-concept examples:

- `gaze-choice-2x2` - simple eye-gaze choice board.
- `qcia-community-shops` - QCIA community access board.
- `curriculum-sentence-builder` - Year 7 hero speech sentence builder; a two-page board with a sentence/message bar and Speak/Undo/Start-again controls.
- `visual-schedule-expressive` - visual schedule with expressive options.
- `needs-repair-board` - respectful needs and repair board; two gaze-safe pages with Help on each.
- `partner-assisted-print` - printable partner-assisted scanning board.

The `curriculum-sentence-builder` and `needs-repair-board` examples also demonstrate multi-page `navigation` buttons (`next-page`/`previous-page` actions), so the regression fixtures cover navigation as well as single-page boards.

## Non-Negotiables

- Do not treat this as clinical AAC assessment or a replacement for SLP/OT/team judgement.
- Do not copy proprietary Boardmaker/PCS assets.
- Do not reduce AAC to quiz answering or adult compliance.
- Preserve student agency: initiate, refuse, repair, comment, ask, choose, answer, explain, stop, and finish where appropriate.
- Match board density and interaction style to the access method.
- Keep privacy and offline classroom use in mind.
- Use open/free symbols or teacher-owned media with attribution.
- Keep the canonical AAC Board IR as the source of truth.
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
4. `skills/agentic-aac-board-maker/references/agent-workflow.md`
5. `skills/agentic-aac-board-maker/references/aac-board-ir.md`
6. `skills/agentic-aac-board-maker/references/board-grammar.md`
7. `skills/agentic-aac-board-maker/references/access-methods.md`
8. `skills/agentic-aac-board-maker/references/curriculum-qcia-translation.md`
9. `skills/agentic-aac-board-maker/references/qa-rubric.md`
10. `skills/icp-backwards-mapping-assessment/SKILL.md`

## License

MIT. See `LICENSE`.

# Agentic AAC Board Maker Agent Pack

Agentic AAC Board Maker is a Codex-plugin-ready skill pack for generating draft AAC boards and classroom communication resources from teacher intent.

The project turns hidden board-making judgement into agent-readable rules: communication rights, core and fringe vocabulary, access methods, symbol strategy, curriculum/QCIA translation, privacy, offline classroom constraints, and release QA.

## Vision

Teacher intent in; evidence-informed, accessible AAC draft resource out.

This is not "AI inside a board maker." It is a workflow for AI as the draft board maker, governed by explicit AAC, access, curriculum, and privacy rules. Human educator, SLP, OT, family, and student judgement still sit above classroom use.

## What This Repository Contains

```text
agentic-aac-board-maker-agent-pack/
  .codex-plugin/             Codex plugin manifest
  .github/workflows/         GitHub validation workflow
  generated/                 Proof-of-concept boards and regression fixtures
  presentations/             Overview presentation for school workflow discussion
  prompts/                   Copy/paste prompts for agent review and build tests
  scripts/                   Repository validation script
  skills/                    Skill folders exposed by the plugin
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
  -> HTML, print, Open AAC Studio JSON, ICP evidence package, or resource pack
  -> validation and QA
```

## Quick Start

Run the release check:

```sh
python3 scripts/check_pack.py
```

Validate a generated AAC Board IR:

```sh
python3 skills/agentic-aac-board-maker/scripts/validate_board_ir.py generated/qcia-community-shops/qcia-community-shops.ir.json
```

Render Open AAC Studio-compatible JSON from an IR file:

```sh
python3 skills/agentic-aac-board-maker/scripts/render_open_aac_studio.py generated/qcia-community-shops/qcia-community-shops.ir.json /tmp/qcia-community-shops.open-aac-studio.json
```

## Plugin And Standalone Use

The repository root can act as a Codex plugin through `.codex-plugin/plugin.json`, which exposes every skill under `./skills/`.

Each skill folder also remains usable on its own:

- `agentic-aac-board-maker` - main workflow for direct AI-generated AAC boards and resource packs.
- `open-aac-studio-board-builder` - Open AAC Studio and Boardmaker-style compatibility layer.
- `build-aac-student-supports` - broader AAC, symbol, print, offline HTML, QCIA, and classroom access patterns.
- `eyegaze-dwell-html` - single-file eye-gaze and dwell-activated HTML support.
- `icp-backwards-mapping-assessment` - ICP backwards mapping, adapted assessment, rubrics, moderation notes, and evidence design.
- `richard-school-resource-workflow` - Richard's broader school-resource workflow context.

## Generated Examples

The `generated/` folder is intentionally kept in the repo. These examples are both demonstrations and regression fixtures. The release check validates every `generated/**/*.ir.json`, renders it to Open AAC Studio JSON, and checks that paired HTML/Open AAC Studio/README outputs exist.

Included proof-of-concept examples:

- `gaze-choice-2x2` - simple eye-gaze choice board.
- `qcia-community-shops` - QCIA community access board.
- `curriculum-sentence-builder` - Year 7 hero speech sentence builder.
- `visual-schedule-expressive` - visual schedule with expressive options.
- `needs-repair-board` - respectful needs and repair board.
- `partner-assisted-print` - printable partner-assisted scanning board.

## Non-Negotiables

- Do not treat this as clinical AAC assessment or a replacement for SLP/OT/team judgement.
- Do not copy proprietary Boardmaker/PCS assets.
- Do not reduce AAC to quiz answering or adult compliance.
- Preserve student agency: initiate, refuse, repair, comment, ask, choose, answer, explain, stop, and finish where appropriate.
- Match board density and interaction style to the access method.
- Keep privacy and offline classroom use in mind.
- Use open/free symbols or teacher-owned media with attribution.
- Keep the canonical AAC Board IR as the source of truth.
- Run QA before claiming a board is ready even as a draft.

## Privacy And Release Status

This repository is prepared as a private working repo. It should not contain real student names, diagnoses, behaviour records, medical details, family details, school IDs, or unnecessary site-specific information.

Generated resources are draft classroom supports. Review them with the relevant education and allied-health team, test with the actual student, device, access method, browser, and classroom environment, and adjust locally before relying on them.

## Useful Review Path

1. `skills/agentic-aac-board-maker/SKILL.md`
2. `skills/agentic-aac-board-maker/references/evidence-base.md`
3. `skills/agentic-aac-board-maker/references/agent-workflow.md`
4. `skills/agentic-aac-board-maker/references/aac-board-ir.md`
5. `skills/agentic-aac-board-maker/references/board-grammar.md`
6. `skills/agentic-aac-board-maker/references/access-methods.md`
7. `skills/agentic-aac-board-maker/references/curriculum-qcia-translation.md`
8. `skills/agentic-aac-board-maker/references/qa-rubric.md`
9. `skills/icp-backwards-mapping-assessment/SKILL.md`

## License

MIT. See `LICENSE`.

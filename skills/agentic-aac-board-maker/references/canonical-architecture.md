# Canonical Architecture

Use this file to keep the pack coherent as it becomes both a Codex plugin and a set of standalone skills.

## Product Shape

The project has three deliverable surfaces:

1. **Codex plugin** — the repository root acts as the plugin root and exposes `./skills/` through `.codex-plugin/plugin.json`.
2. **Standalone skills** — each folder under `skills/` remains copyable/installable as an independent `SKILL.md` skill.
3. **Generated classroom resources** — single-file HTML, printable HTML/Markdown, portable JSON, and resource packs generated from teacher intent.

The product is not the prototype editor. The prototype remains a reference implementation and compatibility target.

## Source Of Truth

`agentic-aac-board-maker` owns:

- teacher-intent intake;
- communication-rights and AAC design rules;
- canonical AAC Board IR;
- output contract selection;
- final QA rubric;
- generated-resource delivery language.

`open-aac-studio-board-builder` owns:

- Open AAC Studio / Open Boardmaker compatibility;
- prototype schema details;
- import/export behaviour;
- app-specific JSON fields and player/editor assumptions.

`build-aac-student-supports` owns:

- broader AAC/student-support build patterns;
- bundled reusable editor/player asset;
- general activity schema and classroom deployment lessons;
- shared accessibility/privacy defaults for AAC supports.

`eyegaze-dwell-html` owns:

- single-file offline dwell HTML implementation patterns;
- PRC-Saltillo/Edge/EQ file-launch constraints;
- dwell manager, target sizing, viewport fit, and high-stakes confirmation details.

`richard-school-resource-workflow` owns:

- Richard-specific school-resource ethos;
- ICP/QCIA/curriculum preservation patterns outside pure AAC board generation;
- multi-AI handoff and governance context.

## Generation Pipeline

For direct generation, use this pipeline:

```text
teacher request
  -> intake assumptions / clarifying question only if needed
  -> communication functions
  -> canonical AAC Board IR
  -> renderer choice
       -> single-file HTML
       -> printable board
       -> Open AAC Studio JSON
       -> full resource pack
  -> validation scripts + QA rubric
  -> draft classroom support with real-device/team caveat
```

Do not let an agent jump straight from teacher request to visual grid. The IR step is the guardrail against pretty, weak communication boards.

## Duplication Rules

When the same rule appears in multiple files, keep the canonical wording in the owning file and link to it elsewhere.

- Communication rights, agency, core/fringe, aided language, and board grammar belong in `agentic-aac-board-maker`.
- Dwell timing, pointer cancellation, and single-file HTML mechanics belong in `eyegaze-dwell-html`.
- Prototype JSON quirks belong in `open-aac-studio-board-builder`.
- Bundled editor/player use belongs in `build-aac-student-supports`.
- School workflow and ICP/QCIA beyond board generation belong in `richard-school-resource-workflow`.

## Compatibility Policy

The canonical AAC Board IR is the design source. Other formats are renderer outputs.

- **Open AAC Studio JSON** should preserve the IR's communication functions, roles, access settings, privacy metadata, and attribution where the app schema supports them.
- **Single-file HTML** should embed or inline what it needs for the classroom context and should not require the prototype app.
- **Printable boards** should preserve scan/pointing order, labels, symbol search terms, attribution, and partner notes.

## Release Gates

Before treating a generated resource as ready for classroom draft use:

1. The IR validates.
2. The renderer output opens or parses.
3. Access method assumptions match density and controls.
4. The QA rubric is green or explicitly caveated amber.
5. The final response says it is a draft classroom support pending real student/device/team testing.


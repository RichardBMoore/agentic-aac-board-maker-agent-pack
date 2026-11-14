---
name: agentic-aac-board-maker
description: "Use when an AI agent should directly generate evidence-informed AAC boards or classroom communication resources from teacher intent, without requiring a board-maker app. Covers intake, AAC evidence principles, board grammar, symbol strategy, access methods, curriculum/QCIA translation, output contracts, QA, and final resource delivery."
license: MIT
metadata:
  hermes:
    tags: [aac, agentic-ai, board-generation, communication-rights, core-vocabulary, aided-language, qcia, curriculum, eye-gaze, switch-scanning, print, offline-html]
    related_skills: [open-aac-studio-board-builder, build-aac-student-supports, eyegaze-dwell-html, accent-display-fit, richard-school-resource-workflow]
---

# Agentic AAC Board Maker

## Overview

Use this skill when the goal is **teacher intent in → accessible AAC board/resource out**.

Richard's larger vision is not to make teachers operate another board-maker interface. The Open AAC Studio / Boardmaker-style web app is a reference laboratory: it reveals the board grammar, access rules, symbol workflows, player behaviours, and QA checks that an AI agent needs. The agent should be able to directly generate a usable board/resource pack as HTML, JSON, Markdown, printable layout, or other classroom-ready output.

This skill turns AAC board-making into an agent workflow. It must keep student communication rights, communicative competence, access method, curriculum participation, privacy, and classroom practicality ahead of visual polish.

## Non-Negotiables

- Do not present outputs as clinical AAC assessment or SLP/OT replacement.
- Preserve student agency: boards should let students initiate, refuse, repair, comment, ask, choose, answer, explain, and reflect where appropriate.
- Do not reduce AAC to adult-controlled quiz answering or behaviour compliance.
- Use Australian English unless asked otherwise.
- Use open/free symbols such as ARASAAC or teacher-owned media; do not copy proprietary Boardmaker/PCS assets.
- Keep sensitive student information out of prompts, filenames, logs, generated examples, and external services unless explicitly approved.
- Prefer local-first, offline-capable, printable outputs for school use.

## Tools And Board Files

Paths in this skill that begin with scripts/, references/ or templates/ are relative to this skill's folder, the one that holds this `SKILL.md`. Run the scripts by their full path; they work from any working directory.

- `scripts/build_board.py` builds a whole pack from one file and reports what still needs work. It is the gate for every board on every host, including hosts that do not run plugin hooks.
- `scripts/inspect_board.py` prints a board as a short outline: each page as a grid, every button's words, role, word class and symbol status, and a "Needs attention" list.

A board has three kinds of file:

| File | What it is | How to handle it |
| --- | --- | --- |
| `<name>.source.json` | The small file you write (about 5 KB) | Read and edit freely |
| `<name>.ir.json` | The built board: canonical IR with house standards and embedded pictures (often 300-450 KB, about 80% base64) | Never open with Read, `cat` or an editor. View with `scripts/inspect_board.py`. Change the source and rebuild |
| `<name>.html`, `partner-card.html`, `<name>.obz` | Renders | Never hand-edit. Rebuild |

The same applies to the example boards in the repository's `generated/` folder: inspect them, do not open them. A board made before source files existed has only an `.ir.json`; rebuild it in place with `scripts/build_board.py <name>.ir.json`.

## Reference Routing

Read these files based on task type:

- `references/evidence-base.md` — AAC/UDL/visual-support principles that must shape generation.
- `references/research-map.md` — source map and 2026-05-26 practice grounding for AAC, access, differentiation, and evidence.
- `references/canonical-architecture.md` — plugin/standalone skill architecture and ownership boundaries.
- `references/aac-board-ir.md` — canonical AAC Board IR used before rendering any output.
- `references/aac-board-ir.schema.json` — executable JSON Schema for canonical IR 0.5.0.
- `references/house-standards.md` — house layout, shared word list, literacy pages, symbol set, colour, partner card, voice, logging and schedules; read before building any board.
- `references/house-layout.json`, `references/house-lexicon.json`, `references/house-settings.json` — the editable house data applied by `scripts/apply_house_standards.py`.
- `references/anti-patterns.md` — weak board patterns to detect and repair before delivery.
- `references/release-checklist.md` — plugin/standalone skill release gates and validation commands.
- `references/agent-workflow.md` — end-to-end workflow for direct agent generation.
- `references/intake-and-decision-tree.md` — how to infer/ask for missing board requirements.
- `references/board-grammar.md` — board patterns, page structures, button roles, and communication functions.
- `references/symbol-and-vocabulary-strategy.md` — core/fringe vocabulary, ARASAAC/custom media, attribution, privacy.
- `references/access-methods.md` — touch, keyboard, eye gaze/dwell, switch scanning, print/partner-assisted design rules.
- `references/curriculum-qcia-translation.md` — convert curriculum/QCIA tasks into communication moves.
- `references/output-quality.md` — renderer capabilities, symbol completion, stable grid positions and task-level acceptance.
- `references/output-contracts.md` — expected shapes for HTML, JSON, printable boards, and resource packs.
- `references/prompt-recipes.md` — reusable prompts for board generation and self-critique.
- `references/qa-rubric.md` — final checks before returning a resource.
- `references/examples.md` — canonical examples and expected agent behaviour.
- `references/evaluation-fixtures.md` — the six benchmark prompts used to regression-test the pack itself (not a gate for an ordinary new board).
- `templates/teacher-intake.md` — concise user-facing intake form when clarification is genuinely needed.
- `templates/board-json-skeleton.json` — the starter source file: copy it to `<name>.source.json` and edit.
- `templates/single-file-html-requirements.md` — required properties for direct HTML output.

Load `eyegaze-dwell-html` only when eye gaze/dwell is explicit. Load `accent-display-fit` whenever an Accent or EQ-managed Edge target is explicit; pair both specialists when that target also uses gaze/dwell. Load `open-aac-studio-board-builder` only for explicit prototype/schema compatibility. Do not fan out to specialist skills merely because the board is “accessible”.

## Default Agent Workflow

1. **Clarify only if needed.** If the request has enough context, proceed with sensible defaults. Ask only when missing information changes the output materially: access method, board purpose, output format, or privacy-sensitive details.
2. **Identify the communication goal.** Convert the teacher task into communication functions: initiate, choose, request, refuse, repair, comment, ask, sequence, explain, reflect.
3. **Select a board pattern.** Choose from yes/no, choice board, first-then, visual schedule, core/fringe board, quiz/comprehension, sentence builder, story/book reader, needs/repair, or curriculum participation board.
4. **Write the board as a small source file before any visuals.** Copy `templates/board-json-skeleton.json` to `<name>.source.json`. Write what needs judgement: pages and grids; each button's `id`, `label`, `role`, `function`, `wordClass` and `searchTerm` (plus `spokenText` when it differs from the label); `access`; `audience`; a `partnerCard` (3-5 model words, wait time, comment examples); teacher notes; `systemFit`; SETT/UDL/differentiation and evidence needs. Leave out what the tools add: the wording, symbols and positions of house words, the ABC keyboard, core words and word endings pages, navigation buttons, colours, speech and logging defaults, and the actions of ordinary speak buttons. Add house words by label alone (`{"id": "btn-help", "label": "Help"}`). Check `references/house-lexicon.json` before choosing a label: a label that matches a house word (Why, Wait, More, Stop, Yes, No...) takes the house message and behaviour, so give your own phrase a different label ("Why did that happen?").
5. **Build it with one command.** `python3 scripts/build_board.py <name>.source.json --out-dir <pack-folder>`. It applies house standards, validates the board (canonical form, JSON Schema, communication and access rules), renders the offline HTML board, the partner card and an OBF/OBZ export, checks HTML/IR parity, eye-gaze rules and screen fit, then prints an outline of the finished board with a "Needs attention" list. Exit status 1 means the pack is not ready. Add `--formats html,partner-card,obf,open-aac-studio` only for explicit Open AAC Studio compatibility. `--paper A3 --orientation portrait` changes the print layout.
6. **Fix in the source file and rebuild until the build passes.** Read the build output, not the built files. A page that is too full: split the page; never shrink targets below the access minimum. "Screen fit" failing: the page is taller than the screen and the bottom row (Help, Different, Finished) is cut off, so use fewer rows or the target size the message gives; three rows with a message bar allow at most 132 px. Pass `--display-floor WIDTHxHEIGHT` only when the team has confirmed the device's real viewport, and say so in the handover. "Your wording was replaced": relabel the button. Then work through the TO DO lines.
7. **Review symbols as candidates.** House words already carry the house symbol set (proposed or team-approved; see `references/house-standards.md`). For this board's own words run `scripts/fetch_arasaac_symbols.py <pack-folder>/<name>.ir.json --review-out <pack-folder>/symbol-review.json` (needs internet). A teacher/team reviewer chooses from the contact sheet; apply the decisions with `--apply-review`, then run `scripts/build_board.py <pack-folder>/<name>.ir.json` to re-render. Later rebuilds from the source keep those reviewed symbols (matched by button id, label and search term). Keep text fallback. Use `--auto-select` only when the user explicitly accepts automated semantic selection.
8. **Get a fresh-eyes review and run real QA.** Where the host has subagents (Claude Code: the `aac-board-qa` agent), hand the pack folder to one that did not build it. Otherwise review it yourself from `scripts/inspect_board.py <ir> --all` against `references/qa-rubric.md` and `references/anti-patterns.md`. Count every active student target, including setup, navigation and stop controls, not only vocabulary cells. Run browser/device tests where available. `scripts/build_board.py <ir> --check` re-verifies a pack without changing it.
9. **Return usable files and honest caveats.** Include where the files were saved, what the board supports, the build's remaining "Needs attention" items, what was not checked (real device, voice, symbol familiarity, print pagination), unresolved `systemFit` items, and what can be customised (the source file).

The individual scripts (`scripts/apply_house_standards.py`, `scripts/validate_board_ir.py`, `scripts/render_html.py`, `scripts/render_partner_card.py`, `scripts/render_obf.py`, `scripts/render_open_aac_studio.py`, `scripts/validate_html_parity.py`, `scripts/canonicalize_board_ir.py` for legacy input) still work on their own; `build_board.py` runs them in the right order. `scripts/evaluate_fresh_output.py` scores the pack's six benchmark prompts only and is not a check for a new board.

## Output Defaults

When the user does not specify output:

- For classroom digital use: create a single self-contained HTML file.
- For Open AAC Studio import/testing: create app-compatible JSON rendered from the canonical IR.
- For low-tech use: create printable HTML or Markdown with symbols/search terms and attribution.
- For complex curriculum tasks: create a resource pack with IR JSON, rendered HTML/print output, teacher notes and the partner card.
- Every board: house standards applied, a partner card, speech settings that prefer an installed voice, and the selection log off unless the team has agreed its purpose.

## Definition Of Done

A generated AAC board is ready only when it is:

- **Evidence-informed:** aligned with communication rights, communicative competence, aided language/core vocabulary principles, and UDL action/expression.
- **Communication-rich:** includes more than content labels or quiz answers, and reaches spelling and core words unless an omit reason is recorded.
- **Consistent:** house words sit at their house addresses and say the house message; colour means word type.
- **Access-real:** designed for the stated access method and usable by keyboard as a baseline.
- **Curriculum-strong:** preserves learning intent while reducing access barriers.
- **Privacy-safe:** no unnecessary student identifiers or sensitive notes.
- **Offline/print-aware:** text fallback, attribution, and practical classroom deployment are addressed.
- **Verified:** `scripts/build_board.py` passes, every page fits the screen it is for, and the board is checked against `references/qa-rubric.md`.

## Fast Response Pattern

When Richard asks for a build, give a short plan, then build unless he clearly asked for planning only. Keep summaries practical:

1. What I made.
2. Where the file is.
3. Access features.
4. Curriculum/communication intent.
5. What still needs real student/device testing.

## Common Failure Modes

- Pretty board, weak communication.
- Too many buttons for eye gaze or switch scanning.
- No Help/Stop/Different/Finished pathway.
- Quiz board where the student only guesses adult answers.
- Teacher controls mixed into student mode.
- AI-generated personalisation using sensitive student details.
- External images/scripts that fail on school networks.
- No attribution for symbols.
- No way for the teacher to adapt vocabulary after generation.
- Multiple schemas drifting apart instead of rendering from the canonical IR.
- Opening a built `*.ir.json` or generated HTML directly, or hand-editing either, instead of inspecting, editing the source and rebuilding.
- Targets made larger without checking the page still fits: the bottom row is cut off, and that row is Help, Different and Finished.
- A phrase button whose label is a house word, silently turned into the house message.
- Help (or any house word) in a different place, or saying something different, from one board to the next.
- Phrase-only boards with no way to spell or combine words.
- Decorative colour that does not mean word type.
- Text-only boards shipped to students who do not read, when reviewed symbols are available.
- Missing SETT/UDL/differentiation/evidence metadata while claiming the resource is differentiated.
- Noun-grid, quiz-only, compliance-first, or adult-voice boards that look polished but reduce student agency.

## Maintenance Note

This skill should absorb lessons from the Open AAC Studio prototype and from real classroom builds. When a generated board fails QA or a better pattern emerges, patch the relevant reference file rather than only fixing one board.

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

## Reference Routing

Read these files based on task type:

- `references/evidence-base.md` — AAC/UDL/visual-support principles that must shape generation.
- `references/research-map.md` — source map and 2026-05-26 practice grounding for AAC, access, differentiation, and evidence.
- `references/canonical-architecture.md` — plugin/standalone skill architecture and ownership boundaries.
- `references/aac-board-ir.md` — canonical AAC Board IR used before rendering any output.
- `references/aac-board-ir.schema.json` — executable JSON Schema for canonical IR 0.4.0.
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
- `references/evaluation-fixtures.md` — proof-of-concept fixtures for regression testing the skill stack.
- `templates/teacher-intake.md` — concise user-facing intake form when clarification is genuinely needed.
- `templates/board-json-skeleton.json` — portable board data skeleton.
- `templates/single-file-html-requirements.md` — required properties for direct HTML output.

Load `eyegaze-dwell-html` only when eye gaze/dwell is explicit. Load `accent-display-fit` whenever an Accent or EQ-managed Edge target is explicit; pair both specialists when that target also uses gaze/dwell. Load `open-aac-studio-board-builder` only for explicit prototype/schema compatibility. Do not fan out to specialist skills merely because the board is “accessible”.

## Default Agent Workflow

1. **Clarify only if needed.** If the request has enough context, proceed with sensible defaults. Ask only when missing information changes the output materially: access method, board purpose, output format, or privacy-sensitive details.
2. **Identify the communication goal.** Convert the teacher task into communication functions: initiate, choose, request, refuse, repair, comment, ask, sequence, explain, reflect.
3. **Select a board pattern.** Choose from yes/no, choice board, first-then, visual schedule, core/fringe board, quiz/comprehension, sentence builder, story/book reader, needs/repair, or curriculum participation board.
4. **Create canonical AAC Board IR 0.4.0 before visuals.** Define pages, roles/functions/actions, real visible-target limits, student/setup controls, system fit, repair, privacy, attribution, SETT/UDL/differentiation and evidence needs. Run `scripts/canonicalize_board_ir.py` for legacy input, then validate against `references/aac-board-ir.schema.json` and `scripts/validate_board_ir.py`.
5. **Review symbols as candidates.** When symbols are wanted, run `scripts/fetch_arasaac_symbols.py <ir> --review-out <review.json>`. A teacher/team reviewer chooses `approvedSymbolId` values from the contact sheet; apply them with `--apply-review`. Keep text fallback. Use `--auto-select` only when the user explicitly accepts automated semantic selection.
6. **Render from IR.** Follow `references/output-quality.md`: preserve chosen positions, distinguish symbol drafts from complete representations, and reject unsupported access modes. Use `scripts/render_html.py` for deterministic single-file HTML, `scripts/render_open_aac_studio.py` for explicit app compatibility, and `scripts/render_obf.py` for OBF/OBZ. Never hand-edit a generated HTML export; change IR or the shared runtime and re-render.
7. **Validate and run real QA.** Run `scripts/validate_html_parity.py`, static checks, and browser/device tests where available. Count every active student target, including setup, navigation and stop controls—not only vocabulary cells. For new candidate folders, run `scripts/evaluate_fresh_output.py` against the fixture manifest.
8. **Return usable files and honest caveats.** Include where the file was saved, what it supports, what needs real-device/team testing, unresolved `systemFit` items, and what can be customised.

## Output Defaults

When the user does not specify output:

- For classroom digital use: create a single self-contained HTML file.
- For Open AAC Studio import/testing: create app-compatible JSON rendered from the canonical IR.
- For low-tech use: create printable HTML or Markdown with symbols/search terms and attribution.
- For complex curriculum tasks: create a resource pack with IR JSON, rendered HTML/print output, and teacher notes.

## Definition Of Done

A generated AAC board is ready only when it is:

- **Evidence-informed:** aligned with communication rights, communicative competence, aided language/core vocabulary principles, and UDL action/expression.
- **Communication-rich:** includes more than content labels or quiz answers.
- **Access-real:** designed for the stated access method and usable by keyboard as a baseline.
- **Curriculum-strong:** preserves learning intent while reducing access barriers.
- **Privacy-safe:** no unnecessary student identifiers or sensitive notes.
- **Offline/print-aware:** text fallback, attribution, and practical classroom deployment are addressed.
- **Verified:** IR validates, output opens/parses, and the board is checked against `references/qa-rubric.md`.

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
- Missing SETT/UDL/differentiation/evidence metadata while claiming the resource is differentiated.
- Noun-grid, quiz-only, compliance-first, or adult-voice boards that look polished but reduce student agency.

## Maintenance Note

This skill should absorb lessons from the Open AAC Studio prototype and from real classroom builds. When a generated board fails QA or a better pattern emerges, patch the relevant reference file rather than only fixing one board.

# Agent Workflow: Teacher Intent To AAC Board

Use this as the operational workflow for direct AI-generated AAC boards/resources.

## Phase 0 — Safety And Scope

Before generating, check:

- Is the request about a classroom support/resource rather than clinical AAC assessment?
- Does it contain sensitive student data? If yes, minimise or anonymise before using external services.
- Is the board meant to supplement communication, not replace a student's full AAC system?
- Is there an access method that changes layout decisions?

If the user supplies private details, use only the minimum needed in the final local file and avoid repeating sensitive details in summaries.

## Phase 1 — Intake

Extract or infer:

- **Context:** lesson/routine/assessment/community activity.
- **Student role:** what the student should be able to communicate or show.
- **Communication functions:** choose, refuse, request, repair, comment, ask, answer, sequence, explain, reflect.
- **Access:** touch, keyboard, eye gaze/dwell, switch scanning, partner-assisted, print.
- **Output:** HTML, JSON, printable board, resource pack, prompt/template.
- **Constraints:** offline, Microsoft Edge, EQ network, PRC-Saltillo, no internet, print-only, symbol source.
- **Age/dignity:** age band and tone.
- **SETT/UDL/differentiation:** student strengths/access preferences without diagnoses, environment constraints, task demand, tool/support choices, and action/expression options.
- **System fit:** established AAC, familiar vocabulary/layout/symbols, actual device/mount/vision/fatigue, language/culture/voice and partner signals.

Ask only if missing data changes the product. Otherwise proceed with explicit assumptions.

## Phase 2 — Board Plan

Produce an internal plan before file generation:

1. Board pattern.
2. Page count.
3. Grid size per page.
4. Recurring core/repair positions.
5. Topic/fringe vocabulary.
6. Access settings.
7. Symbol/search strategy.
8. SETT/UDL/differentiation strategy.
9. Curriculum/evidence strategy.
10. QA risks.

For complex tasks, briefly share this plan with Richard before coding unless he asked to just build.

## Phase 3 — Generate Canonical AAC Board IR

Create canonical AAC Board IR even if final output is HTML or print. Start from `templates/board-json-skeleton.json`; do not invent a smaller shape that omits schema-required access, display, student-control, system-fit, symbol, privacy or attribution fields. See `aac-board-ir.md` for controlled values and behaviour.

This prevents the agent from jumping straight to pretty but weak boards. Renderers should preserve the IR's roles, functions, access assumptions, privacy note, attribution, teacher notes, SETT, UDL, differentiation, participation-barrier, and evidence-plan metadata.

## Phase 4 — Output Generation

First run canonical `--check`, JSON Schema and semantic validation. If symbols are requested, generate a candidate review/contact sheet and apply only approved ids. Then render rather than hand-authoring target outputs.

Choose the renderer/output contract:

- **Single-file HTML:** generate deterministically with `scripts/render_html.py` for direct student use.
- **Canonical IR JSON:** best as the editable source of truth.
- **Open AAC Studio JSON:** best for prototype import/testing or later conversion.
- **Printable HTML/Markdown:** best for low-tech boards or teacher packets.
- **Resource pack:** best for complex curriculum scaffolds with teacher notes and multiple outputs.

Output should include:

- student-facing board/resource;
- text fallback for symbols;
- attribution/licensing notes;
- teacher notes when useful;
- customisation points.

## Phase 5 — QA And Repair

Run the QA rubric. Fix issues before final response where practical.

Minimum checks:

- Does IR canonical/schema/semantic validation pass?
- Can the student say more than adult-selected answers?
- Is there repair/escape language?
- Does total active-target accounting pass in every interaction phase?
- Is text readable and age-respectful?
- Does the file parse/open?
- Are there no external dependencies if offline/single-file was required?
- Is symbol attribution present?
- Are privacy and filenames safe?
- Does the IR include a differentiation/evidence route for any curriculum or QCIA task?
- Does HTML/IR/shared-runtime parity pass, followed by browser/device tests where applicable?
- Does a newly generated candidate folder pass `scripts/evaluate_fresh_output.py` rather than relying only on golden fixtures?

## Phase 6 — Delivery

Final response should include:

- File path or attachment.
- What it does.
- Access features.
- What evidence/curriculum function it supports.
- How to customise.
- Remaining real-world checks: SLP/OT/team, actual student, actual device, school network.

Avoid overclaiming. Say “draft classroom support” or “prototype board” unless it has been tested with the student/team.

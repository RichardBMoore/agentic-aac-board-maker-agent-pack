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

## Phase 3 — Write The Board Source

Write the board as data before any visuals, even if the final output is HTML or print. Copy `templates/board-json-skeleton.json` to `<name>.source.json` and edit it. The source holds what needs judgement: pages, each button's words, role, function and word class, access, audience, partner card, teacher notes, `systemFit`, SETT/UDL/differentiation and evidence. Leave out what the tools add (house-word wording, symbols and positions, literacy pages, navigation, colours, defaults); the build fills schema-required fields it can derive. See `aac-board-ir.md` for controlled values and behaviour.

This prevents the agent from jumping straight to pretty but weak boards. Renderers preserve the board's roles, functions, access assumptions, privacy note, attribution, teacher notes, SETT, UDL, differentiation, participation-barrier, and evidence-plan metadata.

## Phase 4 — Build

Run one command:

```sh
python3 scripts/build_board.py <name>.source.json --out-dir <pack-folder>
```

It applies house standards, runs canonical, JSON Schema and semantic validation, renders the outputs, checks parity, eye-gaze rules and screen fit, and prints an outline with a "Needs attention" list. Fix problems in the source and rebuild. Never hand-author or hand-edit target outputs, and never open the built `*.ir.json` directly (it is mostly embedded pictures): use `scripts/inspect_board.py`. If symbols are requested, generate a candidate review/contact sheet from the built IR, apply only approved ids, and rebuild.

The build writes these outputs by default: the HTML board, the partner card and OBF/OBZ. The contracts are:

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

- Does `scripts/build_board.py` pass (house standards, canonical/schema/semantic validation, parity, eye-gaze rules, screen fit)?
- Can the student say more than adult-selected answers?
- Is there repair/escape language?
- Does total active-target accounting pass in every interaction phase?
- Is text readable and age-respectful?
- Does the file parse/open?
- Are there no external dependencies if offline/single-file was required?
- Is symbol attribution present?
- Are privacy and filenames safe?
- Does the IR include a differentiation/evidence route for any curriculum or QCIA task?
- Have the build's TO DO items been dealt with or carried into the handover (symbols for this board's own words, partner card, teacher notes)?
- Do browser/device tests pass where applicable?
- Has someone who did not build the board reviewed it (the `aac-board-qa` subagent in Claude Code; otherwise a self-review from `scripts/inspect_board.py <ir> --all`)?

`scripts/evaluate_fresh_output.py` is for regression-testing the pack against its six benchmark prompts. It does not evaluate an ordinary new board.

## Phase 6 — Delivery

Final response should include:

- File path or attachment.
- What it does.
- Access features.
- What evidence/curriculum function it supports.
- How to customise.
- Remaining real-world checks: SLP/OT/team, actual student, actual device, school network.

Avoid overclaiming. Say “draft classroom support” or “prototype board” unless it has been tested with the student/team.

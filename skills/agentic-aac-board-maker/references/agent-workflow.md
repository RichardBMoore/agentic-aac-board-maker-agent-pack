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
8. Curriculum/evidence strategy.
9. QA risks.

For complex tasks, briefly share this plan with Richard before coding unless he asked to just build.

## Phase 3 — Generate Canonical AAC Board IR

Create a canonical AAC Board IR even if final output is HTML or print. See `aac-board-ir.md` for the full contract.

```json
{
  "schemaVersion": "0.2.0",
  "format": "agentic-aac-board-ir",
  "title": "",
  "purpose": "",
  "access": {
    "intended": [],
    "profile": ""
  },
  "communicationFunctions": [],
  "pages": [
    {
      "name": "",
      "pattern": "",
      "grid": "3x3",
      "buttons": [
        {
          "label": "",
          "role": "core|fringe|repair|navigation|evidence|teacher",
          "function": "request|refuse|comment|question|answer|sequence|explain|reflect|repair|navigate",
          "searchTerm": "",
          "spokenText": "",
          "actions": []
        }
      ]
    }
  ]
}
```

This prevents the agent from jumping straight to pretty but weak boards. Renderers should preserve the IR's roles, functions, access assumptions, privacy note, attribution, and teacher notes.

## Phase 4 — Output Generation

Choose the renderer/output contract:

- **Single-file HTML:** best for direct student use and eye gaze/dwell resources.
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

- Does the IR validate?
- Can the student say more than adult-selected answers?
- Is there repair/escape language?
- Is the grid compatible with the access method?
- Is text readable and age-respectful?
- Does the file parse/open?
- Are there no external dependencies if offline/single-file was required?
- Is symbol attribution present?
- Are privacy and filenames safe?

## Phase 6 — Delivery

Final response should include:

- File path or attachment.
- What it does.
- Access features.
- What evidence/curriculum function it supports.
- How to customise.
- Remaining real-world checks: SLP/OT/team, actual student, actual device, school network.

Avoid overclaiming. Say “draft classroom support” or “prototype board” unless it has been tested with the student/team.

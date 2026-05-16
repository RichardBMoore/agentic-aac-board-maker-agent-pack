# Copy/Paste Agent Build-Test Prompt

Use this prompt with an AI coding/agent system to test whether the skill stack can actually produce useful outputs.

Please use this local folder as your source of truth:

```text
/Users/richardbrucemoore/Desktop/Agentic-AAC-Board-Maker-Agent-Pack
```

Start with:

```text
skills/agentic-aac-board-maker/SKILL.md
```

Then read the relevant references, especially:

```text
skills/agentic-aac-board-maker/references/evidence-base.md
skills/agentic-aac-board-maker/references/canonical-architecture.md
skills/agentic-aac-board-maker/references/aac-board-ir.md
skills/agentic-aac-board-maker/references/anti-patterns.md
skills/agentic-aac-board-maker/references/agent-workflow.md
skills/agentic-aac-board-maker/references/board-grammar.md
skills/agentic-aac-board-maker/references/access-methods.md
skills/agentic-aac-board-maker/references/curriculum-qcia-translation.md
skills/agentic-aac-board-maker/references/output-contracts.md
skills/agentic-aac-board-maker/references/qa-rubric.md
```

## Task

Create 6 proof-of-concept AAC resources that test the skill architecture:

1. Eye-gaze/dwell choice board  
2. QCIA community access board  
3. Curriculum sentence-builder board  
4. Visual schedule with expressive options  
5. Needs/repair communication board  
6. Printable partner-assisted scanning board  

For each resource, produce:

- a short board plan;
- canonical AAC Board IR JSON;
- the final resource file, preferably single-file HTML unless another format is clearly better;
- Open AAC Studio-compatible JSON only if useful;
- teacher notes;
- symbol/search-term strategy;
- access notes;
- QA notes against the rubric.

Validate any IR JSON with:

```sh
python3 skills/agentic-aac-board-maker/scripts/validate_board_ir.py <board.ir.json>
```

If producing Open AAC Studio JSON, render it from the IR:

```sh
python3 skills/agentic-aac-board-maker/scripts/render_open_aac_studio.py <board.ir.json> <open-aac-studio.json>
```

## Non-Negotiables

- Preserve student communication rights and agency.
- Do not create boards that only allow adult-controlled quiz answering.
- Include repair/escape language where appropriate: Help, Stop, Different, Finished, Not that, I don't know, or similar.
- Match density to access method.
- Use Australian English.
- Do not use proprietary Boardmaker/PCS assets.
- Use text fallback and ARASAAC search terms or open/teacher-owned symbol strategy.
- Keep files offline-friendly where possible.
- Do not include real student names or sensitive details.

## Evaluation Questions

After creating the resources, answer:

1. Did the skill files give enough guidance to build the resources?
2. Where did you have to guess?
3. Which reference file was most useful?
4. Which reference file was missing detail?
5. What should be changed in the skill stack before real classroom use?
6. Did the canonical IR help or get in the way?

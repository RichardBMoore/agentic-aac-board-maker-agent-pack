# Prompt Recipes

These prompts are for agent self-use and for creating reusable handoffs. They encode the expected reasoning.

## Universal Board Generation Prompt

```text
Create an evidence-informed AAC board/resource from this teacher intent:
<context>

Requirements:
- Preserve student agency and communication rights.
- Identify communication functions before choosing vocabulary.
- Blend core and fringe vocabulary.
- Include repair/escape language where appropriate.
- Match density/layout to access method: <access>.
- Use Australian English and age-respectful labels.
- Use ARASAAC search terms or text fallback; do not use proprietary symbols.
- Return <output type>.
```

## Self-Critique Prompt

```text
Review this AAC board as if it will be used in a real classroom.
Check:
1. Can the student initiate/refuse/repair/comment, not only answer?
2. Is the access method realistic for the grid density?
3. Are labels short, speakable, and age-respectful?
4. Is there a core + fringe balance?
5. Does it preserve the curriculum/QCIA intent?
6. Does it avoid private/sensitive data?
7. Does it have attribution and offline/text fallback?
List required fixes before final output.
```

## Eye-Gaze Board Prompt

```text
Generate an eye-gaze/dwell-safe AAC board for: <context>.
Use at most <N> buttons per page. Default dwell 1200 ms.
Prioritise large targets, clear spacing, no scrolling in student mode, visible dwell progress, keyboard fallback, and no single-hover destructive actions.
Include Help/Stop/Different/Finished where appropriate.
Return a single-file HTML board plus teacher notes.
```

## Switch Scanning Prompt

```text
Generate a switch-scanning AAC board for: <context>.
Use a small predictable grid. Keep visual order, DOM order, and scan order aligned.
Provide Start/Stop Scan, Step, Select, and Escape-to-stop if HTML.
Use strong scan highlight not dependent on colour alone.
Return <HTML/JSON/print>.
```

## Curriculum Participation Prompt

```text
Convert this curriculum task into an AAC participation board:
<task>

Do not simply make a quiz unless the task requires it.
Identify the cognitive demand and translate it into communication moves such as choose, compare, explain, because, opinion, question, reflect.
Preserve learning intent while reducing access load.
Return <output type>.
```

## QCIA Board Prompt

```text
Create a QCIA-aligned AAC board for this goal/context:
<goal>

Focus on practical observable communication: choose, request help, sequence, indicate safety, express preference, reflect.
Include teacher evidence notes and student agency options.
Return <output type>.
```

## Symbol Strategy Prompt

```text
For each button in this board, propose:
- label
- communication function
- core/fringe/repair/navigation role
- ARASAAC search term
- spoken text
- whether a teacher-owned photo would be better
Do not use proprietary symbols or sensitive student details.
```

## Teacher Modeling Note Prompt

```text
Write a short teacher note for this board explaining how to model AAC use.
Include: model key words while speaking, comment rather than only questioning, wait time, respond to all communication, and accept multimodal responses.
Keep it practical and classroom-friendly.
```

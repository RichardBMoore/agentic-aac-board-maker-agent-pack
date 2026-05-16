# Intake And Decision Tree

The agent should avoid unnecessary questioning, but AAC boards can fail if key constraints are unknown. Use this decision tree.

## Minimal Intake

If the request is broad, gather or infer:

1. **Purpose:** What should the student communicate or do?
2. **Access method:** touch, keyboard, eye gaze/dwell, switch, print/partner-assisted?
3. **Context:** lesson, routine, assessment, QCIA goal, curriculum area, community/living skill?
4. **Output:** HTML, JSON, printable board, or resource pack?
5. **Button density:** if known, number of choices/pages.

## Ask Only When It Matters

Ask a clarifying question if:

- access method is unknown and the board could be too dense;
- output format is unknown and the user needs a file now;
- the task involves real student sensitive data;
- curriculum level/assessment evidence is essential;
- symbols/photos are requested and source rights are unclear.

Do not ask if a safe default is obvious.

## Default Assumptions

When unspecified:

- Australian English.
- Privacy: anonymous.
- Output: single-file HTML for direct use, JSON if explicitly Open AAC Studio/import.
- Symbol source: ARASAAC search terms, not embedded remote images unless needed.
- Access: touch + keyboard baseline.
- Add eye-gaze/dwell only when requested or clearly implied.
- Grid: 3x3 for general choice boards, 2x2 for high support/yes-no/early gaze.
- Include Help and Finished/Different where useful.

## Board Pattern Decision Tree

- Need quick response/preference/consent? → Yes/no board.
- Need choose from options? → Choice board.
- Need routine/transition? → First-then or visual schedule.
- Need express needs/distress/repair? → Needs/repair board.
- Need show understanding? → Quiz/comprehension board plus Help/I don't know.
- Need write/speak a sentence? → Sentence builder.
- Need participate in text/story? → Story/book reader or opinion + reason board.
- Need curriculum evidence? → Curriculum participation board.
- Need QCIA practical evidence? → QCIA goal board.

## Access Decision Tree

- Eye gaze/dwell: reduce density, large cells, visible dwell, no single-hover destructive actions.
- Switch scanning: small number of choices, predictable order, linear scan first, row-column for larger boards.
- Keyboard: semantic buttons, visible focus, Enter/Space, logical Tab order.
- Print/partner-assisted: strong borders, high contrast, enough whitespace, clear scan/pointing order.
- Touch/mouse: still keep keyboard fallback and target size usable.

## Output Decision Tree

- User asks for “make a board/resource I can use” → single-file HTML by default.
- User asks for “Open AAC Studio/import/editable schema” → JSON.
- User asks for “print/laminate/low-tech” → printable HTML/Markdown.
- User asks for “skill/prompt/workflow” → Markdown skill/reference file.
- User asks for “full pack” → folder with board HTML, JSON, teacher notes, README.

## Privacy Decision Tree

- Public curriculum/example content → safe to use.
- Student name, diagnosis, behaviour, medical, family, OneSchool/NCCD/QCIA evidence details → do not send externally; anonymise in generated files unless explicitly needed.
- Custom photos → use only local/teacher-owned or user-approved media; do not upload to AI vision without explicit approval.

## Quick Intake Template

If clarification is needed, ask in one compact block:

```text
I can build this. Quick details so I don't make the wrong board:
1. Access: touch/keyboard, eye gaze/dwell, switch, or print?
2. Output: single HTML, printable board, Open AAC Studio JSON, or full pack?
3. Board purpose: choose, schedule, answer, explain, request/help, or sentence builder?
4. Any required vocabulary or curriculum/QCIA goal?
```

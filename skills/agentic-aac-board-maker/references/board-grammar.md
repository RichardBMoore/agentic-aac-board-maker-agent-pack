# Board Grammar

Board grammar is the structured language the agent uses before generating HTML/JSON/print output. It prevents shallow “pretty grid of symbols” results.

## Board Unit Hierarchy

1. **Resource** — the whole generated artefact.
2. **Board/activity** — one coherent communication task.
3. **Page** — one screen/print panel.
4. **Button/cell** — one selectable communication item.
5. **Action** — what happens on selection: speak, log, navigate, add word, mark evidence.

## Required Design Fields

For every board, decide:

- `purpose`: why the board exists.
- `audience`: age/stage, dignity tone.
- `accessMethod`: touch, keyboard, eye gaze/dwell, switch, print.
- `communicationFunctions`: what the student can do with it.
- `pattern`: yes/no, choice, first-then, schedule, sentence builder, etc.
- `grid`: rows/columns per page.
- `navigation`: back/next/home/finished behaviour.
- `repair`: how the student says help/stop/different/not that.
- `symbolStrategy`: ARASAAC search terms, custom photos, text-only.
- `evidence`: what teacher can observe/export if assessment/QCIA.

## Button Roles

Use these roles internally:

- `core`: reusable high-frequency words (want, more, help, stop, go, finished, like, different, because).
- `fringe`: context-specific words (hero, recycle, bus, microscope, basketball).
- `repair`: communication repair/safety (help, repeat, show me, not that, too hard, wait).
- `navigation`: next, back, home, finished.
- `evidence`: choices that indicate curriculum/QCIA evidence.
- `comment`: I like, I think, funny, interesting, boring, important.
- `question`: who, what, where, why, can you show me?
- `sentence`: starters/connectives (I think, because, first, next, then, also).
- `teacher`: non-student controls; keep out of student mode or locked.

## Communication Functions

A good board supports one or more:

- initiate
- request
- refuse
- choose
- comment
- ask
- answer
- sequence
- explain
- repair
- reflect
- socialise
- navigate
- regulate/rest

Avoid boards where every button has only `answer` or `label` function unless the user explicitly asks for a narrow quiz.

## Stable Positions

For consistency, use stable positions when possible:

### 2x2

1. Yes / First / Primary choice
2. No / Then / Secondary choice
3. Help / More
4. Finished / Stop

### 3x3

1. I want / I think / Start
2. More / Because / Core
3. Finished / Stop
4. Topic 1
5. Topic 2
6. Topic 3
7. Help
8. Different / Not that
9. Back / Next / Finished

Adjust for context, but keep repair/navigation predictable.

## Page Patterns

### Single Page Choice Board

Use for quick classroom participation. 4–9 buttons; include repair.

### Two Page Curriculum Board

- Page 1: participation functions (I think, because, help, question, finished).
- Page 2: topic vocabulary/evidence choices.

### Sentence Builder

- Page 1: starters.
- Page 2: reasons/connectives.
- Page 3: topic words.
- Page 4: control/repair/speak/clear.

### Visual Schedule

- ordered steps;
- optional “done” state;
- Help/Wait/Finished;
- avoid pretending this is a full expressive AAC system.

### First-Then

- two huge main cells;
- optional Help/Wait/Change;
- avoid using it only to demand compliance.

### Quiz/Comprehension

- prompt + 2–4 choices;
- include Help/I don't know/Show me;
- log result only if relevant;
- feedback calm, not punitive.

## Density Rules

- 2x2: high support, early gaze, yes/no, first-then, simple quiz.
- 2x3 / 3x2: moderate choices, visual schedule.
- 3x3: general AAC choice/curriculum board.
- 4x4: only for confident direct touch/mouse or tested access; avoid for early gaze.
- Multi-page is better than dense clutter for gaze/switch users.

## Agent Self-Check

Before generating final output, answer internally:

- What can the student initiate?
- How can the student refuse or repair?
- How does the board support the lesson goal?
- Which buttons are core vs fringe?
- Is the layout compatible with the access method?
- What should remain editable by the teacher?

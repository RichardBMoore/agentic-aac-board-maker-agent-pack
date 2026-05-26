---
name: open-aac-studio-board-builder
description: "Use when creating, modifying, or QA-checking Open AAC Studio / Boardmaker-style AAC boards, activity JSON, symbol-supported classroom resources, AI-generated board starters, QCIA/Australian Curriculum boards, eye-gaze/dwell/switch-accessible players, print/export resources, or reusable Boardmaker-clone workflows."
license: MIT
metadata:
  hermes:
    tags: [aac, boardmaker, open-aac-studio, symbols, arasaac, eye-gaze, dwell, switch-scanning, qcia, australian-curriculum, offline-html, classroom]
    related_skills: [agentic-aac-board-maker, build-aac-student-supports, eyegaze-dwell-html, classroom-access-tools, richard-school-resource-workflow]
---

# Open AAC Studio Board Builder

## Overview

Use this skill to act as the Open AAC Studio / Boardmaker-style compatibility layer. Richard's larger vision is **not** that teachers must use the Open AAC Studio web app as the final authoring surface. The larger vision is that an AI agent directly makes the AAC board/resource from teacher intent, using `agentic-aac-board-maker` and its canonical AAC Board IR as the design source.

Open AAC Studio is primarily a **research/prototype/reference artefact**: it distils Boardmaker/Open Board-style concepts into schemas, board patterns, access rules, symbol workflows, player behaviours, and QA checks that can be turned into reusable agent skills. The web app proves the workflow and provides concrete examples, but the endgame is agent-generated boards: HTML, JSON, printable boards, or classroom resource packs created directly by the AI.

The goal is not to copy Boardmaker 7's proprietary assets or PCS symbols. The goal is to distil the useful authoring pattern — fast symbol-supported educational and communication boards — into an open, local-first, classroom-ready agent workflow that can create boards quickly while preserving student voice, access, dignity, and offline reliability.

The current reference prototype is usually:

`/Users/richardbrucemoore/Desktop/School/05-Accessibility-AAC-and-Inclusion/AAC-Tools/Open-AAC-Studio-Working/`

Its editor/player pattern includes grid boards, symbol search, Symbolate-style buttons, activity JSON import/export, print, a student player, dwell access, switch scanning, TTS, offline symbol caching, local library, Australian Curriculum v9 starter generation, and QCIA/goal-based board generation. Treat those features as knowledge to extract into agent workflows, not as mandatory software the user must operate.

## When To Use

Use this skill when the user asks to:

- Inspect, modify, or use the Open AAC Studio / Boardmaker-style reference prototype.
- Create Open AAC Studio activity JSON or test a board against the prototype schema.
- Extract reusable board-maker knowledge from the prototype into agent workflows.
- Build a quick AAC board from a teaching goal, curriculum task, QCIA outcome, or worksheet when Open AAC Studio compatibility is specifically useful.
- Make a Boardmaker-style resource without relying on commercial Boardmaker/PCS assets.
- Generate symbol-supported choice boards, visual schedules, first-then boards, quiz boards, book readers, communication repair boards, or sentence builders.
- Turn curriculum content into AAC-accessible communication moves.
- Make a board for eye gaze, dwell, switch scanning, keyboard, touch, print, or offline school use.
- Create a reusable workflow/agent prompt for board generation.
- QA a board before classroom use.

For new direct classroom resources, use `agentic-aac-board-maker` first. Use this skill when the output specifically needs Open AAC Studio compatibility, prototype app behaviour, import/export fields, or editor/player code changes.

Do **not** use this skill to generate clinical advice, replace SLP/OT assessment, store sensitive student data, or clone proprietary Boardmaker assets. Use ARASAAC, teacher-owned images, public-domain/open resources, or text fallbacks with correct attribution.

## Working Principle

A board is only finished when it is:

1. **Communication-rich** — lets the student initiate, refuse, repair, ask, comment, choose, and answer.
2. **Curriculum-strong** — supports the intended learning/evidence, not just random symbols.
3. **Access-real** — works for the intended access method in practice.
4. **Classroom-safe** — local-first, private, printable/exportable, and robust when internet/TTS/images fail.
5. **Fast to make** — uses templates, schema, symbol search terms, and AI drafting to reduce teacher prep time.

## Fast Workflow

1. **Interpret the teacher intent**
   - Topic/task: what lesson, routine, text, assessment, or context?
   - Board purpose: choose, answer, sequence, request, repair, comment, explain, rehearse, record, reflect.
   - Evidence need: curriculum, ICP, QCIA, participation, communication sample, or classroom routine.
   - Access method: touch, mouse, keyboard, eye gaze/dwell, switch scanning, print/partner-assisted.
   - Output: Open AAC Studio JSON, single-file HTML, print board, or changes to the working app.

2. **Choose a board pattern**
   - Yes/no: 2–4 large targets; include Help/More/Finished when possible.
   - Choice board: 4, 6, 9, 12, or 16 targets; one concept per button.
   - Core/fringe board: stable core words plus activity-specific vocabulary.
   - First-then: two very large targets for sequence/routine/transition.
   - Visual schedule: ordered steps with consistent scan/read order.
   - Quiz/comprehension: prompt + 2–4 choices; include Help/I don't know when appropriate.
   - Sentence builder: starters + reasons + feelings/opinions + speak-back.
   - Book reader/story: page-by-page content with stable Next/Back/Finished.
   - Needs/repair: Help, Stop, Break, Different, Again, Too hard, Too loud, Toilet, Pain, Finished.

3. **Draft the vocabulary**
   - Blend core words and task-specific fringe words.
   - Prefer short, speakable labels.
   - Use age-respectful Australian English.
   - Include an escape/repair pathway: Stop, Help, Different, Back, Finished, Not that.
   - For assessment, translate the task into communication functions rather than only right/wrong answers.

4. **Generate Open AAC Studio activity JSON from the canonical IR when possible**
   - Use stable IDs, short labels, symbol search terms/IDs, target layout, access settings, and action lists.
   - Keep activity data separate from editor/player code.
   - Default `privacyLevel` to `anonymous`.
   - Include ARASAAC attribution if ARASAAC symbols/search terms are used.
   - Preserve IR roles/functions and IR 0.3.0 SETT/UDL/differentiation/evidence metadata so the communication design is not lost in app-specific JSON.

5. **Add symbols safely**
   - Use ARASAAC IDs when known; otherwise include `searchTerm` or leave symbol blank with a text fallback.
   - Use teacher-owned photos for local people, places, routines, and equipment.
   - Do not send student names, diagnoses, behaviour notes, or private family/school details to external AI/symbol services.
   - Prepare/copy/cache symbols before the lesson when internet may be unavailable.

6. **Set access defaults**
   - Ordinary AAC: target floor about 96 px.
   - Gaze-heavy boards: prefer 120–200 px targets and at least 20 px gaps.
   - Dwell: start around 1000–1200 ms; use 1500 ms for accidental activation risk; avoid very fast defaults.
   - Switch: linear scan first; row-column for larger boards.
   - Keep DOM order, visual order, focus order, and scan order aligned.

7. **Verify before delivery**
   - Load in editor and player if files are available.
   - Test keyboard, pointer, dwell cancellation, scan start/step/select/stop, TTS stop, contrast, text fit, print/export, and offline readiness.

## Open AAC Studio Working Copy

Common file map:

- `index.html` — editor UI.
- `player.html` — student/classroom player UI.
- `js/data.js` — activity schema, defaults, local library, profiles, logs.
- `js/editor.js` — editor state, rendering, templates, symbol tools, board builders, action controls.
- `js/player.js` — player rendering, classroom mode, access settings, logs, export/report.
- `js/access.js` — dwell controller and switch scanner.
- `js/actions.js` — action execution: speak, log, navigation, variables, conditionals.
- `js/symbols.js` — ARASAAC search, local/offline symbol cache, custom symbols, Symbolate helpers.
- `js/tts.js` — speech synthesis, voice preference, stop speech.
- `js/ai-config.js` — AI provider config, OpenAI-compatible/custom endpoint request handling.
- `js/ai-suggest.js` — AI/fallback generation for symbols, QCIA goal boards, quiz distractors, Australian Curriculum v9 starter boards.
- `js/file-io.js` — import/export helpers.
- `js/sw-update.js` — update banner handling.
- `templates/*.json` — starter activity templates.
- `css/*.css` — editor/player/print styles.
- `sw.js` + `manifest.webmanifest` — PWA/offline app shell.

Run locally:

```sh
cd "/Users/richardbrucemoore/Desktop/School/05-Accessibility-AAC-and-Inclusion/AAC-Tools/Open-AAC-Studio-Working"
python3 -m http.server 4173 --bind 127.0.0.1
```

Open:

- Editor: `http://127.0.0.1:4173/index.html`
- Player: `http://127.0.0.1:4173/player.html`
- Classroom player: `http://127.0.0.1:4173/player.html?classroom=1`

## Boardmaker 7 Inspiration, Not Duplication

Public Boardmaker 7 materials emphasise: fast templates, customisable print/interactive activities, symbol search, symbol-supported education/communication materials, sharing, backward compatibility, cross-platform use, and large symbol libraries. Open AAC Studio should borrow the **workflow ideas** only:

- fast templates
- searchable/open symbols
- custom photos
- print + interactive player
- quick editing
- classroom delivery
- reusable activity library
- import/export
- accessible student mode

Do not copy proprietary PCS symbols, Boardmaker UI art, manuals, templates, or file formats unless the user provides lawful rights and scope.

## Prompt Recipes For Agentic Generation

### Quick choice board

Use when the user gives a topic and wants a rapid board.

Inputs:
- title
- context
- access method
- number of buttons
- required vocabulary

Output:
- activity JSON with 4/6/9/12 buttons
- labels, search terms, actions, accessibility settings

Prompt shape:

```text
Create an Open AAC Studio choice board for: <context>.
Use <N> buttons. Access method: <access>.
Include communication repair options and age-respectful Australian English.
Return Open AAC Studio activity JSON only.
```

### QCIA goal board

Use for personal/living skills, community access, leisure, communication, or transition evidence.

```text
Create an AAC board aligned with this QCIA goal: <goal>.
Convert the goal into student communication moves: choose, request, refuse, ask for help, sequence, comment, and reflect.
Keep labels short. Include ARASAAC search terms. Return Open AAC Studio JSON.
```

### Australian Curriculum v9 board

Use when the user provides learning area, year/band, capability/priority, and classroom focus.

```text
Create an AAC-accessible Australian Curriculum v9 starter board.
Learning area: <area>. Year/band: <year>. Capability: <capability>. Priority: <priority>. Focus: <focus>.
The board should let the student participate in the same lesson through communication functions, not just answer quiz questions.
Return Open AAC Studio JSON.
```

### Worksheet/task conversion

```text
Convert this classroom task into an AAC board.
Task text: <paste task>.
Student access: <access>. Evidence needed: <evidence>.
Create: vocabulary, board pattern, pages, buttons, symbol search terms, and actions.
Include Help, Stop/Finished, and a way to express opinion/reason if appropriate.
```

### Eye-gaze board

```text
Create an eye-gaze/dwell-safe board.
Maximum buttons: <N>. Dwell default: 1200ms unless specified.
Use large targets, minimal scrolling, predictable order, and a safe repair/cancel option.
Return Open AAC Studio JSON and a short access QA checklist.
```

## Default JSON Skeleton

Use `references/open-aac-studio-schema.md` for the full local schema notes. Minimal working activity shape:

```json
{
  "schemaVersion": "0.1.0",
  "app": "Open AAC Studio",
  "id": "activity-example",
  "name": "Example Board",
  "type": "interactive",
  "settings": {
    "orientation": "landscape",
    "width": 1024,
    "height": 768,
    "speakLabels": true,
    "showLabels": true,
    "dwellTimeMs": 1200,
    "switchScanning": false,
    "scanSpeedMs": 1400,
    "scanPattern": "linear"
  },
  "accessibility": {
    "intendedAccess": ["touch", "mouse", "keyboard", "eye-gaze-dwell", "switch-scanning"],
    "minimumTargetSizePx": 120,
    "dwellSafe": true,
    "scanOrder": "dom-order",
    "audioCues": true
  },
  "pages": [
    {
      "id": "page-main",
      "name": "Main",
      "layout": "grid",
      "gridColumns": 3,
      "gridRows": 3,
      "margin": 10,
      "backgroundColour": "#ffffff",
      "buttons": []
    }
  ],
  "variables": {},
  "metadata": {
    "tags": ["aac", "classroom"],
    "curriculum": "",
    "privacyLevel": "anonymous"
  },
  "licences": [
    {
      "source": "ARASAAC",
      "licence": "CC BY-NC-SA",
      "attribution": "Pictograms by ARASAAC (Government of Aragon)"
    }
  ]
}
```

## Button Design Rules

Each button should normally include:

- `id`: stable, lower-case-ish identifier.
- `label`: short student-facing text.
- `symbolId` or `symbolSrc`: optional; text fallback must still work.
- `searchTerm`: useful when generating symbol suggestions even if not persisted by older schema.
- `symbolLayout`: `label-bottom`, `label-top`, `symbol-only`, `label-only`, or `symbolate`.
- `audioCue`: usually same as label, or a clearer spoken phrase.
- `result`: `selected`, `correct`, or `incorrect` when assessment logging matters.
- `actions`: usually `speak-label` and `log-attempt`; add navigation/variables only when needed.

Default actions:

```json
[
  { "id": "act-speak", "type": "speak-label" },
  { "id": "act-log", "type": "log-attempt" }
]
```

## Curriculum-to-Communication Translation

When adapting curriculum, convert content demands into AAC communication functions:

- Identify/label → choose from field, match, say what it is.
- Sequence → first/next/then/last, before/after.
- Compare → same/different, bigger/smaller, like/unlike.
- Explain → because, I think, evidence, reason.
- Opinion → I like, I don't like, best, interesting, boring, surprising.
- Ask/repair → help, repeat, show me, I don't know, different.
- Reflect → I did it, hard/easy, next time, I need.

For ICP/QCIA scaffolds, include own-choice/editable options wherever practical so the student is not trapped in adult-authored answers.

## Common Pitfalls

1. **Making content boards instead of communication boards.** A board full of nouns may label a topic but not let the student communicate. Add core words, opinions, repair, request/refusal, and reasons.

2. **Over-dense gaze boards.** If the student uses eye gaze or dwell, reduce buttons before shrinking targets. Prefer multiple calm pages over one tiny board.

3. **Forgetting offline reality.** ARASAAC search and remote images may fail on the school network. Prepare symbols before class and keep text labels meaningful.

4. **Letting AI invent unsafe/private details.** Use public task/context. Do not send sensitive student information externally.

5. **No escape option.** Always include Help, Stop, Finished, Back, Different, or Not that unless the board is a deliberately tiny yes/no choice.

6. **Teacher controls in student mode.** Student/player mode must be calm, large, predictable, and hard to accidentally break.

7. **Right/wrong-only assessment.** Accessible curriculum evidence should include communication functions and student agency, not only compliance or guessing.

8. **Copying proprietary Boardmaker assets.** Use open symbols or teacher-owned media; never treat PCS/Boardmaker content as free source material.

## Verification Checklist

Before saying a board is ready:

- [ ] It uses the intended board pattern and communication functions.
- [ ] It includes repair/escape vocabulary.
- [ ] Labels are short, speakable, age-respectful, and Australian English by default.
- [ ] Targets are large enough for the intended access method.
- [ ] Visual order, DOM order, focus order, and scan order align.
- [ ] Keyboard operation works.
- [ ] Dwell starts on entry, shows progress, activates once, and cancels on leave.
- [ ] Switch scanning starts, steps, selects, and stops predictably.
- [ ] TTS can be stopped and does not overlap uncontrollably.
- [ ] Symbols have text fallback and attribution.
- [ ] Board still makes sense without internet, colour, speech, or precise pointer control.
- [ ] Teacher controls are separate from student mode.
- [ ] JSON imports/exports cleanly if using Open AAC Studio.
- [ ] Print/export is readable if required.

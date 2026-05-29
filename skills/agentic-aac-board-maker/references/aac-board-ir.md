# AAC Board Intermediate Representation

The AAC Board IR is the canonical structure an agent should create before rendering HTML, printable output, or Open AAC Studio JSON.

## Why It Exists

The IR prevents a common failure mode: turning a lesson topic into a pretty noun grid. It makes the agent state the student's communication purpose, access method, button roles, repair options, symbol strategy, and evidence route before visual output.

## Current Version

`schemaVersion: "0.3.0"` is backward-compatible with `0.2.0`. Existing `0.2.0` boards still validate, but new generated boards should include SETT, UDL, differentiation, participation-barrier, and evidence-plan metadata so the board design remains more than a layout.

## Minimal IR

```json
{
  "schemaVersion": "0.3.0",
  "format": "agentic-aac-board-ir",
  "id": "activity-slug",
  "title": "Board Title",
  "purpose": "What the student can communicate or show.",
  "audience": {
    "ageBand": "secondary",
    "tone": "age-respectful"
  },
  "access": {
    "intended": ["touch", "keyboard"],
    "profile": "direct-selection",
    "minimumTargetSizePx": 96,
    "dwellTimeMs": null,
    "switchScanning": false,
    "scanPattern": "linear"
  },
  "communicationFunctions": ["choose", "repair", "comment"],
  "pages": [
    {
      "id": "page-main",
      "name": "Main",
      "pattern": "choice-board",
      "grid": { "rows": 3, "columns": 3 },
      "buttons": [
        {
          "id": "btn-help",
          "label": "Help",
          "role": "repair",
          "function": "repair",
          "spokenText": "Help",
          "searchTerm": "help",
          "actions": ["speak", "log"]
        }
      ]
    }
  ],
  "symbolStrategy": {
    "defaultSource": "ARASAAC search terms",
    "textFallback": true,
    "customMediaPolicy": "teacher-owned local media only unless explicitly approved"
  },
  "teacherNotes": {
    "modeling": "Model key words while speaking; wait; respond to all communication; accept multimodal responses.",
    "evidence": "Teacher can observe selections, repair attempts, comments, and participation.",
    "customisation": "Replace labels/search terms with local vocabulary."
  },
  "sett": {
    "student": "Strengths, preferences, communication opportunities, and access needs without diagnoses or private identifiers.",
    "environment": "Classroom/device/network/partner conditions.",
    "task": "Learning or participation demand and communication moves needed.",
    "tools": "AAC, print, dwell, switch, symbol, partner, and fallback supports."
  },
  "udl": {
    "engagement": ["Meaningful choice", "safe repair/rest route"],
    "representation": ["Text labels", "symbols/photos", "spoken output"],
    "actionExpression": ["AAC selection", "keyboard", "partner-observed response"]
  },
  "differentiation": {
    "content": "Preserve the key learning intent while reducing access load.",
    "process": "Model, wait, repeat, rehearse, and accept multimodal responses.",
    "product": "Accept selection, constructed sentence, print evidence, export, or teacher observation as appropriate.",
    "environment": "Calm, predictable, local-first student mode.",
    "support": "Team review and vocabulary personalisation before use."
  },
  "participationBarriers": [
    {
      "barrier": "Original task assumes speech, handwriting, fine motor control, or fast response.",
      "support": "Offer large AAC targets, repair vocabulary, wait time, and partner modelling."
    }
  ],
  "evidencePlan": {
    "observable": ["selection", "repair attempt", "comment", "participation"],
    "notJudgement": "Access method and support level are context, not curriculum judgement.",
    "export": "Use anonymous local notes, print, CSV, or portfolio summary only when needed."
  },
  "privacy": {
    "level": "anonymous",
    "containsSensitiveData": false
  },
  "attribution": [
    {
      "source": "ARASAAC",
      "licence": "CC BY-NC-SA",
      "note": "Confirm exact current licence wording when publishing beyond local classroom use."
    }
  ]
}
```

## Controlled Values

### Access Profiles

- `direct-selection`
- `eye-gaze-dwell`
- `mouse-dwell`
- `single-switch`
- `two-switch`
- `partner-assisted-print`
- `print-only`
- `keyboard`
- `mixed-access`
- `partner-assisted-scanning`

### Button Roles

- `core`
- `fringe`
- `repair`
- `navigation`
- `comment`
- `question`
- `sentence`
- `evidence`
- `teacher`

Student-facing renderers must not expose `teacher` buttons inside the main student board.

### Communication Functions

- `initiate`
- `request`
- `refuse`
- `choose`
- `comment`
- `ask`
- `answer`
- `sequence`
- `explain`
- `repair`
- `reflect`
- `socialise`
- `navigate`
- `regulate-rest`

Avoid outputs where every button is only `answer` or `label`.

## Access-Density Rules

Use these as validation defaults:

- `eye-gaze-dwell`: 2x2, 2x3, or 3x3 by default; 4x4 only if the prompt says the student/team has tested dense gaze access.
- `single-switch`: 2x2 or 3x3 first; larger grids need row-column scanning and a clear reason.
- `partner-assisted-print`: keep scan order explicit and include partner script.
- `direct-selection`: 3x3 default; 4x4 acceptable for confident direct selectors.
- Intended-access gaze: if `eye-gaze-dwell` or `mouse-dwell` appears in `access.intended` under any profile (including `mixed-access`), the same nine-target default applies. Prefer multiple calm pages with `navigation` buttons over one dense grid. The validator warns when such a board has a page over nine targets without `denseGazeTested`.

## Renderer Mapping

### Single-File HTML

Preserve:

- `title`, `purpose`, `pages`, `buttons`, roles, functions, access settings, teacher notes, attribution, privacy note.
- Use semantic buttons, keyboard fallback, visible focus, and no remote scripts.
- Load `eyegaze-dwell-html` when `access.profile` is `eye-gaze-dwell` or `mouse-dwell`.

### Open AAC Studio JSON

Map:

- `title` -> `name`
- `access` -> `settings` and `accessibility`
- `grid.rows/columns` -> `gridRows/gridColumns`
- `spokenText` -> `audioCue` or `speak-text`
- `function` and `role` -> preserve as extra button fields where supported; otherwise keep in `metadata` or teacher notes.
- `privacy.level` -> `metadata.privacyLevel`
- `attribution` -> `licences`

Set `app` to `Open AAC Studio` only for an app-compatible export. Keep the IR source in a separate file or `metadata.generatedFrom` when producing a resource pack.

### Printable Board

Preserve:

- labels;
- symbol search terms;
- scan/pointing order;
- partner-assisted note;
- attribution;
- black-and-white readability.

## Multi-Page Navigation And Message Bar

Boards with more than one page should make navigation explicit instead of relying on a single dense grid.

- Use `navigation`-role buttons with `function: "navigate"`.
- Encode page moves as dict actions: `{ "type": "next-page", "targetPageId": "page-id" }`, `{ "type": "previous-page", "targetPageId": "page-id" }`, or `{ "type": "navigate-page", "targetPageId": "page-id" }`. The Open AAC Studio renderer preserves these actions.
- Keep a repair/help route reachable on every page, not only the first.
- An optional top-level `navigation` object can record the page model and intent, for example `{ "model": "two-page sentence builder", "pages": ["page-one", "page-two"], "notes": "…" }`.

Sentence builders should actually assemble a sentence, not speak isolated words. Use an optional top-level `messageBar` object plus message action types:

```json
"messageBar": {
  "enabled": true,
  "placeholder": "Build your sentence here.",
  "speakControl": true,
  "clearControl": true,
  "undoControl": true
}
```

- Word buttons add to the bar with `{ "type": "add-to-message", "text": "word" }` (also speak the single word for feedback).
- A Speak control reads the whole bar with `{ "type": "speak-message" }`.
- Undo and clear use `{ "type": "remove-last-word" }` and `{ "type": "clear-message" }`.

`messageBar` and `navigation` are optional design metadata: the validator ignores them and the single-file HTML renderer is responsible for the live behaviour. See `generated/curriculum-sentence-builder/` for a worked two-page example.

## Powerhouse Metadata

These fields are optional for legacy compatibility, but expected for new resource packs:

- `sett`: explicit Student, Environment, Task, Tools design notes without diagnoses or sensitive identifiers.
- `udl`: engagement, representation, and action/expression supports.
- `differentiation`: content, process, product, environment, and support decisions.
- `participationBarriers`: barriers created by the original task and the access supports that remove or reduce them.
- `evidencePlan`: what can be observed/exported, and what must not be treated as curriculum judgement.

Renderers should preserve these fields in metadata even when the target app does not natively understand them.

## Validation Rules

An IR should fail validation if:

- required top-level fields are missing;
- a page has no buttons;
- a button lacks `id`, `label`, `role`, `function`, or `spokenText`;
- access profile and grid density conflict;
- no repair/help/refusal/finished route exists when the board has more than two content buttons;
- the board appears to be a noun/content grid with no agency function;
- the board is answer-only/quiz-only without uncertainty, repair, explanation, or reflection;
- privacy level is not declared;
- attribution is missing when symbols/search terms are used.

The validator should warn, not fail, when `0.3.0` powerhouse metadata is thin. It also warns when `eye-gaze-dwell`/`mouse-dwell` is an intended access method (even under `mixed-access`) but a page exceeds nine targets without `denseGazeTested`. Warnings are still work to do before claiming a resource is differentiated, curriculum-strong, or genuinely usable by the stated access method.

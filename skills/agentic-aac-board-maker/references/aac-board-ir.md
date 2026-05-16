# AAC Board Intermediate Representation

The AAC Board IR is the canonical structure an agent should create before rendering HTML, printable output, or Open AAC Studio JSON.

## Why It Exists

The IR prevents a common failure mode: turning a lesson topic into a pretty noun grid. It makes the agent state the student's communication purpose, access method, button roles, repair options, symbol strategy, and evidence route before visual output.

## Minimal IR

```json
{
  "schemaVersion": "0.2.0",
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

## Validation Rules

An IR should fail validation if:

- required top-level fields are missing;
- a page has no buttons;
- a button lacks `id`, `label`, `role`, `function`, or `spokenText`;
- access profile and grid density conflict;
- no repair/help/refusal/finished route exists when the board has more than two content buttons;
- privacy level is not declared;
- attribution is missing when symbols/search terms are used.


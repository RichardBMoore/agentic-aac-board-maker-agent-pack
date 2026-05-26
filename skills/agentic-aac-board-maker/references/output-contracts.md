# Output Contracts

Use these contracts so generated boards are predictable and reusable. For direct generation, create canonical AAC Board IR first, then render the requested output.

## Contract 0 — Canonical AAC Board IR

Use for the design source of truth. The IR may be delivered alone when the user asks for schema/JSON, or included inside a resource pack beside rendered outputs.

Must include:

- `schemaVersion`;
- `format: "agentic-aac-board-ir"`;
- safe `id` and human-readable `title`;
- `purpose`, `audience`, `access`, and `communicationFunctions`;
- pages/buttons with `role`, `function`, `spokenText`, and `searchTerm`;
- IR 0.3.0 powerhouse metadata: `sett`, `udl`, `differentiation`, `participationBarriers`, and `evidencePlan`;
- symbol strategy;
- teacher notes;
- privacy declaration;
- attribution/licensing notes.

Use `references/aac-board-ir.md` and `templates/board-json-skeleton.json` as the base.

## Contract A — Single-File HTML Board

Use for direct classroom/student use.

Must include:

- one `.html` file with inline CSS/JS;
- no CDN or remote scripts;
- semantic `<button>` elements;
- visible focus;
- keyboard fallback;
- optional TTS with Stop Speech;
- dwell support only when requested/needed;
- print stylesheet if print likely;
- attribution section;
- teacher notes hidden/collapsible or separate from student area;
- no sensitive data unless explicitly required.

Recommended structure:

```html
<header>title + brief student instruction</header>
<main>
  <section class="board" aria-label="AAC board">
    <button>...</button>
  </section>
</main>
<section class="teacher-notes">...</section>
<footer>Attribution</footer>
```

## Contract B — Open AAC Studio-Compatible JSON

Use for Open AAC Studio-style import/testing or conversion. Treat this as a renderer output from the canonical IR, not as the design source.

Must include:

- schemaVersion;
- app/source;
- id/name/type;
- settings;
- accessibility;
- pages/buttons;
- variables if needed;
- metadata/privacy;
- licences/attribution.

Use `../../open-aac-studio-board-builder/references/open-aac-studio-schema.md` for app-specific fields. Preserve IR roles/functions as extra button fields and preserve SETT/UDL/differentiation/evidence metadata under renderer metadata where possible.

Renderer helper:

```sh
python3 scripts/render_open_aac_studio.py <board.ir.json> <open-aac-studio.json>
```

## Contract C — Printable Board

Use for low-tech AAC, laminating, partner-assisted scanning, or paper backup.

Must include:

- title;
- grid/table/card layout;
- large labels;
- optional symbol placeholders/search terms;
- strong borders;
- scan/pointing order if useful;
- partner note;
- attribution;
- black-and-white readability.

## Contract D — Resource Pack

Use for complex curriculum/QCIA resources.

Suggested files:

```text
<slug>/
  README.md
  board.ir.json
  board.html
  open-aac-studio.json
  printable.html
  teacher-notes.md
  attribution.md
```

README should include:

- purpose;
- access method;
- how to use;
- how to customise;
- which file is the source IR;
- privacy note;
- SETT/UDL/differentiation/evidence summary for curriculum or QCIA resources;
- real-device testing note.

## Contract E — Agent Prompt/Skill Update

Use when the requested output is a reusable workflow rather than a board.

Must include:

- trigger conditions;
- intake fields;
- generation workflow;
- output schema;
- pitfalls;
- verification checklist;
- examples.

## File Naming

Use safe, descriptive filenames:

- no student names unless explicitly requested;
- lowercase slug where possible;
- include access/output type if useful.

Examples:

```text
year7-hero-speech-aac-board.html
qcia-community-access-choice-board.json
hpe-respectful-relationships-print-board.html
```

## Final Response Contract

When returning a generated file:

```text
Made: <file/resource>
Saved at: <path>
Access: <touch/keyboard/gaze/switch/print>
Communication purpose: <functions>
Curriculum/QCIA link: <brief>
Use/check: <how to open or print>
Caveat: test with actual student/device/team before relying on it.
```

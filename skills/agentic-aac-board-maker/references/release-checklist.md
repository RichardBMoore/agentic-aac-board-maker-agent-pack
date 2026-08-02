# Release Checklist

Use this when preparing the pack for distribution as a Codex plugin or as standalone skill folders.

## Plugin Release Gate

The plugin root must include:

- `.codex-plugin/plugin.json`;
- `skills/` with installable skill folders;
- each skill folder has `SKILL.md`;
- each key skill has `agents/openai.yaml`;
- scripts are executable when intended;
- generated/cache files are excluded by `.gitignore`;
- `scripts/check_pack.py` passes with `requirements-dev.txt` installed.
- unit and Playwright browser tests pass.

Run:

```sh
.venv/bin/python scripts/check_pack.py
.venv/bin/python -m unittest discover -s tests
npm run test:browser:chrome
```

## Standalone Skill Release Gate

For each standalone skill folder:

- `SKILL.md` frontmatter has only supported top-level fields;
- `name` is lowercase hyphen-case;
- `description` clearly states when to use the skill;
- `SKILL.md` stays lean and routes detail to `references/`;
- `agents/openai.yaml` exists for UI metadata;
- references are one level deep and named from `SKILL.md`;
- scripts referenced by the skill exist and compile;
- bundled assets are either templates/resources or clearly documented.

## Agentic AAC Release Gate

Before saying the agentic board workflow is usable:

1. Create an IR fixture for each proof-of-concept prompt.
2. Keep each generated fixture as a small resource pack containing:
   - `*.ir.json` as the source of truth;
   - matching `*.open-aac-studio.json` renderer output;
   - matching `*.html` classroom/print/digital output;
   - `README.md` explaining use, access assumptions, and draft-status caveats.
3. Require canonical IR 0.4.0 and pass JSON Schema plus `scripts/validate_board_ir.py`.
4. Fresh-render HTML/Open AAC Studio/OBF outputs and fail byte drift.
5. Pass HTML/IR/shared-runtime parity.
6. Include powerhouse and `systemFit` metadata where practical.
7. Run static HTML/eye-gaze checks and Playwright device-viewport interaction QA.
8. Evaluate newly generated candidate folders with `scripts/evaluate_fresh_output.py`.
9. Review symbols as candidates; apply only approved ids.
10. Review against `qa-rubric.md` and `anti-patterns.md`, recording the owning reference when a fixture fails.

`python3 scripts/check_pack.py` now enforces the generated-fixture regression gate for every `generated/**/*.ir.json` and static generated HTML access/offline checks for every `generated/**/*.html`.

## Versioning Guidance

- Increment the plugin version when distribution metadata, skill routing, or release tooling changes.
- Increment the IR schema version when the canonical IR shape changes.
- Keep Open AAC Studio compatibility schema version separate from the canonical IR version.
- Do not silently change renderer output fields without updating `aac-board-ir.md` or Open AAC Studio schema notes.

## Do Not Ship If

- pack checks fail;
- generated resources require internet when described as offline;
- IR and renderer outputs disagree on access method or button functions;
- canonical IR, fresh-render or HTML/runtime parity fails;
- a proof-of-concept fixture produces quiz-only or noun-only communication;
- a new generated fixture lacks SETT/UDL/differentiation/evidence metadata without a clear reason;
- private student data appears in sample prompts, filenames, logs, or generated examples;
- a gaze/dwell resource has no cancellation/progress path;
- total active-target accounting or browser/device interaction QA fails;
- final language implies clinical prescription or a tested AAC system when it is only a draft classroom support.

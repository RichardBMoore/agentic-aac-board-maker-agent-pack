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
- `scripts/check_pack.py` passes.

Run:

```sh
python3 scripts/check_pack.py
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
3. Validate every generated IR with `scripts/validate_board_ir.py`.
4. Render every generated IR with `scripts/render_open_aac_studio.py` and confirm the output has pages/buttons.
5. Build at least one single-file HTML output and check it opens.
6. For dwell HTML, run the eye-gaze HTML checker.
7. Review against `qa-rubric.md` and `anti-patterns.md`.
8. Record which reference file changed when a fixture fails.

`python3 scripts/check_pack.py` now enforces the generated-fixture regression gate for every `generated/**/*.ir.json`.

## Versioning Guidance

- Increment the plugin version when distribution metadata, skill routing, or release tooling changes.
- Increment the IR schema version when the canonical IR shape changes.
- Keep Open AAC Studio compatibility schema version separate from the canonical IR version.
- Do not silently change renderer output fields without updating `aac-board-ir.md` or Open AAC Studio schema notes.

## Do Not Ship If

- pack checks fail;
- generated resources require internet when described as offline;
- IR and renderer outputs disagree on access method or button functions;
- a proof-of-concept fixture produces quiz-only or noun-only communication;
- private student data appears in sample prompts, filenames, logs, or generated examples;
- a gaze/dwell resource has no cancellation/progress path;
- final language implies clinical prescription or a tested AAC system when it is only a draft classroom support.


# Working on this pack

Guidance for AI agents (Codex, Claude Code) and people changing this repository. For using the pack to make a board, read `skills/agentic-aac-board-maker/SKILL.md` instead.

## What this repository is

A plugin for Claude Code and Codex that turns a teacher's request into a draft AAC board. The repository root is the plugin root for both hosts.

| Path | What it holds |
| --- | --- |
| `skills/` | Seven skills. `agentic-aac-board-maker` is the main one and owns the board format, house standards, renderers and validators |
| `agents/aac-board-qa.md` | Claude Code subagent that reviews a finished board |
| `hooks/` | Claude Code `PostToolUse` hook that checks board files as they are written |
| `generated/` | Seven example boards. They are also the golden regression fixtures |
| `scripts/check_pack.py` | The release gate |
| `tests/`, `browser-tests/` | Python unit tests and Playwright interaction tests |
| `.claude-plugin/`, `.codex-plugin/` | Plugin manifests and the Claude marketplace entry |

## Rules

1. **Do not hand-edit built files.** That covers every `*.ir.json`, `*.html`, `*.obf`, `*.obz`, `*.open-aac-studio.json` and `partner-card.html` under `generated/`. Change the renderer, the shared runtime or the house data, then rebuild (see below). The gate fails on any drift.
2. **Do not open built files to read them.** A built `*.ir.json` or board HTML is about 80% embedded picture data and 300-450 KB. Use `python3 skills/agentic-aac-board-maker/scripts/inspect_board.py <file.ir.json>`.
3. **One runtime.** `skills/agentic-aac-board-maker/assets/aac-board-runtime.js` is embedded in every board. Changing it changes every example, so rebuild them all and run the browser tests.
4. **No student data** in examples, tests, filenames, prompts or commit messages. Examples stay de-identified.
5. **Australian English** in everything a teacher or student reads.
6. **Skills stay usable on their own.** A script may import its neighbours in the same skill's `scripts/` folder. When it reaches into another skill, it must skip that step with a clear message if the other skill is not there.
7. **Keep the plugin installable everywhere.** Do not add a `bin/` folder at the repository root (claude.ai and Cowork refuse plugins that have one) or a `CLAUDE.md` at the repository root (plugin validation warns, and CI treats warnings as failures). Hooks are a safety net only: `build_board.py` must enforce every check itself, because some hosts do not run plugin hooks.
8. **Two copies of the screen-fit constants** exist, in `skills/agentic-aac-board-maker/scripts/display_fit.py` and `skills/accent-display-fit/scripts/check_accent_display.py`. Change both together; `tests/test_display_fit.py` fails if they differ.

## Commands

```sh
python3 -m venv .venv && .venv/bin/python -m pip install -r requirements-dev.txt && npm ci   # once

.venv/bin/python scripts/check_pack.py               # release gate
.venv/bin/python -m unittest discover -s tests       # unit tests
npm run test:browser:chrome                          # real-browser tests (installed Chrome)

claude plugin validate . --strict                            # checks the marketplace entry only
claude plugin validate .claude-plugin/plugin.json --strict   # checks the plugin, skills, agent and hooks
```

Run all three test commands before saying a change works. Say which ones you ran and which you did not.

## After you change something

- **Renderer, runtime, house layout, word list or symbols:** rebuild every example, then run the gate and the browser tests.

  ```sh
  for ir in generated/*/*.ir.json; do
    python3 skills/agentic-aac-board-maker/scripts/build_board.py "$ir" --quiet || break
  done
  ```

- **Validator rules:** add a test, and check that all seven examples still pass with no new warnings.
- **Skill instructions (`SKILL.md`, references):** the gate checks that backticked paths beginning `scripts/`, `references/`, `templates/`, `fixtures/` or `assets/` exist. To judge whether the instructions still produce good boards, have a fresh agent answer the six benchmark prompts in `skills/agentic-aac-board-maker/fixtures/proof-of-concept-prompts.json` and score the result with `skills/agentic-aac-board-maker/scripts/evaluate_fresh_output.py`.
- **A bug in one generated board:** fix the rule, renderer or reference that allowed it, not only the board.

## Releasing

The version appears in five files and must match: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, `package.json` and `package-lock.json` (twice). Add a `## X.Y.Z - YYYY-MM-DD` entry to `CHANGELOG.md`. Installed copies of the plugin stay on their version until this number changes.

## What cannot be checked from this repository

A real PRC-Saltillo Accent, the EQ-managed network and Edge policies, real installed voices, a student's eye-gaze calibration, print pagination, and plugin hooks running inside a live Codex session. Say so when a change touches them.

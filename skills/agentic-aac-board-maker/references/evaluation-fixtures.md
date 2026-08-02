# Evaluation Fixtures

Use these fixtures to check whether the skill stack helps different agents generate useful AAC resources from short teacher prompts.

Each fixture should produce:

- board plan;
- canonical AAC Board IR JSON;
- final resource output;
- teacher notes;
- symbol/search-term strategy;
- access notes;
- QA notes.

## Fixture Set

| ID | Prompt | Expected Output | Key Risks |
|---|---|---|---|
| `gaze-choice-2x2` | Make an eye-gaze choice board for choosing a class activity. | Single-file HTML + IR. 2x2 or 2x3, dwell-safe. | Over-dense grid; no dwell cancellation; no Help/Finished. |
| `qcia-community-shops` | Create a QCIA community access board for going to the shops. | Resource pack or HTML + printable. Practical communication and evidence note. | Becomes noun list; weak safety/help language. |
| `curriculum-sentence-builder` | Make a Year 7 English hero speech sentence-builder board. | Multi-page HTML or JSON + teacher notes. | Waters down speech task; no because/opinion/rehearse path. |
| `visual-schedule-expressive` | Make a morning routine visual schedule with expressive options. | Printable or HTML visual schedule. | Misrepresents schedule as full AAC; no Wait/Help/Change. |
| `needs-repair-board` | Make a respectful needs and communication repair board for a secondary student. | HTML/print board. Age-respectful language and privacy-safe. | Infantilising wording; behaviour-control framing. |
| `partner-assisted-print` | Make a printable partner-assisted scanning board for help, stop, different, finished, and choices. | Printable board with scan order and partner script. | No partner instructions; poor black-and-white print. |

## Minimum Passing Criteria

An agent passes the fixture if:

1. It creates the IR before or alongside the final resource.
2. It includes at least one repair/escape pathway.
3. It matches density to access method.
4. It preserves student agency beyond adult-controlled answers.
5. It includes attribution and privacy notes.
6. It produces a file that parses or opens.
7. It reports caveats honestly as draft classroom support.

## Fresh-Output Harness

Run the harness against newly generated candidate folders, not only `generated/` golden examples:

```sh
python3 scripts/evaluate_fresh_output.py <candidate-root> --report evaluation-report.json
```

Each candidate subfolder must use the fixture id and contain one canonical `*.ir.json`, HTML and teacher notes. The harness checks JSON Schema, semantic quality, HTML/IR/shared-runtime parity and the structured expectations in `fixtures/proof-of-concept-prompts.json`.

## Regression Rule

When a generated resource fails a fixture, patch the owning reference file:

- communication/agency failure -> `evidence-base.md`, `board-grammar.md`, or `qa-rubric.md`;
- access failure -> `access-methods.md` or `eyegaze-dwell-html`;
- schema/output failure -> `aac-board-ir.md` or `output-contracts.md`;
- curriculum/QCIA failure -> `curriculum-qcia-translation.md`.

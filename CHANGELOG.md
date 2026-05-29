# Changelog

All notable changes to this project will be documented in this file.

## 0.3.0 - 2026-05-29

- Rebuilt the `curriculum-sentence-builder` proof of concept as a genuine two-page sentence builder: a running sentence/message bar, Speak sentence / Undo / Start again controls, and `navigation` buttons. It now delivers the multi-page and rehearse/speak behaviour the evaluation fixtures already expected, instead of speaking single words in isolation.
- Split the `needs-repair-board` proof of concept into two gaze-safe pages (no more than nine targets each) with navigation and Help on every page, preserving all twelve self-advocacy and repair messages. This removes a dense 12-target grid that contradicted the eye-gaze density guidance.
- Closed a gaze-density validation gap in `validate_board_ir.py`: boards that list `eye-gaze-dwell`/`mouse-dwell` in `access.intended` under a non-gaze profile (for example `mixed-access`) now warn when a page exceeds nine targets without `denseGazeTested`, matching the anti-patterns and access-density evidence. Added a `mixed_gaze_dense` regression fixture and test.
- These two generated examples are the first to exercise multi-page navigation and the renderer's `next-page`/`previous-page` actions, so the regression fixtures now cover navigation as well as single-page boards.
- Documented the optional `messageBar` and `navigation` IR objects and the multi-page density rule in `aac-board-ir.md`, and aligned `skills/agentic-aac-board-maker/references/examples.md` with the shipped sentence builder.

## 0.2.0 - 2026-05-25

- Added `icp-backwards-mapping-assessment` for ICP backwards maps, adapted assessments, rubrics, evidence packages, teaching sequences, and moderation notes.
- Refreshed `build-aac-student-supports` from the Inclusive Education Toolkit plugin.
- Refreshed `eyegaze-dwell-html` with the current single-file dwell HTML guidance for PRC-Saltillo Accent devices and Education Queensland network constraints.
- Updated plugin metadata and README coverage for ICP and broader inclusive education workflows.

## 0.1.0 - 2026-05-16

- Prepared the Agentic AAC Board Maker pack as a private GitHub working repo.
- Added Codex plugin metadata, skill folders, generated proof-of-concept resources, validation scripts, and GitHub release checks.
- Kept generated boards as regression fixtures for AAC Board IR validation and Open AAC Studio rendering.
- Added privacy guidance for de-identified classroom resource drafting.

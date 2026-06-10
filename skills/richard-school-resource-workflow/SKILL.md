---
name: richard-school-resource-workflow
description: "Richard's school-resource workflow for accessible, curriculum-strong resources including ICP/QCIA assessments, eye-gaze/dwell HTML apps, AAC supports, adaptive gaming, bilingual/EALD scaffolds, and multi-platform AI handoffs. Use when building, reviewing, planning, or improving school resources for Richard."
---

# Richard School Resource Workflow

Use this skill whenever Richard asks for help with school resources, accessible HTML tools, ICP/QCIA assessments, AAC/eye-gaze resources, adaptive gaming, AI-assisted resource production, or cautious organisation/auditing of school-resource folders containing student/evidence materials.

## Privacy note

This skill carries Richard's personal workflow context, including local paths and personal document categories. Exclude or generalise this skill folder before sharing the pack beyond Richard's own machines.

## Working stance

- Be practical, honest, and balanced — not sycophantic.
- Give a short plan before coding/building resources.
- Treat access to curriculum as a human right.
- Do not call a resource done unless it is both accessible in practice and curriculum-strong.
- Preserve cognitive/curriculum demand where possible; remove access barriers, not learning intent.
- Prefer usable files and clear caveats over vague pedagogical praise.

## Richard's workflow context

Richard uses a multi-platform AI workflow:

- Custom GPTs for curriculum alignment.
- Claude/Anthropic/Coworkers for educational structure, collaboration style, and strong drafting.
- Codex for coding.
- Gemini for UI/UX improvement.
- Hermes as local orchestrator, file inspector, builder/reviewer, accessibility checker, and handoff generator.

## Default response flow for builds

Before coding or changing files:

1. Restate the goal briefly.
2. Give a short plan in 3–6 bullets.
3. State assumptions/trade-offs.
4. Wait for go-ahead unless Richard clearly says "just build it" or similar.

When executing after approval:

1. Work on a copy unless explicitly asked to edit the original.
2. Avoid touching unrelated files.
3. Keep offline/single-file constraints when relevant.
4. Verify by reading the file and, where practical, opening/checking it in browser.
5. Report exactly what changed and any remaining limitations.

## Definition of done

A resource is done when it is:

- accessible in the actual student/device context;
- curriculum-strong, not watered down;
- usable by the target student or teacher;
- defensible for ICP/QCIA/APST/QCAA purposes where relevant;
- checked for obvious barriers: keyboard, dwell/eye-gaze, screen layout, contrast, no accidental high-stakes activation;
- honest about limitations.

## Common work types

### At-level English/curriculum scaffolds

Use `references/scaffold-design-patterns.md` when Richard asks for English, Essential English, assessment, vlog/script, feature article, writing, or other curriculum scaffolds. Use `references/bilingual-eald-support-patterns.md` as well when the scaffold involves bilingual/EALD support, home-language drafting, translated task access, or teacher evidence from responses written partly or wholly in another language.

Key distinction: highly scaffolded does **not** automatically mean ICP or modified curriculum. Richard's at-level scaffolds often keep the original task demand and reveal the pathway through structure, examples, glossary/metalanguage, sentence starters, success criteria, TTS/STT, autosave, and export.

Principle: **scaffold the route, not the rigour.**

Default pattern:
- preserve the original assessment expectation unless Richard explicitly asks for ICP/adapted level;
- chunk the task into meaningful sections aligned to the actual assessment sequence;
- name each section's purpose;
- provide models, sentence starters, glossary/metalanguage, and final checklist;
- embed marking-guide/success-criteria reminders at point of need;
- include practical access supports such as read-aloud, dictation where useful, autosave, print/export, high contrast, and focus mode;
- avoid over-scaffolding so every student response sounds identical.

### Bilingual/EALD curriculum supports

Use `references/bilingual-eald-support-patterns.md` when Richard asks for Thai, Japanese, EAL/D, home-language, translation, bilingual exam, or multilingual curriculum supports.

Principle: **use the student's home language to open the curriculum door while keeping evidence connected to the same curriculum thinking.**

Default pattern:
- keep the original task, cognitive verb, and curriculum metalanguage visible unless Richard explicitly requests modified/ICP work;
- translate the access layer: instructions, stimulus text, task verbs, key vocabulary, and process steps;
- provide bilingual glossary, word bank, and sentence starters that scaffold analysis/explanation rather than giving a complete answer;
- allow home-language drafting where appropriate, then preserve the original response plus any English translation/export for teacher judgement;
- separate calm student-facing support from teacher-facing rubric, comments, report, and translation-status tools;
- label Google Translate/browser translation as optional, internet-dependent, and needing teacher judgement rather than treating it as authoritative;
- keep English and the home language visually separated with paired lines/cards/toggles so bilingual text does not become clutter.

### Purpose-built ICP/AAC scaffolds

Use `references/scaffold-design-patterns.md` together with `references/icp-qcia-checklist.md` when Richard asks for ICP/AAC scaffolds for a specific student.

Principle: **translate the assessment into accessible communication.**

Default pattern:
- confirm ICP level, shared class task, assessment mode, and evidence requirements;
- identify communication functions: choose, sequence, express opinion, explain because, ask, answer, rehearse, record;
- convert task requirements into AAC/core-word/sentence-builder moves rather than only text boxes;
- provide rehearsal, playback, recording, export/print/report, and teacher judgement evidence;
- keep student agency through own-choice/editable options where practical;
- remember that purpose-built specificity can be the access feature.

### Accessible HTML tools

Use `eyegaze-dwell-html` when eye gaze/dwell/AAC/offline HTML is involved. Do **not** add dwell/eye-gaze interaction just because a resource is QCIA or accessible; if Richard says it does not need eye gaze, or the access context is ordinary click/tap/keyboard, build a simpler large-button interactive resource with keyboard support and visible focus instead.

Default assumptions:
- Single self-contained HTML unless assets are explicitly requested.
- No CDN/internet dependency for EQ network use.
- Microsoft Edge, `file:///`, Windows, PRC-Saltillo Accent devices where eye gaze is involved.
- Keyboard fallback.
- Visible focus for all interactive controls.
- Large but screen-fit targets.
- For offline visual resources, embedded SVGs as base64 data URIs are a practical way to include images without external files, provided they are simple, relevant, and have useful alt text.

For curriculum-aligned accessible HTML builds:
- Ground the task in current official curriculum/QCAA sources before drafting content when the user names a curriculum version, subject, and year level.
- Preserve the achievement-standard intent in the interaction design; use large guided selections, sentence builders, scenario choices, or teacher evidence panels to reduce access load without removing analysis/evaluation demand.
- Include teacher-facing curriculum alignment inside the resource when useful, but keep the student/player surface calm and uncluttered.
- Verify both curriculum strength and technical access: no external dependencies, dwell cancellation, keyboard fallback, high-stakes confirmation, browser console free of errors, and response/export path works.

### ICP assessments

When writing or adapting ICP assessments:
- Ask/confirm ICP level, subject, year level, curriculum intent, assessment mode, and expected evidence.
- Preserve curriculum alignment and cognitive verbs.
- Adjust access, language, scaffolding, and response mode rather than simply lowering expectations.
- Produce teacher-ready and student-ready versions when useful.

### QCIA resources

When building QCIA materials:
- Link activity evidence to learning goals.
- Prefer practical, observable evidence.
- Use clear student-friendly language but maintain defensible documentation for teachers/QCAA.
- Consider folio evidence, photos, work samples, teacher observations, reflection prompts, and reports.

### Adaptive gaming

When switch/joystick/gamepad access is involved:
- Check hardware assumptions: HORI FlexController, Pretorian Optima joystick, switch count, XInput mapping.
- Use Gamepad API polling, not event assumptions.
- Include keyboard fallback where practical.
- Keep the game genuinely engaging; don't make a thin educational wrapper if the goal is engagement.

### Multi-AI handoffs

Hermes can generate:
- Claude/Cowork brief for educational structure and scaffolding.
- Codex implementation brief with file paths and acceptance tests.
- Gemini UI/UX pass brief with concrete layout/accessibility goals.
- Final Hermes QA checklist.
  
### School/professional folder audits and cleanup

When Richard asks to organise, clean up, audit, index, deduplicate, review, or rename school-resource folders, professional evidence folders, university/application dossiers, or education-work folders:
- Start with a read-only audit; do not change the target folder until explicitly approved.
- If an expected folder is not found by simple path/glob search on macOS, use Spotlight `mdfind` with case-insensitive name fragments before asking Richard where it is.
- Save proposals, indexes, manifests, and audit data outside the target folder first, e.g. under `~/.hermes/work/`.
- Include a machine-readable manifest (CSV or JSON) plus a human-readable Markdown report when the folder has enough contents to warrant review.
- For small application/dossier folders, summarise structure, document purpose, missing placeholders, draft/version flags, and immediate next review targets rather than proposing cleanup for its own sake.
- For `.docx` files, lightweight text preview can be extracted read-only from `word/document.xml` inside the zip when a quick content check is useful; avoid full conversion unless needed.
- Treat student files, photos, QCIA evidence, APST/QCT evidence, parent emails, payslips, application materials, transcripts, recommendations, CVs, statements of purpose, and assessment materials as privacy-sensitive.
- Prefer staged approval gates: low-risk metadata cleanup/indexing first, then scaffolds, then small reviewed archive/rename batches.
- Do not delete by default, even when a separate backup exists; generate a manifest/rollback list before destructive or hard-to-reverse actions.
- Use exact hashes for duplicate detection, but do not assume exact duplicates are safe to delete because evidence-packaged copies may be intentionally duplicated.
- For version-sprawl patterns like `backup`, `copy`, `OLD`, `DELETE_`, `Archives`, and `DUPLICATE`, label as review candidates rather than acting on names alone.
- Rename only when it improves retrieval/clarity, and batch proposed renames with original path, proposed path, reason, and risk level.
- When the user asks to leave a folder alone (e.g. QCIA, Full Registration, student/evidence folders), add it to an explicit exclusion list and show that exclusion in every report/proposal.
- For low-risk cleanup, prefer this sequence: remove/quarantine metadata files only after approval; create `_CURRENT_INDEX/`; copy generated indexes/reports there; create `_ARCHIVE_REVIEW/`; then move only a tiny approved batch of obvious backup/copy files.
- For archive moves, preserve the original relative path under `_ARCHIVE_REVIEW/`, hash before/after move, verify source removal and destination existence, and save a rollback manifest outside the school folder.
- Avoid moving files that are already in an archive folder unless doing so clearly improves retrieval; sometimes indexing an existing archive is better than reshuffling it.

## Red flags to call out

- Pretty UI but weak access.
- Large targets that cause constant scrolling.
- Eye-gaze tasks requiring excessive text entry.
- Touch-only assumptions.
- One-hover destructive actions like submit/reset/delete.
- Student data stored unnecessarily.
- External dependencies in offline/EQ resources.
- Assessment simplification that removes the intended cognitive demand.
- Overbuilt features that make classroom use harder.

## Useful linked references

- `references/resource-intake.md`
- `references/accessibility-qa.md`
- `references/icp-qcia-checklist.md`
- `references/multiai-handoff.md`
- `references/scaffold-design-patterns.md` — Richard-specific distinction between at-level scaffolds and purpose-built ICP/AAC scaffolds, with reusable build patterns.

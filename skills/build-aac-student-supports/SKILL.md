---
name: build-aac-student-supports
description: Build accessible AAC, eye-gaze, dwell, switch-scanning, symbol-supported, printable, and classroom-ready student supports as the access, communication, interface, and tool-construction layer. Use when creating or adapting choice boards, communication boards, visual schedules, first-then boards, symbol-supported curriculum tools, quizzes, story/book readers, writing supports, Boardmaker-style resources, single-file offline HTML tools, PRC-Saltillo Accent/Edge resources, QCIA/EQ Network resources, or any student tool that must work with touch, keyboard, mouse dwell, eye gaze, switches, TTS, symbols, local privacy, Microsoft Edge file URLs, and offline school networks. For generating a complete AAC board end to end from teacher intent, start with agentic-aac-board-maker instead; for the single-file eye-gaze/dwell HTML mechanics themselves, defer to eyegaze-dwell-html.
---

# Build AAC Student Supports

Create practical classroom supports for students with complex communication or access needs. Treat access, communication rights, privacy, and reliability as core product requirements, not extras added after the interface is finished.

Keep this workflow distinct from ICP assessment adaptation:

- AAC/accessibility student-support building is the access, communication, interface, interaction, and tool-construction layer.
- ICP assessment adaptation is the curriculum, evidence, standards, moderation, and judgement layer.
- When AAC supports are being used for ICP or curriculum evidence, apply the ICP workflow first to decide what curriculum evidence is being collected and whether the adapted task is defensible. Then use this skill to decide how the student will access, communicate, complete, and export that task.
- Do not reduce assessment evidence to isolated quiz answers. Translate curriculum work into accessible communication moves such as choose, sequence, express an opinion, explain with "because", ask, answer, rehearse, record, reflect, direct, evaluate, and revise.

## Working Stance

- Build with the student, teacher, SLP, OT, aide, and family context in mind. Do not present the output as clinical assessment or a replacement for specialist advice.
- Preserve the student's voice and agency. Avoid turning AAC into only quiz answering, compliance, or behaviour control.
- Support multimodal communication: speech, gestures, symbols, objects, photos, text, partner-assisted strategies, eye gaze, switches, touch, and keyboard can all coexist.
- Do not make any generated support the student's only communication method or emergency-call method.
- Default to local-first and anonymous. Store names, profiles, session logs, or sensitive notes only when explicitly needed.

## Workflow

1. Identify the support pattern: communication board, choice board, yes/no, first-then, visual schedule, quiz, matching/sorting, story reader, writing support, social script, pain/needs board, or evidence/logging task.
2. Identify access needs: touch, mouse, keyboard, eye gaze with dwell, mouse dwell, single switch, two switch, partner-assisted scanning, high contrast, auditory cues, print, offline, or file-only launch.
3. Design the activity data before the interface. Use stable IDs for activities, pages, buttons, symbols, actions, settings, attribution, and logs.
4. Separate teacher/editing controls from student/player mode. Student mode should be calm, large, predictable, lockable, and hard to accidentally break.
5. Keep teacher assessment, reporting, and editing controls available but separate from the student-facing workflow.
6. Build the smallest complete usable tool, then add polish only after access works.
7. Verify the tool with keyboard, pointer, dwell cancellation, scan order, contrast, text fit, TTS, offline behaviour, and print/export paths.

## Reference Routing

- Read `references/student-support-patterns.md` when choosing board types, vocabulary, symbol strategies, or classroom workflows.
- Read `references/eye-gaze-and-switch.md` when deciding access behaviour for eye gaze, dwell, switch scanning, PRC-Saltillo Accent devices, Microsoft Edge, file URLs, or accidental activation risk.
- Read `references/eye-gaze-html-tools.md` when building a single-file dwell-activated HTML resource for PRC-Saltillo Accent/Edge, Microsoft Edge, `file:///`, EQ/offline networks, or hover-based gaze access.
- Read `references/templates.md` when implementing the dwell button CSS, `DwellManager`, confirmation modal, speech helper, layout snippets, or QA snippets for single-file gaze HTML.
- Read `references/activity-schema.md` when creating JSON activities, templates, action models, logs, or import/export formats.
- Read `references/open-boardmaker-asset.md` when reusing the bundled Boardmaker-style editor/player in `assets/open-boardmaker-classroom-pack/`.
- Read `references/source-notes.md` when checking the reasoning behind AAC, access, WCAG, ARASAAC, and device guidance.
- Copy `assets/eye-gaze-single-file-template.html` as the starter for one-off dwell HTML tools, then replace activity data and labels.
- Run `scripts/check_eye_gaze_html.py <file.html>` against generated single-file gaze tools when practical.

## Default Build Choices

- Use Australian English unless the user asks otherwise.
- Prefer a self-contained HTML file when the resource must run from `file:///`, on a school network with no CDN, or on a dedicated AAC device.
- For single-file gaze HTML, keep all CSS, JS, symbols, and optional audio inline. Do not use CDNs, remote fonts, external scripts, module imports, or network symbol fetches during student use.
- For student-facing gaze HTML, prefer fullscreen: attempt it once at startup, provide a gaze-sized **Full screen** button, and keep F11/non-fullscreen fallback guidance. Treat automatic or enforced fullscreen as an Edge policy/kiosk deployment decision, not a power the page gains merely by being on the EQ network.
- Prefer the bundled Boardmaker asset when the user wants a reusable editor/player, activity library, starter templates, offline symbol preparation, or printable boards.
- Use semantic HTML buttons for student controls. Avoid canvas-only interaction unless there is a strong reason and a full accessible parallel control path exists.
- Use JSON for activity data rather than hard-coded board state.
- Use ARASAAC as the default free symbol source for non-commercial educational resources, but preserve the exact license and attribution required by the source.
- Allow teacher-owned custom images for local people, places, routines, equipment, and student-specific vocabulary.
- Cache app files and symbols for offline use when possible. Keep text labels usable when images or TTS fail.
- For hover/dwell controls, start dwell from pointer or mouse entry, cancel on leave, show progress, and keep Enter/Space as the keyboard activation path.

## Access Baselines

- Make every interactive student target operable by pointer and keyboard.
- Keep visual order, DOM order, focus order, and scan order aligned.
- Use visible focus, hover, dwell, selected, and scan states.
- For ordinary AAC boards, start around 96 px minimum targets. For gaze-heavy boards, prefer 120 to 200 px targets with at least 20 px gaps when the screen can support it.
- Use dwell timing as a student-tuned setting. A good starting range is 800 to 1200 ms; use 600 ms only for confident gaze users and 1000 to 1500 ms when accidental activation is common.
- Never require a destructive or high-stakes action from one accidental dwell. Use a confirm screen, second dwell, undo, or safe cancel path.
- For switches, support linear scan first. Add row-column scan for larger grids. Provide Start/Stop Scan, Step, Select, scan speed, and Escape-to-stop where keyboard is available.
- Provide colour plus another signal for correct/incorrect, selected, error, and completion states.
- Keep main player boards on screen without unnecessary scrolling. Reduce chrome before shrinking access targets.
- In fullscreen, hide the fullscreen launch control to remove an unnecessary gaze target; show it again if fullscreen exits.

## Eye-Gaze, Dwell, And Fatigue

- Use an audio-first / eyes-rest-then-look pattern for eye-gaze users: speak or play the prompt, allow rest away from the target field, then invite the student to look/select.
- Count each dwell selection, including multi-selects, confirmations, edits, and navigation, as gaze-fatigue cost. Reduce avoidable selections.
- Make dwell cancel immediate on pointer leave or focus loss. Provide visible progress without demanding constant visual tracking.
- Use teacher click-only controls when dwell access would increase accidental activation, Midas-touch risk, or accidental changes to assessment/reporting settings.
- Build rest, pause, replay, undo, and safe cancel routes into student mode.
- Keep student-facing workflows calm, predictable, and low pressure; avoid timed penalties unless timing is the construct.

## Evidence And Export

- Treat print/export as a session-end backup when localStorage, browser persistence, device restarts, or school network profiles may be fragile.
- For curriculum evidence tools, capture only what is needed: activity, prompt/page, selected label or response, access method, support level if relevant, timestamp, and teacher note.
- Keep motor/access support visible in logs without converting it into curriculum judgement.
- Provide readable print/PDF summaries, CSV/JSON exports, screenshots, or portfolio-friendly summaries when evidence needs to leave the device.
- Do not store student names or identifiable notes unless explicitly needed; use anonymous labels by default.

## Privacy And Safety

- Do not send student names, diagnoses, school IDs, behaviour notes, disability notes, medical notes, or family details to external services unless the user explicitly requests it and the risk is clear.
- Use anonymous sessions by default. If profiles are needed, keep them local and make Clear Data visible.
- Keep logs minimal: timestamp, activity, page, selected label, access method, and result are usually enough.
- Make exports deliberate and visible: JSON for activities, CSV or plain text for session summaries.
- Avoid AI-generated personalised symbols for real students unless the user explicitly asks and no sensitive student context is sent externally.

## Classroom-Ready Check

Before calling the support finished, confirm:

- The intended access method works, and keyboard fallback also works.
- Dwell starts on entry, shows progress, activates once, and cancels immediately on leave or focus loss.
- Switch scanning highlights in a predictable order and can be stopped.
- Targets are large enough for the intended access method and do not force routine scrolling.
- Text fits inside buttons on mobile and desktop sizes.
- TTS can be stopped and does not overlap uncontrollably.
- Symbols have text fallback and attribution.
- The support still makes sense without internet, colour, speech, or fine motor precision.
- Teacher controls are separate from the student player.
- The fullscreen startup attempt, direct click/keyboard path, blocked-state fallback, and staff exit route work on the target Edge device.
- Print/export output is readable if it is part of the request.

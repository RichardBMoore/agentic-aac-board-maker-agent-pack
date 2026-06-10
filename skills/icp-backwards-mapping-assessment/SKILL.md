---
name: icp-backwards-mapping-assessment
description: Design, review, or improve Individual Curriculum Plan (ICP) backwards maps, adapted mainstream assessments, year-level progression maps, rubrics, evidence packages, teaching sequences, moderation notes, and access-aware judgement tools. Use when the user asks for ICP curriculum alignment, Australian Curriculum or Queensland P-10 ICP assessment design, achievement-standard evidence, differentiated assessment, AAC-supported evidence routes, movement-task alternatives, teacher-observed or portfolio evidence, student-facing scaffolds, teacher-facing mapping tables, or defensible adjustments for students working above or below enrolled year level.
---

# ICP Backwards Mapping and Assessment

## Core Purpose

Backwards map from the curriculum judgement to the assessment evidence, task conditions, teaching sequence, and access pathways.

Keep this workflow distinct from AAC/accessibility resource building:

- ICP assessment adaptation is the curriculum, evidence, standards, moderation, and judgement layer.
- AAC/accessibility student-support building is the access, communication, interface, interaction, and tool-construction layer.
- When a task needs both, answer the ICP question first: "What curriculum evidence are we collecting, and is this adapted task defensible?" Then answer the access question: "How will the student practically access, communicate, complete, and export the task?" Once the curriculum decision is settled, load `build-aac-student-supports` — or `eyegaze-dwell-html` for gaze HTML — for the access layer.

Use this order:

1. Identify the target achievement standard aspect or approved ICP learning focus.
2. Compare the enrolled-year task or achievement standard with the intended ICP level.
3. Trace the year-level curriculum progression to the approved ICP target.
4. Define the observable evidence needed for a defensible judgement.
5. Name the curriculum construct being judged.
6. Separate the construct from the original task's format baggage.
7. Decide whether the task should be adjusted, substantially scaffolded, or rebuilt.
8. Design the evidence route and task conditions that will generate the evidence.
9. Plan teaching and learning that prepares the student to show the evidence.
10. Add access adjustments that preserve the assessed construct.
11. Record support level, independence, residual risks, and evidence for reporting or moderation.

Do not start with an activity, worksheet, project, text, excursion, or preferred resource and attach curriculum afterwards.

Do not simply "make the worksheet easier" or "make the task accessible". First identify the ICP or year-level achievement standard, then name the construct, then design a dignified evidence route that lets the student show that construct.

## Source Anchors

Use these principles unless the user's jurisdiction or school policy says otherwise.

- In Queensland P-10, an ICP is for students who need an adjustment to cognitive expectations in some or all learning areas. It can enable assessment and reporting against an achievement standard one or more years above or below the enrolled year level, or against adjusted learning focuses for a highly individualised curriculum plan.
- An A or E result alone does not automatically mean a student needs an ICP.
- Reasons such as literacy or numeracy difficulty, SAE or EAL/D learning, part-time attendance, behaviour, attendance, disengagement, or lack of a suitable AAC system should not be used alone to justify an ICP.
- Plan age-equivalent curriculum access with similar-aged peers where possible, while assessing against the approved ICP target level or focus.
- For Australian Curriculum work, achievement standards describe the quality of learning to judge. Content descriptions describe what is taught. Elaborations are optional examples, not mandatory assessment requirements.
- For NCCD-related evidence, keep evidence of assessed need, adjustments provided, monitoring and review, and consultation or collaboration.
- Use Universal Design for Learning from the start: provide options for engagement, representation, and action or expression.

Read `references/source-notes.md` when exact policy wording, official links, or currency checks matter.

## Intake Triage

Proceed when the user has supplied enough information to make an aligned draft. Ask only for missing details that materially affect alignment or assessment validity.

Gather or infer:

| Item | What to capture |
|---|---|
| Learning area | English, Mathematics, Science, HASS, Technologies, The Arts, HPE, Languages, or other |
| Enrolled year or band | The age-equivalent class context |
| ICP target | Different year level, partial ICP, above-level ICP, highly individualised focus, or other approved target |
| Curriculum source | Australian Curriculum v9.0, Queensland syllabus, school program, senior-prep pathway, QCIA-related evidence, or other |
| Unit context | Topic, inquiry, text, genre, investigation, project, practical context, or skill area |
| Purpose | Diagnostic, formative, summative, reporting, portfolio, moderation, parent/carer reporting, or NCCD evidence |
| Standard aspect | Exact achievement standard wording where available; otherwise mark inferred aspects for teacher confirmation |
| Teaching content | Content descriptions, syllabus objectives, curriculum codes, or local learning goals |
| Access profile | Communication, literacy, motor, sensory, assistive technology, AAC, eye gaze, switch, bilingual, or other needs |
| Support level | Independent, visual support, verbal prompt, modelled example, scribe, reader, AAC partner, peer collaboration, reduced choices, physical assistance |
| Product and timeframe | Single task, lesson sequence, rubric, tracker, assessment sheet, HTML scaffold, parent summary, or term unit |

If the user wants a quick draft and details are missing, use these defaults and label them as assumptions:

- Curriculum style: Australian Curriculum v9.0.
- Output: Markdown table.
- Assessment type: formative-to-summative task with portfolio evidence.
- Evidence: at least two or three opportunities across time, context, or mode.
- Accessibility: plain language, uncluttered layout, large readable print equivalent, clear headings, no reliance on colour alone.
- Privacy: de-identify student details unless the user requires otherwise.

## Workflow

### 1. State The Judgement Target

Create a short alignment statement:

```text
This task assesses [learner/group] against [target year/band/focus] in [subject], focusing on [achievement standard aspect]. The evidence will show [observable learning evidence] under [allowed support conditions].
```

Make the enrolled year context and assessed ICP level visible when they differ.

### 2. Map The Year-Level Progression

When adapting a mainstream at-year-level task, preserve the assessment lineage:

| Step | Action |
|---|---|
| Original standard | Identify the enrolled-year achievement standard aspect and the original task demand. |
| Original construct | Name the subject construct the class task is trying to assess. |
| ICP target | Identify the approved ICP year-level achievement standard aspect or learning focus. |
| Progression path | Trace the same or nearest defensible construct through the intervening year levels, down or up as relevant. |
| Target evidence | State what the construct looks like at the intended ICP level. |
| Mismatch check | Name any part of the original task that cannot validly map to the ICP target. |

Do not assess the enrolled-year achievement standard just because the student can access the task with support. Do not average between year levels. Judge against the approved ICP target, while keeping the age-equivalent class context visible where possible.

If the original task's construct does not have a clean progression to the ICP target, state that clearly and recommend a rebuilt evidence route or moderation review.

### 3. Deconstruct The Standard

Break the selected standard or outcome into the curriculum construct being judged:

| Element | Identify |
|---|---|
| Cognitive verb | identify, describe, explain, analyse, evaluate, create, solve, investigate, compare, justify, perform |
| Knowledge | concept, topic, text, process, representation, material, system, skill |
| Context | familiar, unfamiliar, class unit, local context, real-world situation, practical setting, text type |
| Quality marker | accuracy, detail, reasoning, fluency, independence, coherence, transfer, complexity |
| Product or process | response, model, performance, written text, oral/AAC explanation, digital artefact, investigation, solution |
| Barrier risk | reading, writing, memory, motor, sensory, language, social, timing, executive function |
| Evidence opportunity | task feature that will make the target learning visible |

For mainstream task adaptations, separate essential construct evidence from format baggage:

| Decision | Ask |
|---|---|
| Essential evidence | Which choices, responses, explanations, demonstrations, reasoning, reflections, or products are required by the ICP target? |
| Format baggage | Which parts are only the mainstream delivery format, such as handwriting, worksheet volume, independent research load, timed writing, oral speech, fine motor production, or whole-class performance? |
| Adult role risk | Where might an adult accidentally supply the reasoning while calling it access support? |
| Access route | Which AAC, observation, practical, portfolio, or partner-assisted route preserves the construct? |

### 4. Select Teaching Content

Choose the smallest set of content descriptions or objectives that genuinely supports the judgement:

- 1-2 for a short evidence task.
- 2-4 for a larger assessment.
- 4-6 for a term unit only when the assessment can validly collect evidence for all of them.

Do not treat general capabilities, cross-curriculum priorities, engagement, effort, or participation as substitutes for the subject achievement standard unless the approved plan uses a highly individualised learning focus.

### 5. Define Acceptable Evidence

Before designing the activity, specify:

- what the student will do, say, make, select, perform, explain, solve, investigate, create, read, view, listen to, respond to, or demonstrate;
- how the evidence connects to the achievement standard aspect;
- what support is allowed and how it will be recorded;
- what evidence is not enough, such as copied work, task completion without curriculum evidence, or adult interpretation without an observable student response;
- whether evidence is needed across multiple dates, contexts, modes, or trials.

### 6. Design The Assessment

Decide the adaptation type before building:

| Type | Use when |
|---|---|
| Adjusted | The original task construct matches the ICP target and needs access, layout, language, timing, or response-mode adjustments. |
| Substantially scaffolded | The construct is still relevant but the student needs reduced cognitive load, explicit choices, sentence builders, modelled practice, or smaller evidence steps. |
| Rebuilt | The original task format or year-level demand would create false failure, hide the ICP construct, be unsafe, or make evidence indefensible. |

Include:

- task title and purpose;
- curriculum alignment;
- student-friendly learning goal;
- task steps;
- materials and task conditions;
- response options;
- allowed access adjustments;
- evidence to collect;
- success criteria;
- marking guide or rubric.

Adapt the age-equivalent class task before creating a separate task, unless access, safety, dignity, or the approved plan requires an alternative pathway.

### 7. Design The Evidence Route

Use an evidence package, not just a student activity, when stakes or moderation matter. Include the student-facing task or tool plus the teacher judgement materials needed to defend the decision.

Possible evidence routes:

- AAC response or sentence builder;
- partner-assisted selection or scanning;
- teacher observation of choices, demonstrations, or interaction;
- directed demonstration by a peer, aide, or teacher;
- photo, video, screenshot, print summary, JSON/CSV export, or portfolio artefact;
- oral, signed, gestured, symbol-supported, or text response;
- practical sorting, matching, sequencing, classifying, constructing, or comparing;
- family or context form when home routines, culture, health habits, equipment, or preferences are curriculum-relevant;
- repeated evidence across dates, settings, modes, or partners.

For movement or physical-performance tasks, do not make motor impairment the basis of curriculum failure. When direct movement is unsafe or not meaningful, consider evidence as director, coach, strategist, evaluator, or safety checker. The student may choose a movement, strategy, rule, or equipment option; direct a partner to demonstrate; identify what should change after a demonstration; compare two demonstrations; or use AAC to explain why a strategy supports participation, health, safety, cooperation, or movement success.

### 8. Add Access Pathways

Adjust access before changing cognitive demand. Name the barrier and the adjustment.

Common pathways:

| Barrier | Access pathway |
|---|---|
| Reading load | read-aloud, audio, key vocabulary, simplified layout, symbol support, text-to-speech |
| Writing load | scribe, speech-to-text, sentence stems, selection board, AAC, oral response, matching, drag/drop |
| Motor demand | switch access, eye gaze, partner-assisted scanning, larger targets, digital version |
| Memory load | checklist, worked example, visual sequence, repeated practice, anchor chart |
| Language load | glossary, visuals, bilingual support, concrete examples, sentence frames |
| Sensory load | quiet space, reduced visual clutter, headphones, predictable routine |
| Executive function | chunked steps, timer, progress tracker, one instruction per line |
| Social demand | rehearsal, role card, partner option, individual response mode |

Never present access adjustments as easier curriculum unless the approved ICP target actually changes the curriculum expectation.

Access support is not curriculum judgement. Record motor, speech, gaze, fatigue, translation, partner, scribe, reader, or AAC support separately from achievement. Use wording like:

```text
Motor/access support was recorded separately from curriculum judgement. The judgement is based on the student's demonstrated curriculum choices/responses, not on the physical method used to access the task.
```

### 9. Build Judgement Tools

For rubrics and marking guides:

- name the achievement standard aspect;
- describe curriculum evidence at each level;
- separate curriculum quality from independence, prompting, disability-related access, handwriting, speech clarity, speed, spelling, or behaviour unless those are the assessed constructs;
- use the target ICP level, not the enrolled year level, when reporting against a different approved level;
- use school-approved reporting language for highly individualised plans rather than forcing an A-E rubric where it does not fit.

For evidence trackers, capture date, target, task context, response mode, support level, independence, teacher judgement note, artefact link or description, and next step.

For high-stakes or moderated ICP adaptations, include:

- student-facing task or tool;
- teacher rubric or grading matrix;
- evidence capture method;
- observation notes, print/PDF workflow, screenshots/photos, exports, or portfolio checklist;
- family/context form when relevant;
- moderation or handoff note;
- review email or cover note when sending to a teacher, HOD, case manager, or moderation colleague.

Moderation handoff notes should use this structure:

1. Original task.
2. ICP target.
3. Construct decision.
4. Adaptation decision: adjusted, scaffolded, or rebuilt.
5. Evidence route.
6. Judgement method.
7. Residual risks.
8. Review request.

### 10. Plan Teaching After Assessment

Design teaching that prepares students for the evidence task:

1. connect to prior knowledge;
2. explicitly teach vocabulary, concepts, tools, or processes;
3. model the skill;
4. practise with guided support;
5. practise with reduced support;
6. provide formative feedback;
7. rehearse the assessment format;
8. collect assessment evidence;
9. reflect and set next steps.

Each lesson should identify the assessment evidence it prepares, the content it teaches, the access supports built in, and the readiness check.

## Output Rules

- Use Australian English spelling.
- Be direct, practical, and teacher-usable.
- Link every recommendation to the target standard, learning focus, evidence, or access barrier.
- Include curriculum codes when the source provides them.
- Include access adjustments and support level in every teacher-facing assessment or map.
- Include a quality assurance checklist unless the user asks for a very short answer.
- For student-facing resources, include a learning goal, success criteria, clear steps, response options, and a mini checklist.
- For teacher-facing resources, include alignment, evidence, adjustments, task conditions, and judgement notes.
- For HTML or digital assessments, build accessible interaction: keyboard support, large targets, high contrast readiness, clear focus order, simple layout, no required external dependencies.
- Do not include identifiable student details unless the user supplied them and the output requires them.
- Do not label the student as "ICP", "Year 1 level", "modified down", or similar inside student-facing resources.
- Keep student-facing language age-respectful when the curriculum level is below the enrolled year.
- Preserve agency through choices, own examples, opinions, reasons, preferences, and student-selected order where possible.
- Reduce research load when research is not the assessed construct.
- Build in rest breaks and low-pressure response routes when fatigue, gaze load, processing, or communication load is high.
- Keep teacher and moderation controls separate from student mode.
- Use anonymous placeholders in reusable examples, public templates, and AI prompts unless the user explicitly approves identifiable details.
- Clearly mark current packages, old alternatives, source tasks, and private forms before zip, share, or handoff workflows.

## Quality Assurance

Before finalising, check:

- The achievement standard aspect or ICP focus is explicit.
- The task evidence matches the cognitive verb and quality marker.
- Content descriptions support teaching rather than replacing the judgement target.
- Adjustments preserve the assessed construct.
- The enrolled year context is maintained where possible.
- Evidence is observable, recordable, and sufficient for the stated purpose.
- Support level and independence are documented separately from curriculum achievement.
- The rubric or judgement guide assesses curriculum learning, not effort, compliance, neatness, or unsupported participation.
- The workload is feasible during ordinary teaching and evidence collection.
- AAC selections are treated as possible curriculum choices, reasoning, reflection, direction, or evaluation, not only low-level quiz answers.
- Adults have not supplied the construct reasoning while only the access method is attributed to the student.
- A polished student activity is accompanied by the needed rubric, evidence capture, teacher notes, and moderation rationale.
- Residual risks, moderation questions, and review needs are clearly recorded.

## Reference Files

- Read `references/templates.md` when the user asks for a backwards map, assessment outline, rubric, teaching sequence, evidence tracker, or access map.
- Read `references/examples.md` when examples would help design a subject-specific draft.
- Read `references/source-notes.md` when the work depends on official Australian Curriculum, Queensland ICP, NCCD, or UDL wording.

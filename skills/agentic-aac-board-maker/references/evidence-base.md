# Evidence Base For Agentic AAC Board Generation

This file gives the agent a practical evidence-informed foundation. It is not a clinical protocol and does not replace SLP/OT/vision/team assessment. Use it to keep generated boards aligned with known AAC, access, and inclusive learning principles.

## Core Sources Consulted

Last checked: 2026-05-26. These are grounding sources for classroom resource design, not clinical, legal, or licensing certainty. Verify exact device, legal, school-policy, and licence details again before high-stakes use or public distribution.

- ASHA Practice Portal: Augmentative and Alternative Communication (AAC) — AAC supplements or compensates for speech/language production/comprehension and supports expression of thoughts, wants, needs, feelings, and ideas. https://www.asha.org/practice-portal/professional-issues/augmentative-and-alternative-communication/
- National Joint Committee / ASHA Communication Bill of Rights, 3rd edition — people have a fundamental right to communicate across life settings, including rights to dignity, meaningful communication, direct address, response, participation, social interaction, information, refusal, preference/opinion expression, meaningful choices, supports, and functioning AAC/AT. https://www.asha.org/njc/communication-bill-of-rights/
- TIES Center / University of Minnesota: core words, aided language modeling, and literacy — core + fringe vocabulary and aided language modeling support communicative competence and literacy participation for students with significant communication needs. https://publications.ici.umn.edu/ties/communicative-competence-tips/connecting-core-words-aided-language-modeling-and-literacy
- AssistiveWare Learn AAC: communication partner skills — model AAC, wait/listen/respond, presume competence, use AAC across contexts, model more than requests, comment rather than over-question. https://www.assistiveware.com/learn-aac/build-communication-partner-skills
- Janice Light communicative competence framework — AAC competence includes linguistic, operational, social, and strategic competence. Summary: https://praacticalaac.org/praactical/communicative-competence-in-aac/
- Visual supports as evidence-based practice — visual supports can increase understanding, participation, independence, predictability, and reduce anxiety/challenging behaviour risk. https://docs.autismspeaks.org/evidence-based-practices/visual-supports
- Indiana Resource Center for Autism: visual schedules and choice boards — visual schedules/choice boards are often receptive supports and should not be mistaken for a full expressive AAC system. https://iidc.indiana.edu/irca/articles/visual-schedules-and-choice-boards-avoid-misinterpretation-of-their-primary-functions.html
- CAST UDL Guidelines — design multiple means of engagement, representation, and action/expression; learners need flexible ways to communicate and show learning. https://udlguidelines.cast.org/
- Tobii Dynavox access methods — common AAC access methods include touch, eye gaze, mouse dwell, and scanning. https://www.tobiidynavox.com/pages/access-methods-for-aac
- ISAAC Communication Access — communication access includes being understood, preferred methods, time/opportunity to communicate, accessible information, and support from trusted people where needed. https://isaac-online.org/english/communication-access/
- Project Core — classroom AAC should include high-frequency core vocabulary and aided language input across authentic routines. https://www.project-core.com/
- SETT Framework, Joy Zabala — decisions should account for Student, Environment, Task, and Tools rather than choosing tools in isolation. https://www.joyzabala.com/
- Australian Curriculum Student Diversity — students with disability may need adjustments to access, participate, and demonstrate learning. https://www.australiancurriculum.edu.au/resources/student-diversity/students-with-disability/
- QCAA QCIA — evidence should show participation and achievement in planned learning, without confusing access support with curriculum judgement. https://www.qcaa.qld.edu.au/senior/certificates-and-qualifications/qcia
- Disability Standards for Education 2005 — reasonable adjustment and consultation obligations shape access planning in Australian education contexts. https://www.education.gov.au/disability-standards-education-2005
- WCAG 2.2 — target size, pointer cancellation, keyboard, focus, contrast, and reduced-motion principles are baseline web accessibility constraints, while AAC and gaze targets usually need much larger dimensions. https://www.w3.org/TR/WCAG22/
- ARASAAC terms — preserve exact attribution and non-commercial/share-alike licence details when using ARASAAC pictograms or derived materials. https://arasaac.org/terms-of-use

## Design Commitments Derived From The Evidence

### 1. Communication rights first

Generated boards must support the student's right to:

- be addressed directly;
- make meaningful choices;
- request and refuse;
- express preferences, feelings, comments, and opinions;
- receive responses to communication;
- participate as a full communication partner;
- access a functioning communication system.

Agent implication: every board should include agency/repair language unless the task is deliberately tiny and the user asks otherwise.

### 2. Communicative competence is multidimensional

A board should support more than vocabulary labels:

- **Linguistic:** words/phrases, core/fringe vocabulary, sentence building.
- **Operational:** usable access method, stable positions, clear navigation.
- **Social:** greetings, commenting, turn-taking, opinions, relationships.
- **Strategic:** repair, ask for help, repeat, different, stop, wait, I don't know.

Agent implication: when generating a board, tag each button/page with its communication function mentally, even if not displayed.

### 3. Core + fringe vocabulary

Core words are flexible across contexts; fringe words are topic/person/activity-specific. Strong boards usually need both.

Agent implication:

- include core words such as want, more, help, stop, go, finished, like, different, again, think, because, yes/no where relevant;
- add fringe vocabulary for the actual lesson/routine/task;
- avoid boards made only of topic nouns.

### 4. Aided language/modeling matters

Communication partners should be able to model use of the board. Boards should be model-friendly: clear, stable, not too cluttered, and useful for adult comments as well as student responses.

Agent implication: include a brief teacher note for how to model key buttons when producing resource packs.

### 5. Visual supports are useful but not automatically expressive AAC

Visual schedules and choice boards can support comprehension and transitions, but they are not a full expressive system by themselves.

Agent implication: if generating a schedule or choice board, add expressive options where appropriate: Help, Wait, Different, Like/Don't like, Finished, Question, Change.

### 6. UDL: action and expression must be flexible

Students differ in how they navigate and express learning. Boards should offer accessible response modes that preserve learning goals.

Agent implication: translate curriculum into accessible communication moves rather than lowering the task by default.

### 7. Access method changes the design

Touch, keyboard, eye gaze/dwell, switch scanning, partner-assisted scanning, and print all impose different constraints.

Agent implication: never generate layout purely from desired vocabulary count. First decide whether the target number of buttons is compatible with the access method.

### 8. Differentiation must be explicit

Differentiation is not a softer target. A strong board states how access load is reduced while the learning or participation intent remains visible.

Agent implication: new resource packs should include `sett`, `udl`, `differentiation`, `participationBarriers`, and `evidencePlan` in the IR. These notes should avoid diagnoses and private identifiers.

### 9. Evidence is not the same as access support

Logs, dwell selections, partner prompts, and support levels can contextualise evidence. They should not be treated as proof that the student did or did not understand the curriculum construct.

Agent implication: record only the minimum needed: activity, prompt/page, selected label/response, access method/support context if relevant, timestamp, and teacher note.

## Practical Evidence-Informed Rules

- Prefer communication opportunities over behaviour-control boards.
- Prefer comments/opinions/questions/reasons in addition to requests.
- Include wait time and partner modeling notes where useful.
- Use stable locations for recurring core/repair buttons.
- Keep output editable; teams need to personalise vocabulary.
- Treat AAC as multimodal: speech, gesture, symbols, text, photos, partner-assisted strategies, switches, eye gaze, and keyboard can all coexist.
- The generated board is a classroom support, not the student's only or emergency communication system.
- Use SETT to keep access decisions grounded in the student, environment, task, and tools.
- Use UDL to provide multiple ways to engage, understand, and express learning.
- Make the evidence route explicit without converting motor/access support into grading.

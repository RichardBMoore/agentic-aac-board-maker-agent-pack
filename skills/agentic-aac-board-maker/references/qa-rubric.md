# QA Rubric

Use this before returning any generated AAC board/resource.

Scoring: Green = ready for draft use; Amber = usable with caveat/fix soon; Red = fix before delivery.

## 1. Communication Rights And Agency

- Green: Student can initiate/choose/refuse/repair/comment or ask as appropriate.
- Amber: Student can choose/answer but has limited agency.
- Red: Student can only comply or answer adult-controlled prompts.

Required checks:

- [ ] Help/repair option included when appropriate.
- [ ] Stop/Finished/Different/Not that considered.
- [ ] Student is not spoken for in teacher notes.
- [ ] Board supports meaningful choices, not token choices only.

## 2. Communicative Competence

- [ ] Linguistic: useful words/phrases, core + fringe.
- [ ] Operational: access method and navigation are usable.
- [ ] Social: comments/opinions/questions where relevant.
- [ ] Strategic: repair/help/refusal route.

## 3. Curriculum/QCIA Strength

- Green: Reduces access load while preserving learning/evidence intent.
- Amber: Participation is present but curriculum evidence is thin.
- Red: Task is watered down to unrelated picture choosing.

Checks:

- [ ] Cognitive demand identified.
- [ ] AAC moves match that demand.
- [ ] Evidence/teacher observation route exists when needed.
- [ ] SETT/UDL/differentiation notes show how access barriers were reduced without erasing learning intent.
- [ ] EvidencePlan states what can be observed/exported and what must not be treated as curriculum judgement.

## 4. Access Method Fit

- [ ] Grid density matches access method.
- [ ] Targets large enough.
- [ ] Keyboard fallback present for digital outputs.
- [ ] Dwell cancellation and progress if gaze/dwell.
- [ ] Scan order logical if switch scanning.
- [ ] Print order/partner scanning clear if low-tech.

Red flags:

- More than 9 buttons on any page for an untested gaze user (the validator's enforced limit; set denseGazeTested: true only after dense gaze access is genuinely tested).
- Scrolling required for routine gaze selections.
- Hover-only UI without cancellation.
- Hidden tiny controls in student mode.

## 5. Visual/Text Design

- [ ] Labels short and speakable.
- [ ] Font size and contrast adequate.
- [ ] Colour not sole signal.
- [ ] Symbols do not overwhelm text.
- [ ] Age-respectful language.

## 6. Symbols, Licensing, Privacy

- [ ] Text fallback for every symbol.
- [ ] ARASAAC/custom source attribution included.
- [ ] No proprietary Boardmaker/PCS assets copied.
- [ ] No unnecessary student names/diagnoses/sensitive details.
- [ ] External AI/symbol calls avoided for private content.

## 7. Technical Verification

For HTML:

- [ ] File opens.
- [ ] Browser console has no obvious JS errors.
- [ ] Buttons activate by click and keyboard.
- [ ] TTS can stop if included.
- [ ] No external dependencies if promised offline.
- [ ] Print preview reasonable if print required.

For JSON:

- [ ] Parses as JSON.
- [ ] Required fields present.
- [ ] Page/button arrays valid.
- [ ] No trailing comments or invalid syntax.

For resource packs:

- [ ] README explains use/customisation.
- [ ] Relative links work.
- [ ] Attribution included.

## Final Caveat Language

Use honest wording:

```text
This is a draft classroom support/resource generated from the provided context. It should be reviewed by the teaching/SLP/OT team and tested with the actual student, access method, device, and school environment before relying on it.
```

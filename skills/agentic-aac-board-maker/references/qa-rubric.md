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

- [ ] Total simultaneously active targets match `visibleTargetLimit`; setup matches `setupTargetLimit`.
- [ ] Targets large enough.
- [ ] Keyboard fallback present for digital outputs.
- [ ] Dwell cancellation and progress if gaze/dwell.
- [ ] Scan order logical if switch scanning.
- [ ] Print order/partner scanning clear if low-tech.

Red flags:

- More than 9 active targets—including navigation/utilities—for an untested gaze user.
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
- [ ] Symbol candidates were reviewed for meaning, familiarity, culture and visual access; approved ids are recorded.
- [ ] ARASAAC/custom source attribution included.
- [ ] No proprietary Boardmaker/PCS assets copied.
- [ ] No unnecessary student names/diagnoses/sensitive details.
- [ ] External AI/symbol calls avoided for private content.

## 7. Technical Verification

For HTML:

- [ ] Fresh-rendered from IR; embedded IR and shared-runtime parity pass.
- [ ] File opens on intended browser/device-sized viewport with no page/console errors.
- [ ] Buttons activate by click and keyboard.
- [ ] Dwell start/cancel/activation are browser-tested when applicable.
- [ ] TTS makes Stop Speech the only active target while speaking.
- [ ] Live total-target audit passes in setup, board, navigation and speech states.
- [ ] No external dependencies if promised offline.
- [ ] Print preview reasonable if print required.

For JSON:

- [ ] Parses as JSON.
- [ ] Canonicalisation `--check`, JSON Schema and semantic validation pass.
- [ ] Page/button arrays valid.
- [ ] No trailing comments or invalid syntax.

For resource packs:

- [ ] README explains use/customisation.
- [ ] Relative links work.
- [ ] Attribution included.
- [ ] Fresh-output evaluation harness passes the relevant fixture(s).

## 8. System Fit Review

- [ ] Relationship to the student's established AAC/low-tech system is clear.
- [ ] Familiar vocabulary and stable motor/location patterns are preserved or flagged for review.
- [ ] Symbols/text/photos are known or awaiting explicit candidate review.
- [ ] Actual access calibration, device, browser, mount, seating, vision and fatigue are checked or unresolved honestly.
- [ ] Language/culture/voice and reliable partner yes/no/cancel/repair signals are recorded.

## Final Caveat Language

Use honest wording:

```text
This is a draft classroom support/resource generated from the provided context. It should be reviewed by the teaching/SLP/OT team and tested with the actual student, access method, device, and school environment before relying on it.
```

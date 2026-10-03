# House Standards

House standards make every generated board behave like part of one communication system rather than a one-off grid. They are data files a team can edit once, plus one tool that applies them:

```sh
python3 scripts/apply_house_standards.py board.ir.json            # apply (idempotent)
python3 scripts/apply_house_standards.py board.ir.json --check    # release gate: already applied?
```

Run it after writing the IR and before rendering. It changes nothing on a second run. The validator fails canonical IR 0.5.0 that does not record `house`.

| File | What it holds | Who changes it |
| --- | --- | --- |
| `references/house-layout.json` | Permanent grid addresses for recurring words | Team, rarely |
| `references/house-lexicon.json` | One label, message, word class and symbol per recurring word | Team, when vocabulary or symbols are reviewed |
| `references/house-settings.json` | Colour scheme, voice, literacy defaults, partner-card defaults, logging default | Team |
| `assets/house-symbols/` | The house symbol PNGs (ARASAAC, CC BY-NC-SA) | `scripts/review_house_symbols.py` |

## 1. Words keep their place (motor planning)

Consistent symbol location makes selection faster with practice (Thistle et al. 2018), and this matters most for gaze and switch users. Addresses are relative to the grid, so they hold on any grid size:

| Slot | Words | Address |
| --- | --- | --- |
| help | Help | bottom-left |
| different | Different / Undo / Delete | bottom row, middle |
| finished | Finished / Start again | bottom-right |
| stop | Stop / Speak | top-right (the "voice corner"; the runtime's Stop speech control appears just beside it) |
| nav | the page's forward button | right column, middle row |
| keyboard / nav-back | ABC on the first page; ◀ back on later talking pages | left column, middle row |

On a 3x3 page that is:

```text
[ content ] [ content ] [ Stop/Speak ]
[ ABC/◀   ] [ content ] [ next ▶     ]
[ Help    ] [ Diff/Undo] [ Finished   ]
```

Rules:

- A house word on the wrong cell fails validation.
- Keep other recurring words in the same cell across related pages too (for example Wait, Yes and No on every shop page) by giving them the same `position`; the tool keeps existing positions. House words never move between boards.
- Content fills the other cells in reading order. Content may use an unused reserved cell, except the Help cell (warning).
- Two words from one slot on the same page is a conflict: split the page.
- Grow a board by hiding cells in place (`"hidden": true` on a button) and revealing them later, never by reshuffling. Record when to review hidden words in teacher notes. Hidden buttons are not targets and keep their address in HTML and OBF.
- If the student already has an established device with a different motor plan, follow the student's system: set `house.layoutSource` to `"student-system"` with a `layoutNote`. The word list, literacy and colour rules still apply.

## 2. Same button, same message (word list)

Every recurring word has one label and one spoken message on every board, for example `Wait` always says "Please wait" and `Different` always says "I want something different". Buttons that use a house word carry `lexiconId`. A button whose label matches a house word or alias without `lexiconId` fails validation, so drift such as "Wait" meaning "I need to wait" on one board and "Please wait" on another cannot ship. If you genuinely mean a different word (for example "Change" meaning coins), use a different label such as "My change". Combined labels such as "Stop / wait" are not matched: choose Stop or Wait.

Behaviours: `speak` says the whole message now; `compose` adds the word to the message bar and says it; `operation` runs an action (Speak, Undo, Start again, Delete, Space, ABC).

## 3. Language, not just phrases (literacy pages)

Unless a board opts out, the tool adds:

- **ABC keyboard**, reachable from the first page. On boards limited to nine targets it is a gaze-safe two-step keyboard: letter groups (QWERTY rows by default, ABC order available), then letters, returning to the groups after each letter, with Speak, Delete and Help. `literacy.keyboard.mode: "full"` gives a one-page keyboard only when `visibleTargetLimit >= 32`. Spelling uses `add-letter`, `add-space` and `delete-letter` actions; OBF exports them as `+letter`, `:space` and `:backspace`.
- **Core words**: I, want, don't, like, go, more (configurable) that build messages in the message bar. "don't" rather than "not" by default, so partners model "I don't like it" rather than "I not like".
- **Word endings** for older students (secondary and Year 5+): -s, -ing, -ed that change the last word ("go" + -ed = "went"). Studies with school-age children show endings can be taught; results with teenagers are more mixed, so watch and adjust.
- A **message bar** whenever spelling or core words are present.

Talking pages are linked in a ring: one forward button per page plus a back button on talking pages after the first, so neighbouring pages are one step apart. The Word endings page also has a back button (to the page where the word was chosen is usually one step back). The Core words page is forward-only because six words, Speak, Help and the forward button fill a 3x3 page, so its left-middle cell holds a word: model that difference. Keyboard pages put ◀ back in the same left-middle cell.

Opt out only with a reason the team can read: `literacy.keyboard = {"enabled": false, "omitReason": "..."}`. Boards with no page of 3x3 or larger opt out automatically ("early choice board"), because spelling belongs on the student's main system there.

## 4. Symbols reviewed once (house symbol set)

House words carry one symbol each. Symbols start as `proposed` (chosen by the agent, favouring age-neutral black-line figures) and become `approved` after one team review:

```sh
python3 scripts/review_house_symbols.py --review-out house-symbol-review.json   # offline review sheet
python3 scripts/review_house_symbols.py --apply-review house-symbol-review.decisions.json
python3 scripts/review_house_symbols.py --approve-proposed help,stop,finished   # agreed in a meeting
```

Then re-run `apply_house_standards.py` on each board and re-render. Topic words still go through the per-board review in `scripts/fetch_arasaac_symbols.py`. Boards show the status in the teacher panel ("proposed by the agent and awaiting team review"). A symbol approved for the house set is a starting point, not proof a particular student recognises it: keep checking with the student.

## 5. Colour means word type

Buttons carry `wordClass` (pronoun, verb, describing, noun, conjunction, preposition, social, question, adverb, important, determiner, operation, letter, ending). With `display.colourScheme: "modified-fitzgerald"` the tool sets pale fills from `house-settings.json`: yellow pronouns, green verbs, blue describing words, orange nouns, pink social words, purple questions, red important/negation/emergency words. Classify pre-stored phrases by their key word ("Too expensive" is describing; "Where is it?" is a question).

Arrange space before colour: group words by type on the page; for young learners grouping helps search more than background colour does (Thistle & Wilkinson). Fills that disagree with the scheme produce a warning.

**CVI profile:** `display.visualProfile: "cvi"` switches colour coding off and renders a black background, white text, one highlight colour (`display.highlightColour`, use the student's preferred colour) for focus and dwell, wider gaps and symbols on a plain plate. Target count, dwell time and symbol type (photos, Sclera, simple single-element symbols) are vision/CVI team decisions.

## 6. Partner card

Partner training has some of the strongest evidence in AAC. Every board has `partnerCard`:

```json
"partnerCard": {
  "modelWords": ["btn-where", "btn-buy", "btn-pay", "btn-thank-you"],
  "waitSeconds": 15,
  "commentExamples": ["Touch Where is it?: \"I can't see the bread. Where is it?\""],
  "promptLadder": ["...least-to-most steps, ending with no hand-over-hand..."],
  "notes": "..."
}
```

`scripts/render_partner_card.py board.ir.json partner-card.html` prints a one-page card: the 3-5 words to model this week and where they are, how long to wait (at least 5 seconds; default 10, 15 for gaze, switch and partner-assisted access; longer pauses gave more responses and longer messages in Mathis et al. 2011), comments to use instead of test questions, the least-to-most prompt ladder, and where the house words live. The same card appears in the board's teacher panel and print-out.

## 7. Community boards introduce the student

Boards with `audience.settings` containing `"community"` must have the house word **How I talk** on the first page: "I use this device to talk. Please wait while I build my message. Talk to me, not my helper." (after Scope's communication access guidance). The tool adds it when there is room.

## 8. Voice

`speech` sets `lang`, optional `voiceName`, `rate`, `pitch` and `preferLocal`. The runtime prefers voices installed on the device (`SpeechSynthesisVoice.localService`) in en-AU, then en-GB, then English, because Edge's "Online (Natural)" voices need internet. Pin one voice by name (for example "Microsoft Catherine" on Windows or "Karen" on iPad) after choosing it with the student, and use it on every board through `house-settings.json`. The teacher panel and Sound check report the voice in use and warn when it is an online voice or the pinned voice is missing.

## 9. Opt-in selection log

`evidenceLog.enabled` is false by default. When the team turns it on (with an agreed purpose in `evidencePlan`), the teacher panel offers Record, Partner modelling, Download CSV and Clear. Logs stay in memory on the device until downloaded. Each row records time, page, button, label, message, communication function, role, word class, whether it was a student selection or a partner model, and the access method. The panel summarises student selections by communication function (requests, comments, questions, refusals), the number of different messages and partner models. Logs miss speech, gestures and context: treat them as one source alongside teacher observation, never as proof of understanding.

Open the teacher panel with three quick taps on the board title, Ctrl+Shift+T, or `?teacher=1` in the address. Ctrl+Shift+M toggles partner modelling; a badge shows while it is on.

## 10. Visual schedules

A page with `schedule.steps` (button ids in order) shows **Now ▶**, **Next** and **Done ✓** badges, a dashed border on Next and strike-through on done steps (never colour alone). A button with the `schedule-done` action (the house word Finished on the schedule page) marks the current step done; adults can mark or undo steps in the teacher panel.

## Speech and dwell behaviour

- The board stays visible and live while speaking. Stop speech appears in a reserved column at the right edge, never over the board, so it cannot appear under a resting gaze. During speech the live target audit allows the board's limit plus this one control.
- After any selection, page change or setup action, dwell will not start again until the pointer leaves the spot it is resting on. This stops a resting gaze from re-selecting the same button or the button that appears in its place on the next page.
- A new selection interrupts the current message.

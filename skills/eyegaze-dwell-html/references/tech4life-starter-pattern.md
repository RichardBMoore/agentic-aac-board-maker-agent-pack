# Tech for Life Eye-Gaze Starter Pattern

Use this reference when creating a reusable starter file for Richard's Technology for Life eye-gaze/dwell resources.

## Why this exists

A review of Tech for Life eye-gaze HTML files showed that the strongest resources share a predictable interaction contract:

> Look at a target → dwell progress appears → leaving cancels → selection activates once → student can hear/read/continue → teacher can collect evidence.

The main improvement is not just bigger buttons; it is consistency across files so students do not need to relearn the interface every lesson.

## Starter file shape

Create new activities from a single-file HTML starter with these standard parts:

1. Header with activity title and a large `Read Prompt` button.
2. Central student area with:
   - one prompt/question at a time
   - 2–4 large dwell choices where possible
   - visible student response strip
3. Teacher/access side panel with:
   - optional student/group name
   - dwell-time selector: 600, 800, 1000, 1200, 1500 ms
   - test dwell button
   - high contrast toggle
   - stop speech button
   - clear choice button
   - teacher evidence textarea
   - copy report and print buttons
4. Footer/status area showing `Ready`, `Dwelling…`, `Cancelled`, or `Selected`.

## Activity-object editing model

Keep the dwell/access machinery stable. For most new lessons, edit only an `activity` object near the top of the script:

```js
const activity = {
  title: 'Safe Searching',
  prompt: 'What should you do if a search result makes you feel unsure or unsafe?',
  readOnChoice: true,
  choices: [
    {
      id: 'ask-teacher',
      symbol: '🙋',
      label: 'Ask a teacher',
      evidence: 'The student identified asking a trusted adult as a safe online strategy.'
    },
    {
      id: 'close-page',
      symbol: '❌',
      label: 'Close the page',
      evidence: 'The student identified closing unsafe content as a protective action.'
    }
  ]
};
```

This keeps new resource creation fast while preserving consistent dwell, TTS, keyboard, report, and layout behaviour.

## Must-have implementation details

A Tech for Life starter should include:

- `DwellManager` reused unchanged between files where possible.
- `pointerenter`/`mouseenter` to start dwell.
- `pointerleave`/`mouseleave` and `blur` to cancel dwell.
- Enter/Space keyboard activation.
- Visible conic-gradient dwell ring or equivalent progress indicator.
- Activation cooldown so one gaze does not double-trigger.
- `speechSynthesis` read-aloud and stop speech controls.
- High contrast class toggle.
- Teacher report generated locally only.
- Copy and print evidence actions.
- No external dependencies: no `http://`, `https://`, CDN, remote fonts, `fetch(`, or `type="module"`.

## Recommended verification scan

Before calling the starter EQ/offline ready, inspect the generated HTML for:

```text
has_http: False
has_cdn: False
has_fetch: False
has_type_module: False
has_pointerenter: True
has_pointerleave: True
has_keyboard_enter_space: True
has_tts: True
has_print: True
```

A simple script can read the HTML as text and check for those strings. Treat `cdn` as a string-risk check: avoid even mentioning it inside the deliverable if using a crude scan.

## Design rule

For this user's Tech for Life resources, the guiding phrase is:

> Consistency is access.

The student should spend effort on the curriculum task, not on rediscovering how the interface behaves.

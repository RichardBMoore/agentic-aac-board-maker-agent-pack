# Eye Gaze HTML Tools For Accent Devices

Use this reference when building a single self-contained HTML resource for a student using eye gaze or mouse dwell on PRC-Saltillo Accent or Edge devices, especially on EQ/offline networks and Microsoft Edge opened from `file:///`.

## Contents

- Build stance
- Target environment
- Non-negotiables
- Dwell timing
- Target size and layout
- Interaction model
- Confirmation and recovery
- Speech and audio
- Student data and privacy
- QA workflow
- Prompt pattern

## Build Stance

Build the student-facing experience first. A useful gaze tool should open quickly, fit the screen, work without internet, tolerate imprecise gaze, and recover gracefully from accidental activation.

Prefer a single `.html` file for one-off classroom tools. Use the bundled Boardmaker asset only when the user needs a reusable editor/player, a symbol library workflow, or multiple imported activities.

## Target Environment

Common deployed context:

- OS: Windows 10 IoT LTSC or Windows 11.
- Browser: Microsoft Edge Chromium, often launched from USB or local storage with `file:///`.
- Eye tracker: PRC-Saltillo NuEye, Look, or similar infrared module mounted below the screen.
- Screen: Accent 1000 and Accent 1400 units commonly use 1920 x 1200 displays.
- Network: assume no CDN, no remote fonts, no symbol API, and no internet during student use.
- Dedicated AAC builds may need the Integrated Feature Pack for browser access.

Treat these as classroom assumptions, not a universal hardware contract. If the user gives a specific viewport or device model, design and test against that.

## Non-Negotiables

- Produce one self-contained HTML file unless the user explicitly asks for a project.
- Inline CSS and JavaScript. Embed small symbols and optional audio as data URIs or use text-only fallbacks.
- Use semantic `<button>` elements for every student choice.
- Make all primary gaze targets at least 120 x 120 px; prefer 150 to 200 px for 2 to 6 choices.
- Keep at least 20 px between gaze targets.
- Use visible dwell progress, usually a conic-gradient ring or fill.
- Cancel dwell immediately on pointer/mouse leave.
- Provide keyboard fallback with Tab plus Enter/Space. Arrow-key grid navigation is a bonus.
- Include `aria-label` on buttons, an `aria-live` status, and a visible focus indicator.
- Use Australian English by default.
- Use text contrast that meets WCAG AAA for labels wherever possible.
- Avoid scroll in student mode. Remove decorative chrome before shrinking targets.

## Dwell Timing

Start with these values and expose them as constants or data attributes:

| Context | Time |
| --- | --- |
| Default classroom tool | 800 to 1200 ms |
| Accidental activation risk | 1000 to 1500 ms |
| Confident gaze user | 600 to 800 ms |
| Confirmation step | 600 ms |
| Avoid below | 500 ms |
| Avoid above | 1500 ms |

The "Midas touch" risk is central: students often look at a button to read it. Reduce false activations with enough dwell time, progress feedback, large gaps, confirmation for high-stakes choices, and a clear way to cancel or undo.

## Target Size And Layout

Use full-cell layouts instead of small buttons inside large empty panels.

Recommended patterns:

- 2-choice AAC: two full-height cells in a 1 x 2 grid.
- 4-choice quiz: 2 x 2 grid with prompt above and stable feedback below.
- Story reader: page content area plus large Back, Next, Repeat, and Finished controls.
- Word bank: large pill buttons only when the task truly needs many short words; otherwise use grid cells.
- Utility controls: Stop Speech, Help, Back, and Finished should also be gaze-sized.

Do not put a tiny toolbar beside large student choices. If teacher controls are needed, put them behind a locked or hidden panel and keep student mode uncluttered.

## Interaction Model

On Accent eye-gaze setups, the tracker moves the Windows mouse cursor. Build hover dwell around pointer/mouse events:

- Use `pointerenter` and `pointerleave` when available.
- Fall back to `mouseenter` and `mouseleave`.
- Do not rely on `touchstart`, touch gestures, drag, or pointer-down activation.
- Keep click activation for mouse testing and partner use, but guard against duplicate firing.
- Use focus styles for keyboard users; only start dwell on focus if the activity deliberately needs keyboard-dwell behaviour.

For the implementation snippets, read `templates.md`. For a complete starter, copy `../assets/eye-gaze-single-file-template.html`.

## Confirmation And Recovery

Require confirmation, second dwell, undo, or safe cancel for:

- Quiz submission.
- Clear or reset.
- Delete.
- Export.
- Leaving the activity.
- Any answer where an accidental wrong choice would matter.

For low-stakes communication boards, speak the selected label and leave an obvious Back, Undo, More, Help, or Finished path where useful.

## Speech And Audio

Use the Web Speech API for simple offline speech feedback:

- Set `utterance.lang = "en-AU"`.
- Cancel any current utterance before speaking the next one.
- Provide a Stop Speech control.
- Do not assume a specific installed voice.

Use tones sparingly and make them optional. Some students benefit from a short cue; others find it distracting or aversive. Do not make audio the only feedback channel.

## Student Data And Privacy

For one-off classroom HTML tools:

- Do not include student names, diagnoses, school IDs, behaviour notes, or medical details unless explicitly needed.
- Keep logs off by default.
- If logging is requested, store only minimal local data and make export/clear actions deliberate.
- Do not fetch remote images or symbol data during student use.

## QA Workflow

Before handing over the file:

1. Open it in Edge from `file:///`.
2. Confirm there are no console errors.
3. Confirm the Network tab shows no external requests.
4. Check the page fits the target viewport without student-mode scrolling.
5. Hover a choice and confirm dwell progress fills at the expected timing.
6. Move away before completion and confirm dwell cancels.
7. Leave gaze on a completed choice and confirm it does not fire repeatedly.
8. Use Tab and Enter/Space to activate a choice.
9. Confirm all interactive targets are at least 120 x 120 px.
10. Confirm all buttons have accessible labels and focus states.
11. Confirm speech can be stopped.
12. Run `scripts/check_eye_gaze_html.py <file.html>` for static checks.

Use this DevTools snippet for runtime target checks:

```javascript
document.querySelectorAll('button').forEach((btn) => {
  if (btn.offsetParent === null) return;
  const r = btn.getBoundingClientRect();
  const ok = r.width >= 120 && r.height >= 120;
  console.log(`${ok ? 'OK' : 'CHECK'} ${btn.getAttribute('aria-label') || btn.textContent.trim()} - ${Math.round(r.width)}x${Math.round(r.height)}px`);
});
```

## Prompt Pattern

When expanding a user request into an implementation brief, preserve these constraints:

```text
Build a single-file HTML resource for a student using eye gaze on a PRC-Saltillo Accent 1000/1400 or similar Windows AAC device. It will open in Microsoft Edge from file:/// with no internet. Eye gaze behaves like a mouse cursor, so interaction must be hover/dwell based with an 800 ms starting dwell time. Include no external dependencies. Make all student controls at least 120 x 120 px, use visible dwell progress, cancel dwell on pointer leave, support Tab plus Enter/Space, include ARIA labels, use Web Speech API with en-AU where speech is needed, use Australian spelling, and target WCAG AAA contrast for text. The activity is: [describe activity].
```

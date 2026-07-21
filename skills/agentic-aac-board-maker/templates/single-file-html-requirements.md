# Single-File HTML Requirements

Use this when the agent directly creates an HTML AAC board/resource.

## Hard Requirements

- One `.html` file unless the user asks for a pack.
- Inline CSS and JavaScript.
- No CDN, remote fonts, module imports, or external scripts.
- No network symbol fetching during student use unless explicitly allowed.
- Semantic `<button>` elements for student choices.
- Keyboard operation with Tab + Enter/Space.
- Visible focus and high contrast states.
- Text fallback for every symbol/image.
- Stop Speech button when speech synthesis is included.
- Print styles when printable use is likely.
- Attribution footer/section.
- Teacher notes separate from student board.
- For gaze/dwell student resources, one startup fullscreen attempt and a gaze-sized **Full screen** button.

## Recommended HTML Sections

```html
<header class="app-header">
  <h1>Board title</h1>
  <p>Short student-friendly instruction.</p>
</header>

<main>
  <section class="board" aria-label="AAC communication board">
    <button class="aac-button" data-speak="Help">Help</button>
  </section>
</main>

<details class="teacher-notes">
  <summary>Teacher notes</summary>
</details>

<footer class="attribution">...</footer>
```

## Dwell Requirements

Only add dwell when requested/needed. If included:

- Start on pointerenter/mouseenter.
- Cancel on pointerleave/mouseleave/blur.
- Show progress ring/bar.
- Activate once after threshold.
- Require pointer leave or cooldown before reactivation.
- Keep Enter/Space keyboard activation independent of dwell.

## Fullscreen Requirements For Gaze Resources

- Call `document.documentElement.requestFullscreen()` once at startup. This succeeds automatically only when the browser/device policy permits it.
- Provide a Full screen button at least 120 x 120 px with visible focus/dwell feedback.
- Attach a direct native `click` listener before the general dwell manager and call `requestFullscreen()` synchronously inside it. A delayed JavaScript hover callback does not supply ordinary Edge's transient user activation.
- Hide the launch button while fullscreen is active and restore it after exit.
- If blocked, leave the board usable and announce the choices: activate Full screen with click/Enter/operating-system dwell click, press F11, or ask EQ IT to configure managed fullscreen.
- For automatic EQ deployment on Edge 132+, document `FullscreenAllowed` plus `AutomaticFullscreenAllowedForUrls`. For locked use, document Edge kiosk/Assigned Access. Do not claim that a page can set either policy itself.
- Keep Escape or the managed staff exit route available.

## Switch Requirements

If included:

- Start/Stop Scan.
- Step.
- Select.
- Escape stops scanning.
- Highlight current item strongly.
- Keep scan order equal to DOM/visual order.

## Print Requirements

- Use `@media print`.
- Hide interactive-only controls.
- Preserve board labels, borders, symbols/search terms if useful.
- Include attribution.
- Ensure black-and-white readability.

## Teacher Notes Requirements

Include concise notes:

- purpose;
- access method;
- how to model AAC use;
- how to customise labels/symbols;
- real-device/team testing caveat.

## Speech, Feedback, And Motion

- Message bar / spoken-feedback area uses `aria-live="polite"`.
- Include a one-time "Sound check" control: Edge/Chromium block `speechSynthesis` until the page has user activation, and hover-only eye-gaze input never grants it. Handle the utterance `error` event with a visible status message.
- Every button's `aria-label` must contain its visible label text (WCAG 2.5.3 Label in Name).
- Respect `prefers-reduced-motion`: keep the dwell progress indicator visible but replace the animated sweep with a static fill.
- Sticky headers or score bars must not cover the focused control (WCAG 2.4.11 Focus Not Obscured).

## Verification Snippet

When possible, verify in browser/console:

```js
document.querySelectorAll('button').length
[...document.querySelectorAll('button')].every(b => b.textContent.trim() || b.getAttribute('aria-label'))
document.querySelectorAll('script[src],link[href^="http"],img[src^="http"]').length
```

For offline files, remote dependency count should be zero unless explicitly accepted.

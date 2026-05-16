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

## Verification Snippet

When possible, verify in browser/console:

```js
document.querySelectorAll('button').length
[...document.querySelectorAll('button')].every(b => b.textContent.trim() || b.getAttribute('aria-label'))
document.querySelectorAll('script[src],link[href^="http"],img[src^="http"]').length
```

For offline files, remote dependency count should be zero unless explicitly accepted.

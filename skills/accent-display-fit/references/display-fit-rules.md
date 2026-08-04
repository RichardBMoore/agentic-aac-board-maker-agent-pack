# Display Fit Rules

Concrete layout rules and code patterns that make a single-file activity survive the real Accent/EQ viewports. These refine — never replace — the pack's canonical template and runtime.

## The Fit Formula

Check before building, at the **must-fit floor 1264 x 600**:

```text
needed_width  = cols * target + (cols - 1) * gap + horizontal_page_padding
needed_height = rows * target + (rows - 1) * gap + page_chrome

page_chrome ≈ 96 px (title + padding)   |   ≈ 166 px with a message bar
```

With the pack defaults (target 150, gap 12, padding 24):

| Grid | Needs (no message bar) | Needs (message bar) | Fits 1264 x 600? |
| --- | --- | --- | --- |
| 1 x 2, 2 x 2 | ≤ 336 x 408 | ≤ 336 x 478 | Yes |
| 2 x 3 | 498 x 408 | 498 x 478 | Yes |
| 3 x 3 | 498 x 570 | 498 x 640 | Yes / **No with message bar** |
| 3 x 4 | 660 x 570 | 660 x 640 | Yes / **No with message bar** |
| 4 x anything | — | — | **No** (4 rows x 150 + chrome > 600) |

When the maths fails you have exactly three levers, in order:

1. **Fewer cells per page** — paginate with the runtime's existing page navigation.
2. Trim page chrome (title height, padding), then gap — but keep gaps generous for gaze (the pack recommends ~20 px between gaze targets; 12 px is the template default and the practical minimum).
3. Reduce the target floor toward 120 px (never below; 120 is the interaction-contract minimum).

Scrolling in student mode and sub-120 px targets are never levers.

## Fit-First CSS Skeleton

For AAC boards rendered by `render_html.py`, keep the canonical template exactly as generated and make it fit by **passing the fit formula** (choose grid size/pagination so the template's `minmax(var(--min-target),1fr)` floors can never force overflow). The skeleton below is for **custom, non-IR activities** (stories, quizzes, writing tools) built outside the renderer; it matches the template's class/var conventions:

```css
:root { --min-target: 150px; --gap: clamp(8px, 1.2vmin, 12px); }        /* gap flexes down first */
html, body { margin: 0; height: 100%; }
body { min-height: 100vh; min-height: 100dvh; }                          /* dvh pair, vh fallback */
.student-layer { min-height: 100vh; min-height: 100dvh; padding: clamp(6px, 1vmin, 12px); }
.page-title { font-size: clamp(1rem, 2.2vmin, 1.6rem); margin: 0 0 clamp(4px, 0.8vmin, 8px); }
.board-grid {
  display: grid;
  grid-template-columns: repeat(var(--grid-columns), minmax(0, 1fr));    /* minmax(0,1fr): cells share space, never force overflow */
  grid-template-rows: repeat(var(--grid-rows), minmax(0, 1fr));
  gap: var(--gap);
  height: calc(100vh - var(--chrome, 96px));
  height: calc(100dvh - var(--chrome, 96px));
}
.dwell-btn { min-width: 0; min-height: 0; font-size: clamp(0.95rem, 2.4vmin, 1.6rem); }
```

Then **enforce** the 120 px floor with the fit formula (validator + browser test), not with `min-width:150px` on the cell. A px min-size on cells inside a fixed-count grid is exactly what forces overflow on small viewports: the grid cannot shrink, so the page scrolls. Sizing cells `minmax(0,1fr)` and controlling *cell count per page* keeps both promises: fills any screen, and targets stay ≥120 px because the maths was checked.

Text and symbols inside cells: `font-size: clamp(...)` with `vmin`, symbols `max-width:55%; max-height:55%; object-fit:contain;` (already template convention) — nothing inside a cell may have a fixed px size that exceeds a 120 px cell.

## Viewport Height

- Always the pair: `min-height:100vh;` then `min-height:100dvh;` (old engines ignore the second line; new engines prefer it).
- Never size anything from assumed device pixels (`height:1080px`, `top:900px`).
- `calc(100vh - Npx)` is acceptable only where N is the measured chrome of *this page*, and the grid inside must use `minmax(0,1fr)` rows so it can compress.
- Do not use `100vw` for widths (it includes scrollbar width on Windows and causes 17 px horizontal overflow). Use `100%`.

## Feature Baseline

Unlocked Accents can run **years-old Edge** (offline devices do not update), and the Empower browser engine is undocumented. Target ~Chromium 80 (2020) for anything structural.

| Never rely on (layout breaks silently) | Use instead / guard |
| --- | --- |
| `:has()`, `@container` queries, `subgrid`, CSS nesting | Classic selectors, media queries, plain grid |
| `dvh/svh/lvh` alone | Pair with `vh` fallback line |
| `aspect-ratio` for critical sizing | Grid `minmax(0,1fr)` cells |
| `inset: 0` shorthand on critical layers | `top/right/bottom/left: 0` or accept a guarded extra line |
| `gap` in flexbox for critical spacing | `gap` in **grid** (older), or margins |
| `text-wrap: balance`, `color-mix()`, `oklch()` | Plain values |
| JS: top-level `await`, `?.`/`??` in the **critical path**, `type="module"` | Classic script; keep modern syntax out of code that builds the visible layout |

Guard pattern for enhancements:

```css
@supports (height: 100dvh) { .student-layer { min-height: 100dvh; } }
```

**No-JS / broken-JS fallback:** the static HTML must already show the board layout and a short visible line such as "If buttons do not respond, tell your teacher." inside `<noscript>` *and* as a JS-removed element — on an old engine a syntax error kills the whole script, which otherwise leaves a silent dead page.

## Zoom And Scaling Resilience

- Survive Edge page zoom 67–150% and Windows scaling 100–200%: guaranteed by fluid rules above **if** nothing has a fixed px footprint bigger than its grid share.
- The Empower browser has student-reachable Zoom In/Out buttons — assume zoom will drift mid-session.
- Quick check: in DevTools, zoom to 150% at 1264 x 600 — no horizontal scrollbar may appear, and setup controls must stay on-screen.

## QA Viewport Matrix

Test (Playwright `npm run test:accent`, or manual DevTools device sizes) at:

| Profile | CSS viewport | Represents |
| --- | --- | --- |
| `accent-1400-150` | 1280 x 720 | 1400-30 fullscreen at 150% scaling |
| `accent-1400-chrome` | 1264 x 600 | Must-fit floor: maximised Edge, scaled |
| `accent-1400-original` | 1280 x 800 | 2013 Accent 1400 |
| `nuvoice-keymode` | 1180 x 460 | Representative half-screen computer window |
| `grace-floor` | 1024 x 460 | Published minimum-width grace contract |
| `empower-browser` | 1280 x 600 | Empower Accessible Web Browser |

Pass criteria: no horizontal scroll anywhere; no student-mode vertical scroll at must-fit sizes and above; at grace sizes no horizontal scroll and reachable, ≥120 px setup controls (content may paginate). Check `document.documentElement.scrollWidth <= innerWidth` everywhere and `scrollHeight <= innerHeight` at must-fit sizes.

## On-Page Fit Report (optional, teacher-facing)

For diagnosing a specific device, temporarily add inside the teacher panel:

```html
<p class="fit-report"></p>
<script>
(function () {
  var el = document.querySelector(".fit-report");
  if (el) { el.textContent = "Viewport: " + window.innerWidth + " x " + window.innerHeight +
    " CSS px, zoom/scale factor " + (window.devicePixelRatio || 1); }
}());
</script>
```

A teacher reading "1280 x 610" from the device tells you more than any spec sheet.

# Canvas Allowlist And Limitations

Source: Instructure, "Canvas HTML editor allowlist" (community KB article 387066), checked 21 October 2026. Canvas changes this list from time to time, so re-check it when saved pages lose something unexpectedly. `scripts/render_canvas_safe.py` encodes this list; `scripts/compare_saved_canvas_page.py` shows what a real save kept.

## What a teacher controls

A teacher controls the **body of their own course pages**: the HTML inside the rich content editor. They do not control the QLearn shell: global navigation, course menu, header, institution theme or Canvas's own CSS and JavaScript. An API token acts as the teacher. It gives **no extra privileges** and does **not** bypass the sanitiser: HTML sent through `PUT /api/v1/courses/:id/pages/:url` is cleaned exactly like HTML pasted into the editor.

## Kept

- **Elements:** `a abbr acronym address area article aside audio b bdo big blockquote br caption cite code col colgroup dd del details dfn div dl dt em embed figcaption figure font footer h1–h6 header hr i iframe img ins kbd legend li map mark nav object ol p param picture pre q rp rt ruby samp section small source span strike strong sub summary sup table tbody td tfoot th thead time tr track tt u ul var video`, plus MathML.
- **Pages remove `object`, `embed` and `param`** even though they appear on the general list.
- **Attributes on any element:** `style class id title role lang dir`, any `aria-*`, any `data-*`. The ids `body` and `length` are refused.
- **Per element:** for example `a[href target name rel download]`, `img[src alt width height srcset loading decoding title align usemap]`, `iframe[src width height title allow allowfullscreen sandbox loading …]`, `th[scope colspan rowspan …]`, `td[colspan rowspan …]`, `table[summary width border …]`, `video/audio[src controls poster muted playsinline …]`, `track[kind label src srclang default]`.
- **URL protocols** for links and images: `https: http: ftp: mailto: tel:` and relative links. `data:` images and `javascript:` links are removed.
- **Inline `style` properties:** layout (`display float overflow position` — only `static/relative/absolute` — `visibility z-index`), size (`width height min-/max-* aspect-ratio box-sizing object-fit`), spacing (`margin padding gap`), text (`color font line-height letter-spacing text-align text-decoration text-indent text-transform text-underline-offset white-space word-break …`), `background border border-radius box-shadow outline`, lists and tables, flexbox and grid, multi-column, `animation transform transition`, print breaks, `content counter-* quotes`, and interaction (`cursor opacity pointer-events user-select accent-color appearance`). Longhands of a listed shorthand are kept (`margin-top`, `border-left-color`, `background-color`).
- **iframe `sandbox` tokens** kept: `allow-modals allow-orientation-lock allow-pointer-lock allow-popups allow-popups-to-escape-sandbox allow-presentation allow-same-origin allow-scripts allow-storage-access-by-user-activation allow-top-navigation-by-user-activation allow-downloads allow-forms`. `allow-top-navigation` is removed.
- `target="_blank"` links get `rel="noopener"` on save. `data-url`, `data-method`, `data-remote`, `data-remove`, `data-confirm` and `data-disable-with` are renamed `data-custom-*`.

## Observed on QLearn (differs from the published list)

- **21 October 2026:** saving a page through the API removed `object-fit` and `box-sizing` from `<img style>` even though both appear on the published allowlist. Square symbols were unaffected. A padded symbol grew by its padding and border because the box model fell back to `content-box`. Size padded images as content box (width = target − padding − border) and don't rely on `object-fit`.
- Pages read through the API include QLearn's mobile-theme `<link>` and `<script>` tags. These are injected by QLearn rather than authored. Strip them before re-saving (QLearn re-adds them), and don't count them as content.

- **21 October 2026:** a SCORM package imported "as page" is a page whose body is one `<iframe>` to `/courses/<id>/external_tools/retrieve?borderless=true&url=…`. The same iframe can be placed in other pages to embed the tool inside a lesson, and it works there too. **But the API returns that body with the encoded `url=` parameter damaged** (`https%3A%2F%2F` becomes `https%3A%2F`). A copy made from the API version opens the course home instead of the tool. Repair it to `https%3A%2F%2F` (or copy the address from the rendered page) before saving, then check the embed in a browser. QLearn keeps the iframe's `allow="fullscreen; microphone; clipboard-write"`.

Always run `scripts/compare_saved_canvas_page.py` after saving: it reports exactly which properties the real instance kept.

## Removed or not usable on a page

- `<script>`, `<style>`, `<link>`, `<meta>`, `<form>`, `<input>`, `<button>`, `<select>`, `<textarea>`, `<canvas>`, inline `<svg>` and every `on…=` event handler. No interactivity survives, so dwell, speech buttons, drag-and-drop and self-marking quizzes cannot work on a page.
- CSS custom properties (`--name`), `position: fixed/sticky`, `@media`, `:hover`, web fonts and `@font-face`.
- Base64 (`data:`) images. Upload images to the course Files and link them, with alt text.

## Patterns that survive

- Start with one wrapper `<div>` carrying the page-level look. Every other style is inline on its element (`templates/accessible_canvas_page.html`, `templates/canvas-safe-styles.json`).
- Use real headings in order under the page title. Canvas shows the title as H1, so the body starts at H2.
- Underline links, give a link that stands alone a large padded target (48 px high), and write link text that says where it goes.
- Use `<table>` only for data, with `<th>` headers and a `<caption>` where it helps.
- Use Canvas media or `<video controls>` with captions. For an external video, use an `<iframe>` with a `title`.
- For spoken directions on a page, use Canvas's own media recorder or an `<audio controls>` file. Immersive Reader stays available to students; the page cannot auto-speak.

## Why some features need SCORM

Anything that must **do** something (speak a message, dwell-select, build a sentence, move between board pages) needs JavaScript, and Canvas pages remove all of it. Label those features SCORM-dependent and package the activity with `scripts/build_scorm.py`. Do not leave dead buttons on a page.

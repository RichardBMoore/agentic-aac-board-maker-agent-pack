---
name: eyegaze-dwell-html
description: Build accessible, single-file HTML tools for students who use eye gaze and dwell selection on PRC-Saltillo Accent AAC devices (1000/1400) running Windows with Microsoft Edge on the Education Queensland network. Use for student resources involving eye gaze, dwell activation, AAC, Accent devices, accessible HTML, QCIA/Inclusion students with complex access needs, gaze-activated choices, choice boards, quiz tools, story readers, and worksheets for non-verbal students.
---

# Eye Gaze & Dwell-Activated HTML Tools

Build everything as a **single self-contained HTML file**.

Use this skill when the resource must work for students using:
- eye gaze
- dwell activation
- AAC devices
- PRC-Saltillo Accent devices
- Microsoft Edge opened from `file:///`
- no internet / no CDN on the EQ network

## Core operating assumptions

- Eye gaze behaves like a **mouse cursor**, not touch.
- Your HTML must rely on **hover / pointer / focus states**, not touch events.
- Leaving a target must **cancel dwell**.
- Every tool must still include a **keyboard fallback**.
- Large targets matter, but **fit-on-screen matters too**. Do not make targets so large that students must constantly scroll.

## Fix-first checklist

For every eye-gaze HTML tool, confirm all of these:

- single-file HTML only
- no external CDN or internet dependency
- no touch-only interaction model
- dwell cancels on pointer leave
- visible dwell progress during activation
- high contrast focus state
- generous spacing between targets
- keyboard fallback works with Tab + Enter/Space
- high-stakes actions use confirmation dwell or a second step
- layout avoids unnecessary scrolling
- important content stays in a clear central reading/interaction area

## Packaging and display-fix workflow

Use this when an accessible HTML resource displays correctly on the build machine but incorrectly after being downloaded from Discord, opened on a phone, copied to USB/OneDrive, or opened on an EQ computer/network.

1. Check for relative assets before resending: search the HTML for `src=`, `href=`, `assets/`, `http://`, `https://`, `@import`, `fetch(`, and `type="module"`.
2. If the HTML references an `assets/` folder or local images, do not send just `index.html`. Either send a zip containing the whole folder, or preferably make an EQ-safe single-file HTML.
3. For a single-file HTML, embed local images/media as `data:` URIs so the resource works from `file:///` with no companion folder. Keep the original as a source copy and write the fixed version to a clearly named file such as `*_EQ_single_file.html`.
4. Avoid spaces in the attachment path when sending via Discord/Hermes media syntax. Copy to a short temporary filename such as `/tmp/resource_EQ_single_file.html` before attaching if needed.
5. Verify before reporting done: open the fixed file in a browser or local HTTP server, check console errors, and confirm `document.images` have `complete === true` and non-zero `naturalWidth`.
6. If the resource is large but under Discord limits, prefer a true single-file HTML for phone/EQ transfer. If too large, send a zip and clearly tell the user not to separate `index.html` from its assets folder.

Minimal Python pattern for embedding image references:

```python
from pathlib import Path
import base64, mimetypes, re
src = Path('index.html')
root = src.parent
html = src.read_text(encoding='utf-8')

def embed(rel):
    p = root / rel
    mime = mimetypes.guess_type(str(p))[0] or 'application/octet-stream'
    return 'data:%s;base64,%s' % (mime, base64.b64encode(p.read_bytes()).decode('ascii'))

html = re.sub(r'(["\\'])(assets/[^"\\']+\\.(?:png|jpg|jpeg|webp|gif|svg))\\1',
              lambda m: m.group(1) + embed(m.group(2)) + m.group(1), html)
Path('resource_EQ_single_file.html').write_text(html, encoding='utf-8')
```

## Device context

- **OS:** Windows 10 IoT LTSC or Windows 11
- **Browser:** Microsoft Edge (Chromium)
- **Eye tracker:** NuEye or Look module
- **Screens:** Accent 1000 = 10.1 inch, Accent 1400 = 14 inch, both 1920×1200
- **Environment:** EQ network, offline use, local files only

## Dwell timing guidance

| Context | Recommended dwell |
|---|---|
| Known/confident classroom tool | **800ms** |
| Unknown or first-pass generated board | 1000–1200ms |
| Student prone to accidental activation | 1000–1500ms |
| Confident gaze user | 600ms |
| Never go below | 500ms |
| Never go above | 1500ms |
| Confirmation step | 600ms |

Use 800ms for Richard-style known classroom tools when that matches the student/device context. For a new generated AAC board with an unknown eye-gaze user, start at 1000–1200ms and tune down only after real-device testing. Excessive dwell creates fatigue.

## Target size guidance

Use these as practical design rules, not rigid laws:

- **Primary dwell buttons:** start around **120px** minimum height/width
- **Ideal large-choice cells:** 150–200px when the screen can support it
- **Gap between adjacent targets:** at least 20px
- **Button text:** at least 1.4rem
- **Text contrast:** target AAA where possible

Important: if 120–200px targets force scrolling on every screen, reduce the chrome around them before you enlarge targets further.

## Layout rules

Prefer:
- single-column or simple 2-column layouts
- central interaction areas
- minimal top chrome
- minimal decorative motion
- clear vertical flow

Avoid:
- dense toolbars
- small clustered options
- wide horizontal scanning
- layouts that require constant scroll to reach the next action

## Viewport-fit troubleshooting for dynamic activities

Use this when a dwell/eye-gaze HTML activity works at first but buttons, navigation, teacher panels, or footer controls move out of view as the student progresses or responses accumulate.

1. Reproduce the issue at the tightest realistic viewport height/zoom, not only a large desktop window.
2. If bottom controls must remain visible on desktop, make the outer app a fixed viewport grid such as `height:100vh; height:100dvh; grid-template-rows:auto minmax(0,1fr) auto` rather than relying on `min-height:100vh`.
3. Add `min-height:0`, `minmax(0,1fr)`, and/or `overflow:hidden` to nested CSS grid/flex containers whose children are pushing the layout taller than the viewport. Grid children often refuse to shrink without these.
4. Constrain teacher/evidence side panels and accumulated response areas independently so they scroll or compress inside their own panel instead of expanding the whole app.
5. Preserve narrow-screen scrolling with a media query (for example, allow `body{overflow:auto}` and `height:auto` below the desktop breakpoint) rather than over-compressing gaze targets on small devices.
6. For short desktop heights, add a compact mode that trims chrome first: reduce padding/gaps/header size/panel padding before reducing dwell target size. If needed, change choice cards to a wider grid while keeping targets gaze-usable.
7. Verify dynamically: progress to the latest page/state, accumulate realistic response text, then check that `document.body.scrollHeight <= innerHeight`, footer/navigation/card rectangles do not overlap, and the browser console has no JavaScript errors.

## Core component pattern

Use a large dwell button with:
- label text
- optional symbol/image
- visible progress indicator
- strong focus styling
- completion feedback

Read these reference files when needed:
- For the reusable button CSS and markup: `references/dwell-button.md`
- For the reusable JS controller: `references/dwell-manager.md`
- For layout patterns: `references/layouts.md`
- For device/environment reminders: `references/device-context.md`
- For Richard's reusable Technology for Life starter-file pattern: `references/tech4life-starter-pattern.md`

## High-stakes actions

For actions like:
- submit
- reset
- delete
- send/export

use either:
- a second dwell to confirm, or
- a separate confirmation button/screen

Do not let a single accidental hover submit the task.

## Assessment redesign pattern

When adapting paper, Word, PDF, or ordinary digital assessments for eye-gaze / AAC students, do not simply reproduce free-text boxes. First ask what cognitive evidence the task needs, then reduce the motor load.

Prefer **guided selection builders**:
- break a paragraph/table answer into 2–4 selection steps
- show 2–4 large options per screen where possible
- let the student choose evidence, technique, meaning/effect, or sentence parts
- assemble the selected choices into a visible response for review
- keep optional free text as an extension, not the main path
- preserve assessment intent while reducing thousands of dwell keystrokes into a small number of deliberate selections

Use this especially for ICP, QCIA, English/Humanities short responses, film/image analysis, sentence builders, and scaffolded exams.

## Interaction rules

Your dwell implementation must:
- start on pointer/hover/focus entry
- show progress while dwelling
- cancel immediately on pointer leave / focus loss
- provide visible completion feedback
- optionally provide subtle audio feedback if appropriate

## Implementation pattern

Use a reusable dwell manager and large-button pattern rather than custom one-off dwell logic for every tool.

If you are building a new resource from scratch, read:
- `references/dwell-button.md`
- `references/dwell-manager.md`
- `references/layouts.md`

## Accessibility rules

Always include:
- visible focus state
- keyboard fallback
- forced-colors / high contrast support where practical
- clear labels
- no reliance on colour alone
- pointer cancellation

Relevant WCAG principles here include:
- Pointer Cancellation
- Focus Visible / Focus Appearance
- Keyboard operability
- Target Size

## Design judgement reminder

Do not apply the guidance mechanically.

For eye gaze, the correct balance is:
- large enough targets
- enough spacing to prevent misfires
- enough dwell feedback to reduce uncertainty
- but still compact enough to keep the task on screen

When in doubt, prioritise:
1. no accidental activation
2. clear dwell progress
3. no unnecessary scrolling
4. simple, central layouts
5. consistent behaviour across the whole tool

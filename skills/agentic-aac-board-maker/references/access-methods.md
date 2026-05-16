# Access Methods

The access method determines board density, layout, target size, navigation, and safety. Do not design visually first.

## Universal Baseline

Every digital board should support:

- semantic buttons;
- keyboard Tab + Enter/Space;
- visible focus;
- clear labels;
- no reliance on colour alone;
- Stop Speech if using TTS;
- no single accidental activation for destructive actions.

## Touch / Direct Selection

Use when the student can directly select targets.

- Minimum target: around 44 CSS px for general web access; for AAC classroom boards, prefer 96 px+.
- Support larger targets when motor accuracy is variable.
- Avoid tiny toolbars near main student choices.
- Consider keyguards if used in the real device context, but do not assume one.

## Eye Gaze / Dwell

Eye gaze usually behaves like a mouse pointer. Build with pointer enter/leave and focus fallback.

Rules:

- Prefer 2x2, 2x3, 3x3; avoid dense 4x4 unless tested.
- Target floor: 120 px; 150–200 px for small boards when screen allows.
- Gap: 20 px where practical.
- Dwell default: 1000–1200 ms; 1500 ms for accidental activation risk; 600–800 ms only for confident users.
- Show visible dwell progress.
- Cancel immediately on pointer leave/blur.
- Prevent repeat firing while gaze stays on one target.
- Keep important controls on screen; reduce chrome before shrinking targets.
- High-stakes actions need a confirm step.

## Mouse Dwell / Head Mouse / Joystick Mouse

Similar to eye gaze but may tolerate slightly denser layouts depending on user control. Still provide:

- visible hover/dwell;
- cancellation;
- large targets;
- no hover-only hidden menus.

## Switch Scanning

Start simple.

- Use linear scanning for small boards.
- Use row-column scanning for larger grids.
- Keep visual order, DOM order, and scan order aligned.
- Provide Start/Stop Scan, Step, Select.
- Support Escape to stop when keyboard is available.
- Use strong highlight not dependent on colour alone.
- Avoid excessive button counts; scanning time grows quickly.

## Partner-Assisted Scanning / Print

For low-tech or partner-assisted use:

- Use strong borders and whitespace.
- Include row/column labels if useful.
- Keep scan order obvious.
- Provide a partner note: pause, point/read options consistently, wait for signal, confirm selection.
- Include repair options such as wrong one, again, stop, finished.

## High Contrast / Vision

- Use high contrast text and borders.
- Do not encode correctness or state by colour alone.
- Use plain fonts and generous spacing.
- Avoid busy symbol backgrounds.
- Provide black-and-white print viability.

## Access QA By Output

### HTML

- Open file locally.
- Tab through controls.
- Enter/Space activate.
- Pointer leave cancels dwell.
- No console errors.
- No external dependencies if promised offline.

### JSON

- Parse JSON.
- Check target sizes implied by grid.
- Check access settings and metadata.

### Print

- Print preview readable.
- Borders visible.
- Text large enough.
- Attribution present.

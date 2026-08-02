# Intake And Decision Tree

Avoid unnecessary questioning, but do not design a student-specific access system from topic and diagnosis alone. Gather, infer, and visibly record the information that determines whether the resource fits the student's existing communication and access setup.

## Three Intake Layers

### 1. Resource intent

- communication/participation purpose and context;
- curriculum/QCIA evidence need, if any;
- age band, tone, language(s), and output format;
- required vocabulary and privacy constraints.

### 2. Existing communication system

- established AAC/device/low-tech system and whether this resource supplements it;
- familiar vocabulary, stable word locations/motor patterns, symbol set, photos, text or objects already understood;
- preferred voice/pronunciation and culturally meaningful representations;
- reliable yes/no, refuse, cancel, repair, wait and partner-interpreted signals.

### 3. Real access conditions

- access method and current dwell/scan/calibration settings;
- actual screen/device/browser, mounting, seating, reach and positioning;
- visual field, contrast, lighting and fatigue considerations;
- accidental-selection pattern, reliable cancellation and staff setup needs.

Record layer 2–3 findings in canonical IR `systemFit`. Use `team-input-needed` where they remain assumptions.

## Ask Only When It Changes The Design

Ask when access method could change density, student-specific symbol support is requested without known representations, stable vocabulary/motor patterns might be displaced, sensitive data/media rights are unclear, or curriculum judgement depends on the exact standard. Otherwise proceed with labelled assumptions.

## Safe Defaults

- Australian English; anonymous data; age-respectful secondary-safe tone.
- Single-file HTML for direct classroom use; Open AAC Studio JSON only when explicitly requested.
- Touch + keyboard baseline. Add gaze/dwell or scanning only when requested or clearly established.
- Text fallback and ARASAAC search candidates; no automatic symbol choice in the recommended workflow.
- 3×3 direct-selection board or 2×2/2×3 gaze board; Help plus refusal/repair where meaningful.
- Resource is a draft companion to—not a replacement for—the student's full communication system.

## Pattern And Output Routing

- preference/consent → yes/no or choice board;
- routine/transition → first-then or expressive visual schedule;
- needs/distress/repair → needs/repair board;
- understanding/evidence → curriculum participation board with uncertainty, repair and explanation;
- constructed speech/writing → sentence builder with a functioning message bar;
- print/laminate → printable HTML with partner scan order;
- explicit Open AAC Studio/import/schema → Open AAC Studio JSON renderer;
- full pack → canonical IR + generated HTML + appropriate interchange export + teacher notes.

## Access Routing

- Eye gaze/dwell: explicit setup phase, no more than three setup targets, large cells, pointer-leave cancellation, one shared runtime, and no more than nine active board targets unless genuinely device-tested.
- Switch: predictable DOM/scan order, linear first, fatigue-aware density and a reliable stop route.
- Keyboard: native buttons, visible focus, Enter/Space and logical order.
- Partner-assisted print: numbered/declared scan order, wait-confirm script and black-and-white readability.

Use `templates/teacher-intake.md` for the compact user-facing questions.

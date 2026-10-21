# Accessibility Acceptance Checks

Automated checks catch structure; people catch meaning. Each item says who or what checks it.

## Canvas page (`canvas_page` target)

| Check | Target | Checked by |
| --- | --- | --- |
| Every word, link, image (with alt) and media item kept | 100% | `render_canvas_safe.py` inventory + `compare_saved_canvas_page.py` after save |
| Only allowlisted HTML/CSS | No `<script>`, `<style>`, handlers or form controls | `render_canvas_safe.py`; `tests/test_canvas_safe.py` |
| Headings | Start at H2 under the page title; no skipped levels | Script; teacher confirms the outline reads sensibly |
| Text contrast | ≥ 4.5:1 normal text, ≥ 3:1 large text and UI borders (WCAG 2.2 AA) | Script replaces failing source colours; house palette tested |
| Colour meaning | Nothing is conveyed by colour alone | **Teacher** (script warns whenever it changes a colour) |
| Text size and spacing | Body 18 px, line height 1.6, line length ~46em; no source text under 16 px | Script |
| Link targets | Underlined; a link on its own line is a 48 px padded target; link text says where it goes | Script styles and warns; **teacher** rewords vague links |
| Images | Meaningful alt text, or `alt=""` if decorative; no base64 | Script blocks saving; **teacher** writes the alt text |
| Tables | Data tables have `<th>` headers | Script warns; **teacher** decides |
| Media | Captions for video; titles on iframes | Script warns; **teacher** checks |
| Zoom/reflow | Readable at 200% zoom without sideways scrolling | **Teacher** in the browser |
| Keyboard and screen reader | Tab order follows reading order; headings navigable | **Teacher**, ideally with a student or support staff |
| Curriculum | Learning intention, stimulus and instructions unchanged unless the teacher asked | **Teacher** |

## SCORM activity (`scorm` target)

| Check | Target | Checked by |
| --- | --- | --- |
| Package valid and self-contained | No FAIL lines; nothing loads from the internet | `validate_scorm.py` (also run by the builder) |
| Activity unchanged | Byte-for-byte the original plus the bridge | `validate_scorm.py --source`; `tests/test_scorm_packaging.py` |
| Board quality | All existing pack gates green before packaging | `check_pack.py`, the Playwright suite, the `aac-board-qa` agent |
| Gaze targets | ≥ 120 px (board minimum honoured), spaced, fixed positions, visible dwell progress, cancel on leave, one activation, re-arm | Pack runtime + `browser-tests/scorm-package.spec.mjs` in a nested frame |
| Communication | Ask, refuse, comment, repair, stop, finished, spell where suitable; not quiz-only | Board IR + house standards; **team** review |
| Speech | Spoken output without Immersive Reader; failures announced | Runtime; **teacher** confirms voices on the device |
| Fullscreen | Visible control; blocked state announced; board usable either way | Browser test (blocked case); **teacher** records the real result |
| Fit | No clipping at the real frame size; full-size targets | Browser test at 960 × 600; **teacher** records it on the device |
| Dictation (STT) | Only where proven; always an equivalent non-speech route | **Not claimed.** Record in the results sheet |
| Real device | Student's Accent, access method, mounting, browser, delivery route | **Student and team trial** (`references/teacher-scorm-upload-guide.md`) |

## Before anything is called ready

1. All automated checks are green.
2. The teacher has reviewed accessibility and curriculum alignment.
3. The student and relevant AAC/OT/SLP team have trialled the real access method on the real device.
4. Unknowns are written down as unknowns, not as passes.

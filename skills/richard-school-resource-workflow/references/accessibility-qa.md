# Accessibility QA Checklist

Use this before calling a student-facing resource done.

## General

- Clear purpose and simple instructions.
- No unnecessary clutter.
- Student can complete the task without hidden teacher-only knowledge.
- Reading level fits the target student, unless curriculum language is intentionally retained.
- High contrast or readable colour scheme.
- Focus states are visible.
- Keyboard fallback works with Tab + Enter/Space.
- Buttons/inputs have clear labels.
- No reliance on colour alone.
- No internet/CDN dependency when offline use is required.

## Eye gaze / dwell

- Eye gaze treated as mouse cursor/hover, not touch.
- Dwell starts on pointer/focus entry.
- Dwell cancels immediately on pointer leave/focus loss.
- Visible dwell progress.
- Targets large enough, with spacing to prevent misfires.
- No constant scrolling to reach main actions.
- High-stakes actions use confirmation dwell or a second step.
- Excessive text entry avoided; use guided selection builders where appropriate.

## AAC / low text output

- Response options are meaningful, not tokenistic.
- Student can express a defensible answer without excessive typing.
- Optional free-text is optional, not required for baseline success.
- TTS/read-aloud supports independent review.

## Switch / joystick / gamepad

- Gamepad API uses polling.
- Dead zone included for sensitive joystick.
- Press-any-button/start screen included if needed.
- One or two switch operation considered.
- Keyboard fallback included where practical.

## Final judgement

- Does this remove the access barrier while preserving curriculum intent?
- Would the evidence produced be defensible?
- Is it practical in a real classroom session?

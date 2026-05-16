# Device and Environment Context

Use this when you need the hardware/browser context.

- **OS:** Windows 10 IoT LTSC or Windows 11
- **Browser:** Microsoft Edge (Chromium)
- **Launch mode:** `file:///` from USB or local storage
- **Devices:** PRC-Saltillo Accent 1000 and 1400
- **Eye tracker:** NuEye or Look module
- **Display:** 1920×1200
- **Environment:** Education Queensland network, no CDN, no internet during student use

## Important operating rule

Eye gaze behaves like a **mouse cursor**.

That means:
- hover and pointer events matter
- touch-only interaction patterns will fail
- dwell must cancel when the cursor leaves the target
- pointer/hover/focus patterns are safer than touch assumptions

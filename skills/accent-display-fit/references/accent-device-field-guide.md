# Accent Device Field Guide

Sourced facts about the environment student HTML actually runs in. Researched August 2026; treat as defaults to verify on the student's own device, not guarantees.

## Hardware And Operating System

| Device | Screen | Native resolution | OS |
| --- | --- | --- | --- |
| Accent 1400-30 (current) | 14 in | 1920 x 1080 | Windows 10 Pro on most fielded units; Windows 11 Pro on current shipments |
| Accent 1400 original (ACN1400, 2013) | 14.1 in | 1280 x 800 | Older Windows |
| Accent 1000-series | ~10 in class | varies by revision | Windows 10/11 |

Sources: PRC-Saltillo Accent 1400-30 specifications (documentation.prc-saltillo.com/docs/accent-1400-30-specifications); Accent 1400-30 Hardware Manual 18751 v1.02; PRC april-2024 fix pages (Windows 10 applied to "Accent 1400 (all serial numbers)"); AZTAP Accent 1400 info sheet (2013 model, 1280 x 800). One Empower user guide (18743 v2.12) lists 2560 x 1440 — unresolved documentation conflict; three other official sources say 1920 x 1080.

## Windows Display Scaling — The Main Layout Killer

Windows commonly recommends **150% scaling for a 14 in 1920 x 1080 panel**. At 150%, the browser reports a viewport of about **1280 x 720 CSS px**. No PRC document establishes the device's configured default, so use 150% only as a conservative planning assumption until it is checked on the device (Settings > System > Display > Scale).

Effective viewport = native resolution ÷ scale factor − browser chrome:

| Scale | 1920 x 1080 becomes | Minus maximised-Edge chrome (~110 px) |
| --- | --- | --- |
| 100% | 1920 x 1080 | 1920 x ~970 |
| 125% | 1536 x 864 | 1536 x ~754 |
| 150% (planning assumption) | 1280 x 720 | 1280 x ~610 |
| 175% | 1097 x 617 | 1097 x ~507 |

This is why a file built and tested at 1920 x 1080 "doesn't display correctly on the Accent" while looking perfect on a monitor at 100%.

## NuVoice And The Browser

- **NuVoice has no built-in browser.** Dedicated devices get Wi-Fi for updates only, with no internet browser (NuVoice Software Manual 15444 v2.9, p.62).
- The **Integrated Feature Pack (IFP)** — a paid unlock (about USD 15) — makes the device non-dedicated and exposes the normal Windows environment, where browsing happens in Microsoft **Edge** (prc-saltillo.com/dedicated-non-dedicated).
- In NuVoice **Key Mode**, the vocabulary shrinks to 2–4 rows at the bottom and Windows applications "go to a half-screen or smaller size" (manual pp.146, 172). A browser sharing the screen this way may give the page roughly **1180 x 460 CSS px or less**.
- NuVoice can also be hidden entirely (Hide/Show NuVoice), giving the browser the full screen.
- Because unlocked Accents are often kept offline, **Edge may be years out of date** — avoid cutting-edge CSS/JS (see `display-fit-rules.md`).

## Empower And Its Accessible Web Browser

- Empower ships an **Accessible Web Browser** "specifically designed for use with head tracking and eye tracking"; requires software ≥1.06 and the IFP on dedicated devices (documentation.prc-saltillo.com/docs/web-browser.md).
- Layout: **two rows of control buttons across the top** (Prev/Next, URL bar, Favourites, Zoom In/Out, Tab Left/Right + Select Link, Read Mode, Page/Section Scroll); the rest is the page. Plan for ~1280 x ~600.
- It navigates by **Select Link** and scroll buttons — semantic buttons/links are mandatory.
- It **cannot download or upload files or print** — a OneDrive link to an .html file is a dead end in this browser. Use USB or an IT-hosted URL for Empower devices.
- Rendering engine is undocumented (Chromium-based is plausible but unconfirmed) — another reason for the conservative feature baseline.

## Eye Tracking (NuEye / Look)

- The tracker gives "full visual control of the device"; selection by blink, dwell or switch.
- In Windows apps, gaze drives the **OS mouse pointer**. NuVoice's Windows Access settings include a **Windows Dwell Time (default 1.0 s)** and a **Mouse Post-Select menu** (Left Click / Right Click / Double Click / Click & Hold) — dwelling in a browser fires a **real click** (NuVoice manual pp.105–107, 226).
- Empower's default selection is 0.8 s auto dwell.
- Consequences for HTML: click activation is first-class on-device; page hover-dwell must not double-fire with the OS click; the page's dwell time should be chosen with the team relative to the OS dwell, not independently.
- That gaze presents to a web page exactly like a moving mouse is inference from the manuals, not a PRC-stated fact — verify hover behaviour on the student's device.

## Getting Files Onto The Device

- A **USB flash drive ships as a standard component** with the Accent 1400-30, and PRC's own update workflows use USB.
- Non-dedicated devices expose the Windows desktop, Downloads folder and Edge.
- OneDrive/SharePoint behaviour and the EQ-specific delivery routes are covered in `eq-delivery-playbook.md`.

## Quick On-Device Checks

1. Settings > System > Display: note **Scale** and **Resolution**.
2. Open Edge, press F12 is often blocked — instead visit a local test page that prints `innerWidth x innerHeight`, or use the fit report the validator template prints.
3. Note whether the student uses NuVoice hidden, Key Mode, or the Empower browser — each changes the viewport.
4. `edge://version` shows the Edge build; if it is old and the device is offline, the conservative baseline matters.

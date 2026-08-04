# EQ Delivery Playbook

How a single-file HTML activity actually reaches a student's Accent (or EQ laptop) on the Education Queensland network — and what goes wrong on the way.

## The Core Fact

**OneDrive and SharePoint do not serve HTML files as web pages.** A shared link either force-downloads the file or shows the raw source in a preview pane. Sending a OneDrive link is therefore a *transfer* step, never a *display* step. Every delivery must end with the file opened locally in a real browser (usually Edge from `file:///`) or hosted on a real web server.

## Route A — OneDrive link, download, open in Edge (default for NuVoice + IFP devices)

1. Upload the `.html` file to OneDrive/SharePoint and share the link (EQ accounts: keep sharing within the organisation).
2. On the Accent (NuVoice hidden or Key Mode, Windows side): open the link in **Edge**, choose **Download**, then open the file from the **Downloads** folder (Ctrl+J → open, or File Explorer → double-click).
3. First open may warn because the download carries **Mark of the Web**. Only for a verified, internally supplied file whose name and version you expect, choose **Keep** if SmartScreen queries it. Do not bypass a warning for an unknown or unexpected file; stop and ask school IT. If a verified file then appears inert, right-click it → Properties → tick **Unblock** → OK.
4. Press **F11** (or use the file's Full screen button) before handing to the student.

Troubleshooting:

| Symptom | Cause | Fix |
| --- | --- | --- |
| Browser shows code instead of the activity | OneDrive preview / opened raw source | Download the file and open the local copy |
| Download blocked | EQ filtering or SmartScreen policy | Try from the teacher account, use Route B, or ask school IT to allow the file |
| Opens but layout broken/cut off | Display scaling / viewport | This is a build problem — apply `accent-display-fit` |
| Opens blank/white | Very old Edge engine or a JS error | Rebuild against the conservative baseline; check the file's no-JS fallback message |

## Route B — USB drive (works everywhere, including Empower)

A USB flash drive ships with every Accent 1400-30 and PRC's own workflows use USB.

1. Copy the `.html` file (and nothing else it depends on — it must be self-contained) to USB.
2. On the Accent: File Explorer → USB drive → double-click the file (opens in Edge). Copy it into `Documents` or `Desktop` first if the drive will be removed.
3. Files copied via USB usually carry no Mark of the Web, so they open without warnings.

Use Route B whenever downloads are blocked, for **Empower's Accessible Web Browser devices** (that browser cannot download files at all — a colleague loads the file onto the device once, or IT hosts it), and for offline classrooms.

## Route C — Hosted URL (for Empower browser and locked-down setups)

If the school can host the file (school intranet, IT-managed web space), the Empower browser and managed Edge can open it directly by URL.

- Ask IT for an **https** location reachable inside the EQ network; give them the single file.
- A trusted https origin is also the safest target for the Edge automatic-fullscreen policy below.
- Public hosting of student-specific resources is a privacy decision — keep files name-free (pack law) and prefer intranet hosting.

## EQ-Managed Edge Notes

- EQ filters web traffic (Broadcom/Symantec WebFilter categories). CDNs, font services and symbol APIs may be blocked on the school network even when the page itself opens — another reason the file must be fully self-contained.
- Fullscreen: the pack's existing guidance applies (Edge 132+ `FullscreenAllowed`, `AutomaticFullscreenAllowedForUrls`; kiosk/Assigned Access for locked use). `file:///*` in that policy covers *every* local file — flag that scope honestly when asking IT.
- School devices are Intune-managed; teachers cannot change Edge policies from the page or the device. Anything needing policy goes through school IT/Managed Internet Service.

## Teacher Handover Checklist

Copy into teacher notes for each delivered file:

1. Transfer: OneDrive link (download, don't preview) or the supplied USB copy.
2. Open the downloaded/copied file in Edge on the device — not the OneDrive preview.
3. If a verified internal file is warned, choose Keep / Unblock once; send unknown or unexpected files to school IT.
4. Go fullscreen (F11 or the Full screen button) before the student starts.
5. Check the layout fills the screen with no scrollbars. If anything is cut off, note the device model and Settings > Display > Scale value and report back — do not hand a scrolling page to a gaze user.
6. Know the exit: Esc leaves fullscreen; Alt+F4 closes.

## Naming And Versioning

- Name files `activity-topic-vX.html` (no student names — pack privacy law).
- When updating, bump the version in the filename and delete stale copies from Downloads/USB, or the student gets the old file forever.

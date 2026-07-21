# Open AAC Studio Classroom Deployment

## Recommended classroom launch

Use the local server during trials:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Open the classroom player:

```text
http://127.0.0.1:4173/player.html?classroom=1
```

For managed Windows or Edge deployments, pin or install the PWA from the browser. The manifest starts directly at `player.html?classroom=1`, requests fullscreen display, and the player calls the Fullscreen API at startup. Ordinary Edge still requires user activation, but managed Edge 132+ can allow the startup call with the policy below.

## Enforced fullscreen on the EQ network

The network itself does not grant fullscreen permission. EQ IT must deploy a Microsoft Edge or Windows device policy. Use one of these supported routes.

### Route 1: automatic Fullscreen API

For Microsoft Edge 132 or later:

1. Enable the mandatory Edge policy `FullscreenAllowed`.
2. Add the trusted activity origin to `AutomaticFullscreenAllowedForUrls` under **Administrative Templates > Microsoft Edge > Content settings > Allow automatic full screen on specified sites**.
3. Prefer a specific HTTPS school origin, for example `https://aac.example.eq.edu.au`. For this local server workflow, allow the exact localhost origin used for deployment. The only valid wildcard for local files is `file:///*`; it applies to every local file, so use it only after EQ security review.
4. Open `player.html?classroom=1`. The player requests fullscreen automatically and keeps the ordinary Start Classroom/F11 fallback if policy is missing or blocked.

This route removes browser chrome but still preserves Escape for staff.

### Route 2: locked Edge kiosk

Use Digital/Interactive Signage kiosk mode when the activity must remain locked full screen:

```bat
msedge.exe --kiosk "https://trusted-school-origin/player.html?classroom=1" --edge-kiosk-type=fullscreen --no-first-run
```

Deploy and manage the kiosk with Windows Assigned Access, Intune, or the EQ-approved equivalent. Test one device first, including the staff exit procedure, eye tracker, TTS, local storage, offline symbols, and any permitted URLs. A page cannot install these policies itself.

## Before a lesson

1. Open the editor.
2. Build or load the activity.
3. Use `Fix Symbols` if any symbols are missing.
4. Use `Prepare Offline` while the network is available.
5. Check the offline readiness banner. It should show the app cache and symbol-cache state.
6. Open `Classroom Player`.
7. Confirm automatic fullscreen starts under the managed policy. Otherwise press `Start Classroom` or F11.

`Prepare Offline` stores ARASAAC symbol images in IndexedDB. The player then prefers cached images when available, including on `file://` style launches where service workers cannot run.

## Network allowlist

Allow live symbol search and symbol image loading from:

```text
https://api.arasaac.org
```

The app itself is local-first. Once boards and symbols are prepared, a network drop should not stop the current activity.

## Privacy

Student profiles and session logs stay on the local device. On shared classroom laptops, use `Clear Data` in the player session panel before handing the device to another class, or use anonymous mode for routine classroom use.

## Production checks

- Use `Large AAC` for eye gaze users where possible.
- Prefer fullscreen for eye gaze so tabs and browser chrome cannot become accidental gaze targets.
- Confirm the intended Fullscreen API policy or kiosk configuration on the actual EQ-managed device before the lesson.
- Use the player `Contrast` control for students who need high contrast, black-and-white, or yellow-on-black presentation.
- Keep boards at 16 buttons or fewer for classroom play.
- Use `Compact` only when the board still fits the student access method.
- Test Symbolate and conditional-action boards in the player before using them live.
- Prefer action presets for common classroom behaviours, then adjust the detailed action controls only when needed.
- Keep media URLs on trusted `https://` sources and check they work on the school network.
- Confirm TTS works on the device before the lesson.
- Confirm symbols still show after disconnecting the network.

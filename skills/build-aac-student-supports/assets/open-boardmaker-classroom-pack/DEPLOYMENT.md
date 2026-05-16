# Open Boardmaker Classroom Deployment

## Recommended classroom launch

Use the local server during trials:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Open the classroom player:

```text
http://127.0.0.1:4173/player.html?classroom=1
```

For managed Windows or Edge deployments, pin or install the PWA from the browser. The manifest starts directly at `player.html?classroom=1` and requests fullscreen display. Browser security still requires a user gesture, managed kiosk policy, or F11 for true fullscreen.

## Before a lesson

1. Open the editor.
2. Build or load the activity.
3. Use `Fix Symbols` if any symbols are missing.
4. Use `Prepare Offline` while the network is available.
5. Check the offline readiness banner. It should show the app cache and symbol-cache state.
6. Open `Classroom Player`.
7. Press `Start Classroom` on the player device.

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
- Use the player `Contrast` control for students who need high contrast, black-and-white, or yellow-on-black presentation.
- Keep boards at 16 buttons or fewer for classroom play.
- Use `Compact` only when the board still fits the student access method.
- Test Symbolate and conditional-action boards in the player before using them live.
- Prefer action presets for common classroom behaviours, then adjust the detailed action controls only when needed.
- Keep media URLs on trusted `https://` sources and check they work on the school network.
- Confirm TTS works on the device before the lesson.
- Confirm symbols still show after disconnecting the network.

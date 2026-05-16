# Activity Schema

Use portable JSON for classroom activities so boards can be edited, imported, exported, printed, and played by different tools.

## Minimal Shape

```json
{
  "schemaVersion": "0.1.0",
  "app": "Student Support",
  "id": "activity-morning-choice",
  "name": "Morning Choices",
  "type": "interactive",
  "settings": {
    "speakLabels": true,
    "showLabels": true,
    "dwellTimeMs": 1200,
    "switchScanning": false,
    "scanSpeedMs": 1400,
    "scanPattern": "linear"
  },
  "accessibility": {
    "intendedAccess": ["touch", "mouse", "keyboard", "eye-gaze-dwell", "switch-scanning"],
    "minimumTargetSizePx": 96,
    "dwellSafe": true,
    "scanOrder": "dom-order",
    "audioCues": true
  },
  "pages": [
    {
      "id": "page-choices",
      "name": "Choices",
      "layout": "grid",
      "gridColumns": 2,
      "gridRows": 2,
      "buttons": [
        {
          "id": "btn-more",
          "label": "More",
          "symbolId": "5508",
          "symbolSrc": "https://api.arasaac.org/api/pictograms/5508?download=false&color=true&resolution=500",
          "symbolLayout": "label-bottom",
          "audioCue": "More",
          "result": "selected",
          "actions": [
            { "id": "act-more-speak", "type": "speak-label" },
            { "id": "act-more-log", "type": "log-attempt" }
          ]
        }
      ]
    }
  ],
  "metadata": {
    "privacyLevel": "anonymous",
    "tags": ["choice-board"]
  },
  "licences": [
    {
      "source": "ARASAAC",
      "licence": "CC BY-NC-SA",
      "attribution": "Pictograms by ARASAAC/Government of Aragon; preserve source-specific attribution."
    }
  ]
}
```

## Recommended Fields

- `schemaVersion`: Increment when changing data shape.
- `id`: Stable activity ID. Avoid using student names.
- `settings`: Player defaults. Student-specific overrides should live separately.
- `accessibility`: Intended access methods and constraints.
- `pages`: Ordered list of screens.
- `buttons`: Student targets. Use stable IDs, labels, optional symbol IDs, result, and actions.
- `metadata.privacyLevel`: Use `anonymous` unless named profiles are explicitly required.
- `licences`: Keep source, license, attribution, and modification notes.

## Actions

Common actions:

- `speak-label`: Speak the button label.
- `speak-text`: Speak custom text.
- `log-attempt`: Store a minimal session row.
- `next-page`: Move to next page.
- `previous-page`: Move to previous page.
- `navigate-page`: Go to a page ID.
- `mark-correct`: Mark activation as correct.
- `mark-incorrect`: Mark activation as incorrect.
- `set-variable`: Store a value.
- `increment-variable`: Add to a numeric value.
- `conditional`: Choose an action based on a variable.
- `play-audio`: Play teacher-owned or local audio.
- `open-url`: Use sparingly, because school networks and offline use may block it.

## Logging

Keep logs minimal:

```json
{
  "timestamp": "2026-05-11T07:30:00.000Z",
  "studentName": "",
  "activityName": "Morning Choices",
  "pageName": "Choices",
  "buttonId": "btn-more",
  "label": "More",
  "method": "dwell",
  "result": "selected"
}
```

Avoid storing diagnosis, behaviour notes, medical details, case-management details, or parent contact details in activity files or logs.

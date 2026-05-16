# Layout Patterns

Use these when designing specific tool layouts.

## Full-screen boilerplate

```html
<!DOCTYPE html>
<html lang="en-AU">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Activity Title</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { height: 100%; overflow: hidden; font-family: 'Segoe UI', Arial, sans-serif; }
    :root {
      --dwell-colour: #0057b8;
      --dwell-hover-bg: #ddeeff;
      --dwell-complete-colour: #00843d;
      --btn-border-radius: 16px;
    }
  </style>
</head>
<body>
  <!-- content -->
</body>
</html>
```

## 2-choice layout

```css
.choice-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  padding: 1.5rem;
  height: 100vh;
}
```

## 4-choice quiz grid

```css
.answers-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 1rem;
  height: 80vh;
}
```

## Story-reader layout

```css
.story-page {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  align-items: center;
  height: 75vh;
}
```

## Layout judgement rules

Prefer:
- central content
- simple grids
- low visual clutter
- no unnecessary sticky bars
- no forced scroll where avoidable

If large buttons force scrolling, reduce surrounding chrome before shrinking the buttons too far.

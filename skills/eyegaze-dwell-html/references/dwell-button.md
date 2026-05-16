# Dwell Button Pattern

Use this when you need the core eye-gaze button component.

## Markup

```html
<button class="dwell-btn" data-dwell-time="800" aria-label="Describe option here" tabindex="0">
  <div class="btn-content">
    <img class="btn-symbol" src="" alt="symbol description" aria-hidden="true">
    <span class="btn-label">Label Text</span>
  </div>
  <div class="dwell-ring" aria-hidden="true"></div>
</button>
```

## CSS

```css
:root {
  --dwell-colour: #0057b8;
  --dwell-hover-bg: #ddeeff;
  --dwell-complete-colour: #00843d;
  --btn-border-radius: 16px;
}

.dwell-btn {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 150px;
  min-height: 150px;
  padding: 1.5rem;
  border: 4px solid #334;
  border-radius: var(--btn-border-radius);
  background: #ffffff;
  cursor: pointer;
  overflow: hidden;
  transition: background 0.15s, border-color 0.15s, transform 0.1s;
  -webkit-appearance: none;
  appearance: none;
  font-family: inherit;
  font-size: 1.4rem;
  font-weight: 700;
  color: #222;
  user-select: none;
}

.dwell-btn:hover,
.dwell-btn:focus-visible {
  background: var(--dwell-hover-bg);
  border-color: var(--dwell-colour);
  outline: 4px solid var(--dwell-colour);
  transform: scale(1.02);
}

.dwell-btn.is-dwelling {
  background: var(--dwell-hover-bg);
  border-color: var(--dwell-colour);
}

.dwell-btn.dwell-complete {
  background: #d4edda;
  border-color: var(--dwell-complete-colour);
}

.btn-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  z-index: 1;
  pointer-events: none;
}

.btn-symbol {
  width: 80px;
  height: 80px;
  object-fit: contain;
}

.btn-label {
  font-size: 1.4rem;
  font-weight: 700;
  color: #222;
  line-height: 1.2;
}

.dwell-ring {
  position: absolute;
  inset: 0;
  border-radius: var(--btn-border-radius);
  background: conic-gradient(var(--dwell-colour) 0%, transparent 0%);
  opacity: 0.25;
  z-index: 0;
  pointer-events: none;
  transition: opacity 0.1s;
}

.dwell-btn.is-dwelling .dwell-ring {
  opacity: 0.35;
}

.dwell-btn.dwell-complete .dwell-ring {
  background: conic-gradient(var(--dwell-complete-colour) 100%, transparent 0%);
  opacity: 0.4;
}

@media (forced-colors: active) {
  .dwell-btn {
    border: 3px solid ButtonText;
    background: ButtonFace;
    color: ButtonText;
  }

  .dwell-btn:hover,
  .dwell-btn:focus-visible {
    outline: 4px solid Highlight;
  }
}
```

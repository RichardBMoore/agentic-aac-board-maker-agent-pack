# Eye Gaze HTML Templates

Use this file only when implementing a single-file dwell HTML tool. For a complete starter file, copy `../assets/eye-gaze-single-file-template.html` and replace the activity data.

## Contents

- CSS variables
- Dwell button CSS
- DwellManager
- Speech helper
- Confirmation modal pattern
- Layout snippets
- QA snippets

## CSS Variables

```css
:root {
  --text-dark: #1a1a2e;
  --interactive: #003f88;
  --interactive-soft: #e8f1ff;
  --success: #005f2e;
  --alert: #9f0000;
  --bg-warm: #f9f7f2;
  --bg-dark: #1a1a2e;
  --button-bg: #ffffff;
  --button-border: #2f3445;
  --dwell-colour: var(--interactive);
  --dwell-hover-bg: var(--interactive-soft);
  --dwell-complete-colour: var(--success);
  --btn-border-radius: 16px;
  --target-min: 150px;
  --target-gap: 24px;
}
```

## Dwell Button CSS

```css
.dwell-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: var(--target-min);
  min-height: var(--target-min);
  padding: 1.25rem;
  border: 4px solid var(--button-border);
  border-radius: var(--btn-border-radius);
  background: var(--button-bg);
  color: var(--text-dark);
  cursor: pointer;
  overflow: hidden;
  font: inherit;
  font-size: 1.4rem;
  font-weight: 800;
  line-height: 1.15;
  text-align: center;
  -webkit-appearance: none;
  appearance: none;
  user-select: none;
  transition: background 120ms ease, border-color 120ms ease, transform 120ms ease;
}

.dwell-btn:hover,
.dwell-btn:focus-visible,
.dwell-btn.is-dwelling {
  background: var(--dwell-hover-bg);
  border-color: var(--dwell-colour);
  outline: 4px solid var(--dwell-colour);
  outline-offset: 3px;
}

.dwell-btn:hover,
.dwell-btn.is-dwelling {
  transform: scale(1.015);
}

.dwell-btn.dwell-complete {
  background: #e7f6ea;
  border-color: var(--dwell-complete-colour);
  outline-color: var(--dwell-complete-colour);
}

.btn-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.65rem;
  pointer-events: none;
}

.btn-symbol {
  display: grid;
  place-items: center;
  width: 84px;
  height: 84px;
  border: 3px solid #d3d8e6;
  border-radius: 14px;
  background: #f7f9fc;
  color: var(--text-dark);
  font-size: 2rem;
  font-weight: 900;
}

.btn-label {
  max-width: 100%;
  overflow-wrap: anywhere;
}

.dwell-ring {
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: calc(var(--btn-border-radius) - 2px);
  background: conic-gradient(var(--dwell-colour) 0%, transparent 0%);
  opacity: 0.22;
  pointer-events: none;
}

.dwell-btn.is-dwelling .dwell-ring {
  opacity: 0.34;
}

.dwell-btn.dwell-complete .dwell-ring {
  background: conic-gradient(var(--dwell-complete-colour) 100%, transparent 0%);
  opacity: 0.42;
}

@media (prefers-reduced-motion: reduce) {
  .dwell-btn { transition: none; }
  .dwell-btn:hover,
  .dwell-btn.is-dwelling { transform: none; }
}

@media (forced-colors: active) {
  .dwell-btn {
    border: 3px solid ButtonText;
    background: ButtonFace;
    color: ButtonText;
    forced-color-adjust: auto;
  }

  .dwell-btn:hover,
  .dwell-btn:focus-visible,
  .dwell-btn.is-dwelling {
    outline: 4px solid Highlight;
    border-color: Highlight;
  }
}
```

## DwellManager

Use pointer events when available. Keep mouse events as fallback because gaze drives the Windows mouse cursor. Keyboard fallback uses Enter/Space; focus dwell is optional.

```javascript
class DwellManager {
  constructor(options = {}) {
    this.defaultDwellTime = options.dwellTime || 800;
    this.cooldownTime = options.cooldownTime || 450;
    this.onActivate = options.onActivate || null;
    this.audioCues = options.audioCues || false;
    this.dwellOnFocus = options.dwellOnFocus || false;
    this.activeButton = null;
    this.animationTimer = null;
    this.dwellStart = 0;
    this.cooldownActive = false;
    this.boundButtons = new WeakSet();
    this.exitRequired = new WeakSet();
    this.audioContext = null;
  }

  attach(buttons, callback) {
    if (callback) this.onActivate = callback;
    Array.from(buttons).forEach((button) => {
      if (this.boundButtons.has(button)) return;
      this.boundButtons.add(button);

      const enterEvent = window.PointerEvent ? 'pointerenter' : 'mouseenter';
      const leaveEvent = window.PointerEvent ? 'pointerleave' : 'mouseleave';
      button.addEventListener(enterEvent, () => this.handleEnter(button));
      button.addEventListener(leaveEvent, () => this.handleLeave(button));

      if (this.dwellOnFocus) {
        button.addEventListener('focus', () => this.handleEnter(button));
        button.addEventListener('blur', () => this.handleLeave(button));
      }

      button.addEventListener('click', (event) => {
        if (event.detail !== 0) this.activate(button, 'click');
      });

      button.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          this.activate(button, 'keyboard');
        }
      });
    });
  }

  handleEnter(button) {
    if (button.disabled || this.activeButton || this.cooldownActive || this.exitRequired.has(button)) return;
    this.activeButton = button;
    this.dwellStart = performance.now();
    button.classList.add('is-dwelling');
    this.tone(440, 0.025, 0.04);

    const dwellTime = Number.parseInt(button.dataset.dwellTime, 10) || this.defaultDwellTime;
    const animate = (timestamp) => {
      if (this.activeButton !== button) return;
      const progress = Math.min((timestamp - this.dwellStart) / dwellTime, 1);
      this.updateRing(button, progress);
      if (progress >= 1) this.activate(button, 'dwell');
      else this.animationTimer = window.requestAnimationFrame(animate);
    };

    this.animationTimer = window.requestAnimationFrame(animate);
  }

  handleLeave(button) {
    this.exitRequired.delete(button);
    if (this.activeButton === button) this.cancel(button);
  }

  activate(button, method = 'manual') {
    if (button.disabled || this.cooldownActive) return;
    if (this.animationTimer) window.cancelAnimationFrame(this.animationTimer);
    this.animationTimer = null;
    this.activeButton = null;
    this.cooldownActive = true;
    this.exitRequired.add(button);
    button.classList.remove('is-dwelling');
    button.classList.add('dwell-complete');
    this.updateRing(button, 1);
    this.tone(660, 0.035, 0.08);

    window.setTimeout(() => {
      button.classList.remove('dwell-complete');
      this.resetRing(button);
      if (this.onActivate) this.onActivate(button, method);
      window.setTimeout(() => {
        this.cooldownActive = false;
      }, this.cooldownTime);
    }, 180);
  }

  cancel(button) {
    if (this.animationTimer) window.cancelAnimationFrame(this.animationTimer);
    this.animationTimer = null;
    this.activeButton = null;
    this.dwellStart = 0;
    button.classList.remove('is-dwelling', 'dwell-complete');
    this.resetRing(button);
  }

  updateRing(button, progress) {
    const ring = button.querySelector('.dwell-ring');
    if (!ring) return;
    const pct = Math.round(progress * 100);
    ring.style.background = `conic-gradient(var(--dwell-colour) ${pct}%, transparent ${pct}%)`;
  }

  resetRing(button) {
    const ring = button.querySelector('.dwell-ring');
    if (!ring) return;
    ring.style.background = 'conic-gradient(var(--dwell-colour) 0%, transparent 0%)';
  }

  tone(frequency, volume, duration) {
    if (!this.audioCues) return;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return;
      if (!this.audioContext) this.audioContext = new AudioContextClass();
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      osc.connect(gain);
      gain.connect(this.audioContext.destination);
      osc.frequency.value = frequency;
      gain.gain.value = volume;
      osc.start();
      osc.stop(this.audioContext.currentTime + duration);
    } catch (error) {}
  }
}
```

## Speech Helper

```javascript
function speakAU(text) {
  if (!('speechSynthesis' in window) || !text) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-AU';
  utterance.rate = 0.85;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}

function stopSpeech() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
}
```

## Confirmation Modal Pattern

```html
<div class="confirm-modal" id="confirmModal" role="dialog" aria-modal="true" aria-labelledby="confirmTitle" aria-hidden="true">
  <div class="confirm-panel">
    <h2 id="confirmTitle">Choose this answer?</h2>
    <p id="confirmLabel"></p>
    <div class="confirm-actions">
      <button class="dwell-btn confirm-btn" data-confirm="yes" data-dwell-time="600" aria-label="Yes, choose this">
        <span class="btn-content"><span class="btn-symbol">YES</span><span class="btn-label">Yes</span></span>
        <span class="dwell-ring" aria-hidden="true"></span>
      </button>
      <button class="dwell-btn confirm-btn" data-confirm="no" data-dwell-time="600" aria-label="No, go back">
        <span class="btn-content"><span class="btn-symbol">NO</span><span class="btn-label">No</span></span>
        <span class="dwell-ring" aria-hidden="true"></span>
      </button>
    </div>
  </div>
</div>
```

```javascript
const confirmDwell = new DwellManager({ dwellTime: 600 });
let pendingConfirm = null;

confirmDwell.attach(document.querySelectorAll('.confirm-btn'), (button) => {
  closeConfirmation();
  if (button.dataset.confirm === 'yes' && pendingConfirm) pendingConfirm();
  pendingConfirm = null;
});

function showConfirmation(label, onConfirm) {
  pendingConfirm = onConfirm;
  document.getElementById('confirmLabel').textContent = label;
  document.getElementById('confirmModal').classList.add('visible');
  document.getElementById('confirmModal').setAttribute('aria-hidden', 'false');
  speakAU(`Choose ${label}?`);
}

function closeConfirmation() {
  document.getElementById('confirmModal').classList.remove('visible');
  document.getElementById('confirmModal').setAttribute('aria-hidden', 'true');
}
```

## Layout Snippets

```css
.choice-grid.two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--target-gap);
  min-height: 70vh;
}

.choice-grid.four {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: repeat(2, minmax(0, 1fr));
  gap: var(--target-gap);
  min-height: 72vh;
}

.story-page {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 32vw);
  gap: var(--target-gap);
  min-height: 70vh;
  align-items: stretch;
}

.word-bank {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--target-gap);
}

.word-bank .dwell-btn {
  min-height: 120px;
  border-radius: 40px;
}
```

## QA Snippets

Runtime target-size check:

```javascript
document.querySelectorAll('button').forEach((button) => {
  if (button.offsetParent === null) return;
  const rect = button.getBoundingClientRect();
  const ok = rect.width >= 120 && rect.height >= 120;
  console.log(`${ok ? 'OK' : 'CHECK'} ${button.getAttribute('aria-label') || button.textContent.trim()} - ${Math.round(rect.width)}x${Math.round(rect.height)}px`);
});
```

Static check from the skill folder:

```sh
scripts/check_eye_gaze_html.py /path/to/activity.html
```

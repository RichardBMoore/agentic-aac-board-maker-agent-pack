---
name: eyegaze-dwell-html
description: Build accessible, single-file HTML tools for students who use eye gaze and dwell selection on PRC-Saltillo Accent AAC devices (1000/1400) running Windows with Microsoft Edge on the Education Queensland network. Use this skill whenever building ANY student resource that needs to work with eye gaze, dwell activation, AAC devices, or for QCIA/Inclusion students with complex access needs. Also trigger for requests involving dwell buttons, gaze-activated choices, AAC choice boards, accessible quiz tools, story readers, or worksheets for non-verbal students. Apply even if the request just mentions "accessible HTML", "eye gaze", "dwell", "AAC", "QCIA student", or "Accent device".
---

# Eye Gaze & Dwell-Activated HTML Tools
## Reference Guide for Building Student Resources on PRC-Saltillo Accent Devices (EQ Network)

> Build everything as a **single self-contained HTML file** — no external CDN links, no internet required. Eye gaze on the Accent acts as a **mouse cursor**. All interaction is hover/dwell-based.

---

## 1. Device Context

- **OS:** Windows 10 IoT LTSC or Windows 11
- **Browser:** Microsoft Edge (Chromium) — opened via `file:///` from USB or local storage
- **Eye tracker:** NuEye® or Look® module (infrared, clips to screen bottom)
- **Screen:** Accent 1000 = 10.1" · Accent 1400 = 14" · Both 1920×1200px
- **RAM/Storage:** 4GB RAM, 128GB storage
- **Dedicated devices** have no browser — require the **Integrated Feature Pack (IFP)** for web access
- **EQ network:** No CDN, no internet during student use — embed everything inline

**How gaze works:** Eye tracker moves the Windows mouse cursor → your HTML's `:hover`/`mouseenter` states fire → your dwell timer counts down → action triggers. Eye gaze does NOT fire touch events.

---

## 2. Dwell Time Guidelines

| Context | Recommended Time |
|---|---|
| Default classroom tool | **800ms** |
| Student prone to accidental activation | 1000–1500ms |
| Confident/experienced gaze user | 600ms |
| Never go below | 500ms (Midas Touch risk) |
| Never go above | 1500ms (fatigue) |
| Confirmation step (second dwell) | 600ms |

**Midas Touch problem:** Student looks at a button to read it → accidentally activates it. Fix with adequate dwell time + visual progress feedback + generous button spacing.

---

## 3. Target Size & WCAG Standards

| Standard | Size | Notes |
|---|---|---|
| WCAG AA minimum (2.5.8) | 24×24px | Far too small for gaze |
| WCAG AAA (2.5.5) | 44×44px | Still too small |
| **Gaze minimum** | **120×120px** | Absolute floor |
| **Gaze ideal** | **150–200px+** | Full-cell layouts preferred |
| Button gap | 20px minimum | Prevents adjacent activation |
| Text contrast (AAA) | 7:1 | Target for all gaze tools |
| Focus indicator contrast | 3:1 | WCAG 2.4.13 |
| Min font size (buttons) | 1.4rem | ~22px |

**Key WCAG criteria for gaze:**
- `2.5.2` Pointer Cancellation — leaving button MUST cancel dwell
- `2.4.7/2.4.13` Focus Visible — dwell ring IS the focus indicator
- `2.1.1` Keyboard — always include keyboard fallback (Tab + Enter)

---

## 4. CSS Variables (use in every tool)

```css
:root {
  --dwell-colour: #0057b8;
  --dwell-hover-bg: #ddeeff;
  --dwell-complete-colour: #00843d;
  --btn-border-radius: 16px;
}
```

---

## 5. The Dwell Button (Core Component)

```html
<button class="dwell-btn" data-dwell-time="800"
        aria-label="Describe option here" tabindex="0">
  <div class="btn-content">
    <img class="btn-symbol" src="" alt="symbol description" aria-hidden="true">
    <span class="btn-label">Label Text</span>
  </div>
  <div class="dwell-ring" aria-hidden="true"></div>
</button>
```

```css
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
.dwell-btn:hover, .dwell-btn:focus-visible {
  background: var(--dwell-hover-bg);
  border-color: var(--dwell-colour);
  outline: 4px solid var(--dwell-colour);
  transform: scale(1.02);
}
.dwell-btn.is-dwelling { background: var(--dwell-hover-bg); border-color: var(--dwell-colour); }
.dwell-btn.dwell-complete { background: #d4edda; border-color: var(--dwell-complete-colour); }
.btn-content { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; z-index: 1; pointer-events: none; }
.btn-symbol { width: 80px; height: 80px; object-fit: contain; }
.btn-label { font-size: 1.4rem; font-weight: 700; color: #222; line-height: 1.2; }

/* Dwell progress ring — fills clockwise using conic-gradient */
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
.dwell-btn.is-dwelling .dwell-ring { opacity: 0.35; }
.dwell-btn.dwell-complete .dwell-ring {
  background: conic-gradient(var(--dwell-complete-colour) 100%, transparent 0%);
  opacity: 0.4;
}

/* Windows high contrast mode support */
@media (forced-colors: active) {
  .dwell-btn { border: 3px solid ButtonText; background: ButtonFace; color: ButtonText; }
  .dwell-btn:hover, .dwell-btn:focus-visible { outline: 4px solid Highlight; }
}
```

---

## 6. DwellManager Class (paste into every tool)

```javascript
class DwellManager {
  constructor(options = {}) {
    this.defaultDwellTime = options.dwellTime || 800;
    this.tickInterval = 16;
    this.activeButton = null;
    this.animationTimer = null;
    this.dwellStart = null;
    this.onActivate = options.onActivate || null;
    this.cooldownActive = false;
    this.cooldownTime = options.cooldownTime || 400;
    this.audioContext = null;
  }

  attach(buttons, callback) {
    this.onActivate = callback || this.onActivate;
    buttons.forEach(button => {
      button.addEventListener('mouseenter', (e) => this.handleEnter(e.currentTarget));
      button.addEventListener('pointerenter', (e) => this.handleEnter(e.currentTarget));
      button.addEventListener('mouseleave', (e) => this.handleLeave(e.currentTarget));
      button.addEventListener('pointerleave', (e) => this.handleLeave(e.currentTarget));
      button.addEventListener('click', (e) => this.handleClick(e.currentTarget));
      button.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); this.activate(e.currentTarget); }
      });
    });
  }

  handleEnter(button) {
    if (this.activeButton || this.cooldownActive) return;
    this.activeButton = button;
    this.dwellStart = performance.now();
    const dwellTime = parseInt(button.dataset.dwellTime) || this.defaultDwellTime;
    button.classList.add('is-dwelling');
    this._beep(440, 0.05, 0.05);
    const animate = (timestamp) => {
      if (!this.activeButton || this.activeButton !== button) return;
      const progress = Math.min((timestamp - this.dwellStart) / dwellTime, 1.0);
      this.updateRing(button, progress);
      if (progress >= 1.0) { this.activate(button); }
      else { this.animationTimer = requestAnimationFrame(animate); }
    };
    this.animationTimer = requestAnimationFrame(animate);
  }

  handleLeave(button) {
    if (this.activeButton !== button) return;
    this.cancelDwell(button);
  }

  handleClick(button) {
    if (!this.cooldownActive) this.activate(button);
  }

  activate(button) {
    if (this.animationTimer) { cancelAnimationFrame(this.animationTimer); this.animationTimer = null; }
    button.classList.remove('is-dwelling');
    button.classList.add('dwell-complete');
    this._beep(660, 0.15, 0.1);
    this.cooldownActive = true;
    this.activeButton = null;
    setTimeout(() => {
      button.classList.remove('dwell-complete');
      this.resetRing(button);
      if (this.onActivate) this.onActivate(button);
      setTimeout(() => { this.cooldownActive = false; }, this.cooldownTime);
    }, 200);
  }

  cancelDwell(button) {
    if (this.animationTimer) { cancelAnimationFrame(this.animationTimer); this.animationTimer = null; }
    button.classList.remove('is-dwelling', 'dwell-complete');
    this.resetRing(button);
    this.activeButton = null;
    this.dwellStart = null;
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

  setDwellTime(ms) { this.defaultDwellTime = ms; }

  _beep(frequency, volume, duration) {
    try {
      if (!this.audioContext) this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      osc.connect(gain); gain.connect(this.audioContext.destination);
      osc.frequency.value = frequency; gain.gain.value = volume;
      osc.start(); osc.stop(this.audioContext.currentTime + duration);
    } catch(e) {}
  }
}
```

---

## 7. Layout Patterns

### Full-screen HTML boilerplate (use for all gaze tools)
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Activity Title</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { height: 100%; overflow: hidden; font-family: 'Segoe UI', Arial, sans-serif; }
    :root { --dwell-colour: #0057b8; --dwell-hover-bg: #ddeeff; --dwell-complete-colour: #00843d; --btn-border-radius: 16px; }
    /* PASTE DWELL BUTTON CSS HERE */
  </style>
</head>
<body>
  <!-- content -->
  <script>
    /* PASTE DwellManager CLASS HERE */
    const dwell = new DwellManager({ dwellTime: 800 });
    dwell.attach(document.querySelectorAll('.dwell-btn'), (btn) => {
      // Handle activation: btn.dataset.value, btn.dataset.action, etc.
    });
  </script>
</body>
</html>
```

### 2-Choice AAC Board layout
```css
.choice-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  padding: 1.5rem;
  height: 100vh;
}
/* Each .dwell-btn gets width: 100%; height: 100% to fill its cell */
```

### 4-Choice Quiz Grid
```css
.answers-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 1rem;
  height: 80vh;
}
```

### Story Reader layout
```css
.story-page {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  align-items: center;
  height: 75vh;
}
/* Navigation buttons: 120px circles, border-radius: 50% */
```

### Worksheet word bank
```css
.word-bank { display: flex; flex-wrap: wrap; gap: 0.75rem; }
/* Word chips: min-width: 120px, min-height: 70px, border-radius: 40px (pill) */
```

---

## 8. Confirmation Step (Quiz / High-Stakes Actions)

Always add a confirmation modal for quiz answers to prevent accidental wrong answers.

```javascript
// Pattern: dwell selects → show modal → dwell Yes/No → process result
function showConfirmation(label, onConfirm) {
  document.getElementById('confirmLabel').textContent = label;
  document.getElementById('confirmModal').classList.add('visible');
  
  // Re-attach dwell to confirm buttons with shorter time
  const confirmDwell = new DwellManager({ dwellTime: 600 });
  confirmDwell.attach(document.querySelectorAll('.confirm-btn'), (btn) => {
    document.getElementById('confirmModal').classList.remove('visible');
    if (btn.dataset.confirm === 'yes') onConfirm();
  });
}
```

---

## 9. Audio & Speech

```javascript
// Web Speech API — no audio files needed, works on Windows
function speakAU(text) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-AU';
  utterance.rate = 0.85;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

// Audio autoplay unlock — call inside any dwell callback (first user gesture)
let audioUnlocked = false;
function unlockAndPlay(dataUri) {
  if (!audioUnlocked) {
    const ctx = new AudioContext();
    ctx.createBufferSource().start(0);
    audioUnlocked = true;
  }
  const audio = new Audio(dataUri);
  audio.play().catch(() => {}); // silent fail
}
```

**Embedding audio as base64:**
```html
<button class="dwell-btn" data-audio="data:audio/mp3;base64,ABC123...">🔊 Listen</button>
```

---

## 10. Deployment Checklist

### Before giving to a student
- [ ] Opens in Edge from `file:///` with no console errors (F12 → Console)
- [ ] No external requests (F12 → Network tab should show no 404s)
- [ ] Fits screen without scrolling (`height: 100vh`, `overflow: hidden`)
- [ ] Mouse hover → ring fills → activates at correct dwell time
- [ ] Moving mouse away cancels dwell
- [ ] Keyboard Tab + Enter works as fallback
- [ ] All buttons have `aria-label` text
- [ ] All images have `alt` text
- [ ] Text contrast ≥ 4.5:1 (ideally 7:1)
- [ ] All interactive targets ≥ 120×120px
- [ ] File is self-contained (no external font/icon/script links)
- [ ] File name has no spaces: use `activity-name-term3.html`

### Test target sizes in DevTools console
```javascript
document.querySelectorAll('.dwell-btn').forEach(btn => {
  const r = btn.getBoundingClientRect();
  const ok = r.width >= 120 && r.height >= 120;
  console.log(`${ok ? '✅' : '❌'} ${btn.getAttribute('aria-label')} — ${Math.round(r.width)}×${Math.round(r.height)}px`);
});
```

---

## 11. AI Prompt Template

Use this when asking Codex to build a new gaze tool:

> "Build a single-file HTML tool for a QCIA student using eye gaze on a PRC-Saltillo Accent 1000/1400 (Windows, Microsoft Edge, file:// protocol). Eye gaze = mouse cursor — student uses hover/dwell (800ms default) to activate. Requirements: (1) No external dependencies — embed everything; (2) All interactive targets minimum 120×120px; (3) Use the DwellManager class with conic-gradient progress ring; (4) Include ARIA labels and keyboard fallback (Tab + Enter); (5) Web Speech API for audio feedback in Australian English; (6) Australian spelling throughout; (7) WCAG AAA contrast (7:1). The activity is: [DESCRIBE ACTIVITY]."

---

## 12. Colour Reference

```css
/* High-contrast AAA palette */
--text-dark:     #1a1a2e;  /* on white: 15.3:1 */
--interactive:   #0057b8;  /* on white: 4.6:1 AA */
--success:       #00843d;  /* on white: 4.6:1 AA */
--alert:         #c00000;  /* on white: 5.9:1 AA */
--bg-warm:       #f9f7f2;  /* off-white, easier on eyes */
--bg-dark:       #1a1a2e;  /* for headers / question areas */
```

> For detailed code templates (full AAC board, story reader, quiz with confirmation, worksheet word bank), see `../build-aac-student-supports/references/templates.md`.

# Dwell Manager Pattern

Use this when you need the reusable JavaScript dwell controller.

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
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.activate(e.currentTarget);
        }
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
      if (progress >= 1.0) {
        this.activate(button);
      } else {
        this.animationTimer = requestAnimationFrame(animate);
      }
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
    if (this.animationTimer) {
      cancelAnimationFrame(this.animationTimer);
      this.animationTimer = null;
    }

    button.classList.remove('is-dwelling');
    button.classList.add('dwell-complete');
    this._beep(660, 0.15, 0.1);
    this.cooldownActive = true;
    this.activeButton = null;

    setTimeout(() => {
      button.classList.remove('dwell-complete');
      this.resetRing(button);
      if (this.onActivate) this.onActivate(button);
      setTimeout(() => {
        this.cooldownActive = false;
      }, this.cooldownTime);
    }, 200);
  }

  cancelDwell(button) {
    if (this.animationTimer) {
      cancelAnimationFrame(this.animationTimer);
      this.animationTimer = null;
    }
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

  setDwellTime(ms) {
    this.defaultDwellTime = ms;
  }

  _beep(frequency, volume, duration) {
    try {
      if (!this.audioContext) this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      osc.connect(gain);
      gain.connect(this.audioContext.destination);
      osc.frequency.value = frequency;
      gain.gain.value = volume;
      osc.start();
      osc.stop(this.audioContext.currentTime + duration);
    } catch (e) {}
  }
}
```

## Minimal use

```javascript
const dwell = new DwellManager({ dwellTime: 800 });
dwell.attach(document.querySelectorAll('.dwell-btn'), (btn) => {
  // handle activation here
});
```

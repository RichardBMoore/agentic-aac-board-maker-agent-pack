/* Agentic AAC Board shared runtime. Keep this file dependency-free and offline-safe. */
(() => {
  "use strict";

  const documentRoot = document.documentElement;
  const irNode = document.getElementById("aac-board-ir");
  if (!irNode) throw new Error("AAC Board IR payload is missing");
  const ir = JSON.parse(irNode.textContent);
  const state = { activePageId: ir.pages[0]?.id || "", words: [], started: false, speaking: false };
  const setup = document.getElementById("setup-screen");
  const studentLayer = document.getElementById("student-layer");
  const speechLayer = document.getElementById("speech-layer");
  const messageText = document.getElementById("message-text");
  const status = document.getElementById("board-status");
  let speechToken = 0;
  let speechOrigin = null;

  const isRendered = (element) => {
    if (!(element instanceof HTMLElement)) return false;
    if (element.hidden || element.closest("[hidden]")) return false;
    const style = getComputedStyle(element);
    return style.display !== "none" && style.visibility !== "hidden";
  };

  const visibleTargets = () => [...document.querySelectorAll("[data-student-target]")].filter(isRendered);

  const auditVisibleTargets = () => {
    const targets = visibleTargets();
    const phase = state.speaking ? "speech" : state.started ? "board" : "setup";
    const limit = Number(
      phase === "setup" ? ir.access.setupTargetLimit : phase === "speech" ? 1 : ir.access.visibleTargetLimit
    );
    const audit = {
      phase,
      count: targets.length,
      limit,
      ok: targets.length <= limit,
      ids: targets.map((target) => target.id || target.dataset.buttonId || target.dataset.control || "unidentified"),
    };
    documentRoot.dataset.visibleTargetCount = String(audit.count);
    documentRoot.dataset.visibleTargetLimit = String(audit.limit);
    documentRoot.dataset.visibleTargetAudit = audit.ok ? "pass" : "fail";
    if (!audit.ok) console.error("AAC visible-target limit exceeded", audit);
    return audit;
  };

  const announce = (message) => {
    if (status) status.textContent = message;
  };

  const updateMessage = () => {
    if (!messageText) return;
    messageText.textContent = state.words.length ? state.words.join(" ") : messageText.dataset.placeholder;
    messageText.classList.toggle("is-placeholder", state.words.length === 0);
  };

  const setSpeechMode = (enabled) => {
    if (enabled && !state.speaking) speechOrigin = document.activeElement;
    dwell.cancel();
    state.speaking = enabled;
    document.body.classList.toggle("speech-active", enabled);
    if (speechLayer) speechLayer.hidden = !enabled;
    if (studentLayer) studentLayer.inert = enabled;
    if (setup) setup.inert = enabled;
    auditVisibleTargets();
    if (enabled) document.getElementById("stop-speech")?.focus({ preventScroll: true });
    else if (speechOrigin) {
      const destination = isRendered(speechOrigin) ? speechOrigin : visibleTargets()[0];
      destination?.focus({ preventScroll: true });
      speechOrigin = null;
    }
  };

  const stopSpeech = () => {
    speechToken += 1;
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    setSpeechMode(false);
    announce("Speech stopped.");
  };

  const speak = (value) => {
    const phrase = String(value || "").trim();
    if (!phrase) return;
    const selectedMessage = document.getElementById("selected-message");
    if (selectedMessage) selectedMessage.textContent = phrase;
    if (!("speechSynthesis" in window) || typeof SpeechSynthesisUtterance === "undefined") {
      announce(`Speech is unavailable. Message: ${phrase}`);
      return;
    }
    window.speechSynthesis.cancel();
    const token = ++speechToken;
    const utterance = new SpeechSynthesisUtterance(phrase);
    utterance.lang = ir.audience.locale || "en-AU";
    utterance.onstart = () => {
      if (token === speechToken && ir.studentControls.stopSpeechDuringPlayback) setSpeechMode(true);
      announce(`Speaking: ${phrase}`);
    };
    const finish = () => {
      if (token !== speechToken) return;
      setSpeechMode(false);
      announce(`Spoken: ${phrase}`);
    };
    utterance.onend = finish;
    utterance.onerror = () => {
      if (token !== speechToken) return;
      setSpeechMode(false);
      announce("Speech could not be played on this device.");
    };
    window.speechSynthesis.speak(utterance);
  };

  const showPage = (pageId) => {
    const page = ir.pages.find((candidate) => candidate.id === pageId);
    if (!page) {
      announce(`Page ${pageId} is unavailable.`);
      return;
    }
    state.activePageId = pageId;
    document.querySelectorAll("[data-page-id]").forEach((element) => {
      element.hidden = element.dataset.pageId !== pageId;
    });
    announce(`${page.name} page.`);
    auditVisibleTargets();
    document.querySelector(`[data-page-id="${CSS.escape(pageId)}"] [data-student-target]`)?.focus({ preventScroll: true });
  };

  const adjacentPage = (offset) => {
    const index = ir.pages.findIndex((page) => page.id === state.activePageId);
    const page = ir.pages[index + offset];
    if (page) showPage(page.id);
  };

  const runAction = (action, button) => {
    switch (action.type) {
      case "speak-text": speak(action.text || button.dataset.spoken); break;
      case "speak-label": speak(button.dataset.label); break;
      case "add-to-message": state.words.push(action.text || button.dataset.spoken || button.dataset.label); updateMessage(); break;
      case "speak-message": speak(state.words.join(" ")); break;
      case "remove-last-word": state.words.pop(); updateMessage(); announce("Last word removed."); break;
      case "clear-message": state.words = []; updateMessage(); announce("Message cleared."); break;
      case "navigate-page": showPage(action.targetPageId || action.pageId); break;
      case "next-page": adjacentPage(1); break;
      case "previous-page": adjacentPage(-1); break;
      case "log-attempt": document.dispatchEvent(new CustomEvent("aac-attempt", { detail: { buttonId: button.dataset.buttonId } })); break;
      case "mark-correct":
      case "mark-incorrect": document.dispatchEvent(new CustomEvent("aac-evidence", { detail: { type: action.type, buttonId: button.dataset.buttonId } })); break;
      default: console.warn("Unsupported AAC action", action.type);
    }
  };

  const activate = (button) => {
    if (!(button instanceof HTMLElement) || button.disabled || state.speaking) return;
    const actions = JSON.parse(button.dataset.actions || "[]");
    actions.forEach((action) => runAction(action, button));
    button.classList.add("was-activated");
    window.setTimeout(() => button.classList.remove("was-activated"), 240);
  };

  class DwellController {
    constructor(milliseconds) {
      this.milliseconds = milliseconds;
      this.timer = 0;
      this.target = null;
      this.startedAt = 0;
    }
    attach(root = document) {
      root.querySelectorAll("[data-student-target]").forEach((target) => {
        if (target.hasAttribute("data-dwell")) {
          target.addEventListener("pointerenter", () => this.begin(target));
          target.addEventListener("pointerleave", () => this.cancel(target));
          target.addEventListener("pointercancel", () => this.cancel(target));
          target.addEventListener("blur", () => this.cancel(target));
        }
        target.addEventListener("click", (event) => {
          if (target.dataset.dwellActivated === "true") {
            target.dataset.dwellActivated = "false";
            event.preventDefault();
            return;
          }
          this.cancel(target);
          this.dispatch(target);
        });
      });
    }
    begin(target) {
      if (target.disabled || !isRendered(target)) return;
      this.cancel();
      this.target = target;
      this.startedAt = performance.now();
      target.classList.add("is-dwelling");
      target.style.setProperty("--dwell-ms", `${this.milliseconds}ms`);
      this.timer = window.setTimeout(() => {
        target.dataset.dwellActivated = "true";
        this.dispatch(target);
        this.cancel(target);
        window.setTimeout(() => { target.dataset.dwellActivated = "false"; }, 900);
      }, this.milliseconds);
    }
    cancel(target = null) {
      if (target && target !== this.target) return;
      window.clearTimeout(this.timer);
      this.target?.classList.remove("is-dwelling");
      this.timer = 0;
      this.target = null;
    }
    dispatch(target) {
      if (target.matches("[data-button-id]")) activate(target);
      else target.dispatchEvent(new CustomEvent("aac-control", { bubbles: true }));
    }
  }

  const startBoard = () => {
    state.started = true;
    if (setup) setup.hidden = true;
    if (studentLayer) studentLayer.hidden = false;
    showPage(state.activePageId);
  };

  document.addEventListener("aac-control", async (event) => {
    const control = event.target.closest("[data-control]")?.dataset.control;
    if (control === "start") startBoard();
    if (control === "sound-check") speak("Sound check ready");
    if (control === "stop-speech") stopSpeech();
    if (control === "full-screen") {
      try {
        await document.documentElement.requestFullscreen();
        announce("Full screen opened.");
      } catch (_error) {
        announce("Full screen was blocked. The board is still ready to use.");
      }
    }
  });

  const dwell = new DwellController(Number(ir.access.dwellTimeMs || 1200));
  dwell.attach();
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    dwell.cancel();
    if (state.speaking) stopSpeech();
    else announce("Dwell cancelled.");
  });
  updateMessage();
  if (!ir.studentControls.startBoard) startBoard();
  else auditVisibleTargets();

  window.AACBoard = Object.freeze({
    ir,
    state,
    start: startBoard,
    stopSpeech,
    navigate: showPage,
    activate: (buttonId) => activate(document.querySelector(`[data-button-id="${CSS.escape(buttonId)}"]`)),
    countVisibleTargets: () => visibleTargets().length,
    auditVisibleTargets,
  });
})();

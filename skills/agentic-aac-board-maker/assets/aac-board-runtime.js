/* Agentic AAC Board shared runtime. Keep this file dependency-free and offline-safe. */
(() => {
  "use strict";

  const documentRoot = document.documentElement;
  const irNode = document.getElementById("aac-board-ir");
  if (!irNode) throw new Error("AAC Board IR payload is missing");
  const ir = JSON.parse(irNode.textContent);
  const speechSettings = ir.speech || {};
  const logSettings = ir.evidenceLog || { enabled: false };
  const state = {
    activePageId: ir.pages[0]?.id || "",
    words: [],
    spelling: false,
    started: false,
    speaking: false,
    schedule: {},
    voice: { name: "browser default", lang: speechSettings.lang || ir.audience.locale || "en-AU", local: null, pinnedFound: null },
    log: { recording: false, modelling: false, entries: [] },
  };
  const setup = document.getElementById("setup-screen");
  const studentLayer = document.getElementById("student-layer");
  const stopControl = document.getElementById("stop-speech");
  const messageText = document.getElementById("message-text");
  const status = document.getElementById("board-status");
  const teacherPanel = document.getElementById("teacher-panel");
  let speechToken = 0;
  let chosenVoice = null;

  const isRendered = (element) => {
    if (!(element instanceof HTMLElement)) return false;
    if (element.hidden || element.closest("[hidden]")) return false;
    const style = getComputedStyle(element);
    return style.display !== "none" && style.visibility !== "hidden";
  };

  const visibleTargets = () => [...document.querySelectorAll("[data-student-target]")].filter(isRendered);

  // During speech the board stays live and the reserved edge Stop control is the one extra target.
  const auditVisibleTargets = () => {
    const targets = visibleTargets();
    const phase = state.speaking ? "speech" : state.started ? "board" : "setup";
    const boardLimit = Number(ir.access.visibleTargetLimit);
    const limit = phase === "setup" ? Number(ir.access.setupTargetLimit) : phase === "speech" ? boardLimit + 1 : boardLimit;
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

  /* ---------- Message building, spelling and word endings ---------- */

  const updateMessage = () => {
    if (!messageText) return;
    messageText.textContent = state.words.length ? state.words.join(" ") : messageText.dataset.placeholder;
    messageText.classList.toggle("is-placeholder", state.words.length === 0);
  };

  const IRREGULAR = {
    ed: { go: "went", run: "ran", eat: "ate", see: "saw", have: "had", do: "did", make: "made", say: "said", get: "got", come: "came", take: "took", give: "gave", think: "thought", buy: "bought", is: "was", are: "were", find: "found", tell: "told", feel: "felt", write: "wrote", read: "read", swim: "swam", sit: "sat", win: "won", fly: "flew", drink: "drank", sing: "sang", ride: "rode", draw: "drew", leave: "left", lose: "lost", catch: "caught", teach: "taught", bring: "brought", fall: "fell", know: "knew", put: "put", cut: "cut", hit: "hit", hurt: "hurt" },
    s: { person: "people", child: "children", man: "men", woman: "women", mouse: "mice", foot: "feet", tooth: "teeth", sheep: "sheep", fish: "fish", go: "goes", do: "does", have: "has", be: "is" },
  };
  const VOWELS = "aeiou";
  const syllableGroups = (word) => (word.match(/[aeiouy]+/g) || []).length;
  const endsCvc = (word) => {
    if (word.length < 3) return false;
    const [a, b, c] = word.slice(-3);
    return !VOWELS.includes(a) && VOWELS.includes(b) && !VOWELS.includes(c) && !"wxy".includes(c) && syllableGroups(word) === 1;
  };
  const inflect = (word, ending) => {
    const lower = word.toLowerCase();
    if (IRREGULAR[ending]?.[lower]) return IRREGULAR[ending][lower];
    if (ending === "s") {
      if (/(s|x|z|ch|sh)$/.test(lower)) return `${word}es`;
      if (/[^aeiou]y$/.test(lower)) return `${word.slice(0, -1)}ies`;
      return `${word}s`;
    }
    if (ending === "ed") {
      if (lower.endsWith("e")) return `${word}d`;
      if (/[^aeiou]y$/.test(lower)) return `${word.slice(0, -1)}ied`;
      if (endsCvc(lower)) return `${word}${word.slice(-1)}ed`;
      return `${word}ed`;
    }
    if (ending === "ing") {
      if (lower.endsWith("ie")) return `${word.slice(0, -2)}ying`;
      if (lower.endsWith("e") && !lower.endsWith("ee") && lower.length > 2) return `${word.slice(0, -1)}ing`;
      if (endsCvc(lower)) return `${word}${word.slice(-1)}ing`;
      return `${word}ing`;
    }
    if (ending === "er" || ending === "est") {
      if (lower.endsWith("e")) return `${word}${ending.slice(1)}`;
      if (/[^aeiou]y$/.test(lower)) return `${word.slice(0, -1)}i${ending}`;
      if (endsCvc(lower)) return `${word}${word.slice(-1)}${ending}`;
      return `${word}${ending}`;
    }
    return `${word}${ending}`;
  };
  const addWordEnding = (ending) => {
    if (!state.words.length) {
      announce("Choose a word first, then add an ending.");
      return;
    }
    const chunk = state.words[state.words.length - 1];
    const match = chunk.match(/^(.*?)([A-Za-z']+)([^A-Za-z']*)$/);
    if (!match) return;
    const [, before, word, after] = match;
    const changed = inflect(word, ending);
    state.words[state.words.length - 1] = `${before}${changed}${after}`;
    state.spelling = false;
    updateMessage();
    speak(changed);
  };

  /* ---------- Speech output: installed voices first ---------- */

  const langStarts = (voice, prefix) => String(voice.lang || "").toLowerCase().replace("_", "-").startsWith(prefix);
  const pickVoice = () => {
    const synth = window.speechSynthesis;
    if (!synth || typeof synth.getVoices !== "function") return;
    const voices = synth.getVoices() || [];
    if (!voices.length) return;
    const wanted = String(speechSettings.voiceName || "").trim().toLowerCase();
    const lang = String(speechSettings.lang || ir.audience.locale || "en-AU").toLowerCase();
    const pinned = wanted ? voices.find((voice) => voice.name.toLowerCase() === wanted) || voices.find((voice) => voice.name.toLowerCase().includes(wanted)) : null;
    const installed = voices.filter((voice) => voice.localService !== false);
    const preferLocal = speechSettings.preferLocal !== false;
    const pool = preferLocal && installed.length ? installed : voices;
    chosenVoice =
      pinned ||
      pool.find((voice) => langStarts(voice, lang)) ||
      pool.find((voice) => langStarts(voice, "en-au")) ||
      pool.find((voice) => langStarts(voice, "en-gb")) ||
      pool.find((voice) => langStarts(voice, "en")) ||
      null;
    state.voice = {
      name: chosenVoice ? chosenVoice.name : "browser default",
      lang: chosenVoice ? chosenVoice.lang : lang,
      local: chosenVoice ? chosenVoice.localService !== false : null,
      pinnedFound: wanted ? Boolean(pinned) : null,
    };
    renderVoiceStatus();
  };
  const voiceSummary = () => {
    const where = state.voice.local === true ? "installed on this device" : state.voice.local === false ? "online voice: needs internet" : "browser default";
    const pinnedNote = state.voice.pinnedFound === false ? ` The chosen voice "${speechSettings.voiceName}" is not on this device.` : "";
    if (state.voice.local === null) return `Voice: browser default (no installed voice list yet; use Sound check).${pinnedNote}`;
    return `Voice: ${state.voice.name} (${where}).${pinnedNote}`;
  };
  const renderVoiceStatus = () => {
    const node = document.getElementById("voice-status");
    if (node) node.textContent = voiceSummary();
    documentRoot.dataset.voiceLocal = String(state.voice.local);
  };

  const setSpeechMode = (enabled) => {
    state.speaking = enabled;
    document.body.classList.toggle("speech-active", enabled);
    if (!enabled) dwell.cancel(stopControl);
    auditVisibleTargets();
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
    // A new message interrupts the previous one; the board never locks while speaking.
    window.speechSynthesis.cancel();
    if (!chosenVoice) pickVoice();
    const token = ++speechToken;
    const utterance = new SpeechSynthesisUtterance(phrase);
    utterance.lang = chosenVoice ? chosenVoice.lang : speechSettings.lang || ir.audience.locale || "en-AU";
    if (chosenVoice) utterance.voice = chosenVoice;
    if (speechSettings.rate) utterance.rate = Number(speechSettings.rate);
    if (speechSettings.pitch) utterance.pitch = Number(speechSettings.pitch);
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

  /* ---------- Visual schedule: now / next / done ---------- */

  const schedulePages = ir.pages.filter((page) => page.schedule && Array.isArray(page.schedule.steps) && page.schedule.steps.length);
  const renderSchedule = (pageId) => {
    const page = ir.pages.find((candidate) => candidate.id === pageId);
    if (!page?.schedule) return;
    const current = state.schedule[pageId] || 0;
    page.schedule.steps.forEach((buttonId, index) => {
      const button = document.querySelector(`[data-button-id="${CSS.escape(buttonId)}"]`);
      if (!button) return;
      const badge = button.querySelector(".schedule-badge");
      const status = index < current ? "done" : index === current ? "now" : index === current + 1 ? "next" : "";
      button.classList.toggle("is-done", status === "done");
      button.classList.toggle("is-now", status === "now");
      button.classList.toggle("is-next", status === "next");
      if (badge) badge.textContent = status === "done" ? "Done ✓" : status === "now" ? "Now ▶" : status === "next" ? "Next" : "";
      const label = button.dataset.label;
      button.setAttribute("aria-label", status ? `${label}, ${status === "done" ? "done" : status}` : label);
    });
    const node = document.getElementById("schedule-status");
    if (node) {
      const steps = page.schedule.steps.length;
      node.textContent = current >= steps ? "\u2014 all steps done" : `\u2014 step ${current + 1} of ${steps}`;
    }
  };
  const scheduleStep = (direction) => {
    const page = schedulePages.find((candidate) => candidate.id === state.activePageId) || schedulePages[0];
    if (!page) return;
    const steps = page.schedule.steps.length;
    const current = state.schedule[page.id] || 0;
    state.schedule[page.id] = Math.max(0, Math.min(steps, current + direction));
    renderSchedule(page.id);
    announce(direction > 0 ? "Step marked done." : "Last done step restored.");
  };

  /* ---------- Opt-in, on-device evidence log ---------- */

  const logEnabled = Boolean(logSettings.enabled);
  const updateLogView = () => {
    const indicator = document.getElementById("modelling-indicator");
    if (indicator) indicator.hidden = !state.log.modelling;
    const recording = document.getElementById("recording-indicator");
    if (recording) recording.hidden = !state.log.recording;
    const summary = document.getElementById("log-summary");
    if (!summary) return;
    const studentEntries = state.log.entries.filter((entry) => entry.source === "student");
    const counts = {};
    studentEntries.forEach((entry) => { counts[entry.function] = (counts[entry.function] || 0) + 1; });
    const distinct = new Set(studentEntries.map((entry) => entry.label.toLowerCase())).size;
    const models = state.log.entries.length - studentEntries.length;
    const rows = Object.keys(counts).sort().map((name) => `<tr><th scope="row">${name}</th><td>${counts[name]}</td></tr>`).join("");
    summary.innerHTML =
      `<p>${state.log.recording ? "Recording" : "Not recording"}. Student selections: ${studentEntries.length}. ` +
      `Different messages used: ${distinct}. Partner models: ${models}.</p>` +
      (rows ? `<table><caption>Student selections by communication function</caption><tbody>${rows}</tbody></table>` : "");
  };
  const recordSelection = (button, method) => {
    if (!logEnabled || !state.log.recording) return;
    state.log.entries.push({
      time: new Date().toISOString(),
      page: state.activePageId,
      buttonId: button.dataset.buttonId,
      label: button.dataset.label,
      message: button.dataset.spoken,
      function: button.dataset.function || "",
      role: button.dataset.role || "",
      wordClass: button.dataset.wordClass || "",
      source: state.log.modelling ? "partner-model" : "student",
      method,
    });
    updateLogView();
  };
  const csvCell = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  const exportLog = () => {
    const columns = ["time", "page", "buttonId", "label", "message", "function", "role", "wordClass", "source", "method"];
    const lines = [columns.join(",")].concat(state.log.entries.map((entry) => columns.map((column) => csvCell(entry[column])).join(",")));
    const blob = new Blob([`${lines.join("\r\n")}\r\n`], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${ir.id}-selections-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    announce("Selection log downloaded.");
  };
  const setModelling = (enabled) => {
    state.log.modelling = enabled;
    const toggle = document.querySelector('[data-teacher-control="log-model"]');
    if (toggle) toggle.setAttribute("aria-pressed", String(enabled));
    updateLogView();
    announce(enabled ? "Partner modelling is on: selections are logged as models." : "Partner modelling is off.");
  };

  /* ---------- Pages and actions ---------- */

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
    renderSchedule(pageId);
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
      case "add-to-message":
        state.words.push(action.text || button.dataset.spoken || button.dataset.label);
        state.spelling = false;
        updateMessage();
        break;
      case "add-letter": {
        const letters = String(action.text || button.dataset.label || "").toLowerCase();
        if (state.spelling && state.words.length) state.words[state.words.length - 1] += letters;
        else state.words.push(letters);
        state.spelling = true;
        updateMessage();
        break;
      }
      case "add-space": state.spelling = false; announce("Space."); break;
      case "delete-letter": {
        if (!state.words.length) break;
        const last = state.words[state.words.length - 1].slice(0, -1);
        if (last) state.words[state.words.length - 1] = last;
        else { state.words.pop(); state.spelling = false; }
        updateMessage();
        announce("Letter deleted.");
        break;
      }
      case "add-word-ending": addWordEnding(String(action.text || "")); break;
      case "speak-message": speak(state.words.join(" ")); break;
      case "remove-last-word": state.words.pop(); state.spelling = false; updateMessage(); announce("Last word removed."); break;
      case "clear-message": state.words = []; state.spelling = false; updateMessage(); announce("Message cleared."); break;
      case "navigate-page": showPage(action.targetPageId || action.pageId); break;
      case "next-page": adjacentPage(1); break;
      case "previous-page": adjacentPage(-1); break;
      case "schedule-done": scheduleStep(1); break;
      case "log-attempt": document.dispatchEvent(new CustomEvent("aac-attempt", { detail: { buttonId: button.dataset.buttonId } })); break;
      case "mark-correct":
      case "mark-incorrect": document.dispatchEvent(new CustomEvent("aac-evidence", { detail: { type: action.type, buttonId: button.dataset.buttonId } })); break;
      default: console.warn("Unsupported AAC action", action.type);
    }
  };

  const activate = (button, method = "pointer") => {
    if (!(button instanceof HTMLElement) || button.disabled) return;
    const actions = JSON.parse(button.dataset.actions || "[]");
    recordSelection(button, method);
    actions.forEach((action) => runAction(action, button));
    button.classList.add("was-activated");
    window.setTimeout(() => button.classList.remove("was-activated"), 240);
  };

  /* ---------- Dwell: cancel on leave, re-arm only after the pointer leaves ---------- */

  class DwellController {
    constructor(milliseconds) {
      this.milliseconds = milliseconds;
      this.timer = 0;
      this.target = null;
      this.awaitingExit = false;
    }
    attach(root = document) {
      root.querySelectorAll("[data-student-target]").forEach((target) => {
        if (target.hasAttribute("data-dwell")) {
          target.addEventListener("pointerenter", () => this.begin(target));
          target.addEventListener("pointerleave", () => {
            // A target hidden by navigation does not count as the pointer leaving.
            if (isRendered(target)) this.awaitingExit = false;
            this.cancel(target);
          });
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
          this.dispatch(target, event.detail === 0 ? "keyboard" : "pointer");
        });
      });
      document.addEventListener("pointermove", (event) => {
        const over = event.target instanceof Element ? event.target.closest("[data-dwell]") : null;
        if (!over || !isRendered(over)) this.awaitingExit = false;
      }, { passive: true });
    }
    begin(target) {
      if (this.awaitingExit || target.disabled || !isRendered(target)) return;
      this.cancel();
      this.target = target;
      target.classList.add("is-dwelling");
      target.style.setProperty("--dwell-ms", `${this.milliseconds}ms`);
      this.timer = window.setTimeout(() => {
        target.dataset.dwellActivated = "true";
        this.cancel(target);
        this.dispatch(target, "dwell");
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
    requireExit() {
      // After any selection, nothing dwells again until the pointer leaves the spot it is resting on.
      this.cancel();
      this.awaitingExit = true;
    }
    dispatch(target, method) {
      this.requireExit();
      if (target.matches("[data-button-id]")) activate(target, method);
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
    if (control === "sound-check") {
      pickVoice();
      speak("Sound check. This is my voice.");
      announce(voiceSummary());
    }
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

  /* ---------- Teacher panel (never a student target) ---------- */

  const setTeacherMode = (enabled) => {
    document.body.classList.toggle("teacher-mode", enabled);
    if (teacherPanel) teacherPanel.setAttribute("aria-hidden", String(!enabled));
    if (enabled) teacherPanel?.querySelector("h2")?.focus({ preventScroll: true });
  };
  document.querySelectorAll("[data-teacher-control]").forEach((control) => {
    control.addEventListener("click", () => {
      const name = control.dataset.teacherControl;
      if (name === "panel-close") setTeacherMode(false);
      if (name === "log-start" && logEnabled) { state.log.recording = !state.log.recording; control.setAttribute("aria-pressed", String(state.log.recording)); updateLogView(); }
      if (name === "log-model" && logEnabled) setModelling(!state.log.modelling);
      if (name === "log-export" && logEnabled) exportLog();
      if (name === "log-clear" && logEnabled) { state.log.entries = []; updateLogView(); announce("Selection log cleared."); }
      if (name === "schedule-done") scheduleStep(1);
      if (name === "schedule-undo") scheduleStep(-1);
    });
  });
  let titleTaps = [];
  document.querySelectorAll(".page-title, .setup-title").forEach((title) => {
    title.addEventListener("click", () => {
      const now = performance.now();
      titleTaps = titleTaps.filter((time) => now - time < 1500).concat(now);
      if (titleTaps.length >= 3) { titleTaps = []; setTeacherMode(!document.body.classList.contains("teacher-mode")); }
    });
  });

  const dwell = new DwellController(Number(ir.access.dwellTimeMs || 1200));
  dwell.attach();
  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "t") { event.preventDefault(); setTeacherMode(!document.body.classList.contains("teacher-mode")); return; }
    if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "m" && logEnabled) { event.preventDefault(); setModelling(!state.log.modelling); return; }
    if (event.key !== "Escape") return;
    dwell.cancel();
    if (state.speaking) stopSpeech();
    else announce("Dwell cancelled.");
  });
  if ("speechSynthesis" in window && window.speechSynthesis && typeof window.speechSynthesis.addEventListener === "function") {
    window.speechSynthesis.addEventListener("voiceschanged", pickVoice);
  }
  pickVoice();
  renderVoiceStatus();
  updateMessage();
  updateLogView();
  if (new URLSearchParams(location.search).get("teacher") === "1") setTeacherMode(true);
  if (!ir.studentControls.startBoard) startBoard();
  else auditVisibleTargets();

  window.AACBoard = Object.freeze({
    ir,
    state,
    start: startBoard,
    stopSpeech,
    navigate: showPage,
    activate: (buttonId) => activate(document.querySelector(`[data-button-id="${CSS.escape(buttonId)}"]`), "script"),
    countVisibleTargets: () => visibleTargets().length,
    auditVisibleTargets,
    inflect,
    voice: () => ({ ...state.voice }),
    log: () => state.log.entries.map((entry) => ({ ...entry })),
  });
})();

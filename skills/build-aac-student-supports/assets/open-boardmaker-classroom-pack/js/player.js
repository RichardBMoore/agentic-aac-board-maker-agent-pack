(function (global) {
  "use strict";

  var Data = global.BoardmakerData;
  var Symbols = global.BoardmakerSymbols;
  var FileIO = global.BoardmakerFileIO;
  var Tts = global.BoardmakerTts;
  var Actions = global.BoardmakerActions;
  var Access = global.BoardmakerAccess;
  var BOARD_SIZE_KEY = "open-boardmaker.boardSize";
  var CONTRAST_MODE_KEY = "open-boardmaker.contrastMode";

  var state = {
    activity: Data.loadCurrentActivity(),
    pageIndex: 0,
    dwellEnabled: true,
    ttsEnabled: true,
    switchEnabled: false,
    student: Data.getActiveStudent(),
    classroomMode: false,
    locked: false,
    boardSize: normaliseBoardSize(localStorage.getItem(BOARD_SIZE_KEY)),
    contrastMode: normaliseContrastMode(localStorage.getItem(CONTRAST_MODE_KEY)),
    wakeLock: null,
    symbolFallbackShown: false,
    scanner: null
  };

  var els = {};

  function page() {
    return state.activity.pages[state.pageIndex] || state.activity.pages[0];
  }

  function buttonById(id) {
    return (page().buttons || []).find(function (button) {
      return button.id === id;
    });
  }

  function fallbackText(label) {
    return String(label || "?").trim().slice(0, 1).toUpperCase() || "?";
  }

  function fallbackSymbolHtml(label) {
    return '<span class="symbol-fallback" aria-hidden="true">' + escapeHtml(fallbackText(label)) + "</span>";
  }

  function normaliseBoardSize(value) {
    return ["standard", "large", "compact"].indexOf(value) >= 0 ? value : "standard";
  }

  function normaliseContrastMode(value) {
    return ["standard", "high", "black-white", "yellow-black"].indexOf(value) >= 0 ? value : "standard";
  }

  function symbolateHtml(button) {
    var segments = Array.isArray(button.symbolateSegments) ? button.symbolateSegments : [];
    if (!segments.length) {
      segments = String(button.label || "")
        .split(/\s+/)
        .filter(Boolean)
        .map(function (word) {
          return { text: word, symbolSrc: "" };
        });
    }
    return '<span class="symbolate-grid">' + segments.map(function (segment) {
      var image = segment.symbolSrc ? '<img src="' + escapeHtml(segment.symbolSrc) + '" alt="" data-symbol-id="' + escapeHtml(segment.symbolId || "") + '">' : fallbackSymbolHtml(segment.text);
      return '<span class="symbolate-token">' + image + '<strong>' + escapeHtml(segment.text || "") + "</strong></span>";
    }).join("") + "</span>";
  }

  function buttonHtml(button) {
    var layout = button.symbolLayout || "label-bottom";
    var style = button.style || {};
    var font = button.font || {};
    var img = "";
    if (button.type === "symbolate" || layout === "symbolate") {
      return '<button class="activity-button layout-label-only symbolate-button" data-button-id="' + escapeHtml(button.id) + '" data-fallback-label="' + escapeHtml(button.label || "") + '" type="button" aria-label="' + escapeHtml(button.label || "Symbolate button") + '" style="' +
        "background:" + (style.fillColour || "#ffffff") + ";" +
        "border-color:" + (style.borderColour || "#17212b") + ";" +
        "border-width:" + Number(style.borderWidth || 4) + "px;" +
        "color:" + (font.colour || "#000000") + ";" +
        "font-family:" + (font.family || "Verdana") + ", Arial, sans-serif;" +
        '">' + symbolateHtml(button) + "</button>";
    }
    if (layout !== "label-only" && button.symbolSrc) {
      img = '<img src="' + escapeHtml(button.symbolSrc) + '" alt="" data-symbol-image data-symbol-id="' + escapeHtml(button.symbolId || "") + '">';
    } else {
      img = fallbackSymbolHtml(button.label);
    }
    var label = state.activity.settings.showLabels === false || layout === "symbol-only" ? "" : '<span class="button-label">' + escapeHtml(button.label || "") + "</span>";
    return '<button class="activity-button layout-' + layout + '" data-button-id="' + escapeHtml(button.id) + '" data-fallback-label="' + escapeHtml(button.label || "") + '" type="button" aria-label="' + escapeHtml(button.label || "Activity button") + '" style="' +
      "background:" + (style.fillColour || "#ffffff") + ";" +
      "border-color:" + (style.borderColour || "#17212b") + ";" +
      "border-width:" + Number(style.borderWidth || 4) + "px;" +
      "color:" + (font.colour || "#000000") + ";" +
      "font-family:" + (font.family || "Verdana") + ", Arial, sans-serif;" +
      '">' +
      '<span class="button-symbol">' + img + "</span>" +
      label +
      "</button>";
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function cssEscape(value) {
    if (global.CSS && global.CSS.escape) return global.CSS.escape(value);
    return String(value).replace(/'/g, "\\'");
  }

  function setActivityTitle(name) {
    var safe = String(name || "").trim() || "Activity";
    els.title.textContent = safe;
    document.title = safe + " - Open AAC Studio Player";
  }

  function setRangeText(slider, output, unit) {
    var value = slider.value;
    output.textContent = value + " " + unit;
    slider.setAttribute("aria-valuetext", value + " " + (unit === "ms" ? "milliseconds" : unit));
  }

  function render() {
    var currentPage = page();
    setActivityTitle(state.activity.name);
    els.pageTitle.textContent = currentPage.name;
    els.pageCount.textContent = "Page " + (state.pageIndex + 1) + " of " + state.activity.pages.length;
    els.status.textContent = state.activity.settings.speakLabels === false ? "Speech off for this activity" : "Ready";
    els.dwellTime.value = state.activity.settings.dwellTimeMs || 1200;
    setRangeText(els.dwellTime, els.dwellOutput, "ms");
    els.tts.checked = state.ttsEnabled;
    els.enableDwell.checked = state.dwellEnabled;
    els.enableSwitch.checked = state.switchEnabled;
    els.scanSpeed.value = state.activity.settings.scanSpeedMs || 1400;
    setRangeText(els.scanSpeed, els.scanSpeedOutput, "ms");
    els.scanPattern.value = state.activity.settings.scanPattern || "linear";
    els.toggleScan.textContent = state.scanner && state.scanner.isActive() ? "Stop Scan" : "Start Scan";
    els.toggleLock.textContent = state.locked ? "Unlock" : "Lock";
    els.startClassroom.textContent = state.classroomMode && !document.fullscreenElement ? "Go Full Screen" : "Start Classroom";
    els.boardSize.value = state.boardSize;
    els.contrastMode.value = state.contrastMode;
    updateModeClasses();
    updateDensityClasses(currentPage);
    els.board.style.setProperty("--rows", currentPage.gridRows || 2);
    els.board.style.setProperty("--cols", currentPage.gridColumns || 2);
    els.board.innerHTML = (currentPage.buttons || []).map(buttonHtml).join("");
    hydrateBoardSymbols();
    updateOfflineBanner();
    if (state.scanner) state.scanner.refresh();
    renderStudentControls();
    updateLog();
  }

  function renderStudentControls() {
    var profiles = Data.listStudentProfiles();
    var activeId = state.student && !state.student.anonymous ? state.student.id : "anonymous";
    els.studentSelect.innerHTML = ['<option value="anonymous">Anonymous session</option>'].concat(profiles.map(function (student) {
      return '<option value="' + student.id + '">' + escapeHtml(student.name) + "</option>";
    })).join("");
    els.studentSelect.value = activeId;
    if (state.student && !state.student.anonymous) {
      els.studentName.value = state.student.name;
    }
  }

  function setMessage(text) {
    els.message.textContent = text || "";
  }

  function setOfflineBanner(kind, detail) {
    if (!els.offlineBanner) return;
    els.offlineBanner.classList.remove("is-ready", "needs-work", "is-checking", "is-offline");
    els.offlineBanner.classList.add(kind);
    var text = els.offlineBanner.querySelector("span");
    if (text) text.textContent = detail;
  }

  function appCacheReady() {
    if (!("serviceWorker" in navigator)) return Promise.resolve(false);
    if (navigator.serviceWorker.controller) return Promise.resolve(true);
    return navigator.serviceWorker.getRegistration("sw.js").then(function (registration) {
      return Boolean(registration);
    }).catch(function () {
      return false;
    });
  }

  function updateOfflineBanner() {
    if (!Symbols || !Symbols.countActivityCached) {
      setOfflineBanner("needs-work", "Symbol cache unavailable");
      return;
    }
    setOfflineBanner("is-checking", "Checking app and symbol cache");
    Symbols.countActivityCached(state.activity).then(function (result) {
      return appCacheReady().then(function (appReady) {
        var online = navigator.onLine !== false;
        var symbolText = result.total ? result.cached + "/" + result.total + " symbols cached" : "no online symbols needed";
        if (!online && (!appReady || result.missing > 0)) {
          setOfflineBanner("is-offline", "Offline now: " + symbolText);
          return;
        }
        if (appReady && result.missing === 0) {
          setOfflineBanner("is-ready", "Works offline: app cached, " + symbolText);
          return;
        }
        var appText = appReady ? "app cached" : "refresh once to cache app";
        setOfflineBanner("needs-work", appText + ", " + symbolText);
      });
    });
  }

  function updateDensityClasses(currentPage) {
    var rows = Number((currentPage && currentPage.gridRows) || 1);
    var columns = Number((currentPage && currentPage.gridColumns) || 1);
    var buttons = currentPage && Array.isArray(currentPage.buttons) ? currentPage.buttons.length : 0;
    var count = Math.max(buttons, rows * columns);
    var density = count <= 4 ? "few" : count <= 9 ? "medium" : count <= 16 ? "many" : "dense";
    document.body.classList.remove("board-density-few", "board-density-medium", "board-density-many", "board-density-dense");
    document.body.classList.add("board-density-" + density);
  }

  function updateModeClasses() {
    document.body.classList.toggle("classroom-mode", state.classroomMode);
    document.body.classList.toggle("is-locked", state.locked);
    document.body.classList.remove("board-size-standard", "board-size-large", "board-size-compact");
    document.body.classList.add("board-size-" + state.boardSize);
    document.body.classList.remove("contrast-standard", "contrast-high", "contrast-black-white", "contrast-yellow-black");
    document.body.classList.add("contrast-" + state.contrastMode);
    if (els.startClassroom) {
      els.startClassroom.textContent = state.classroomMode && !document.fullscreenElement ? "Go Full Screen" : "Start Classroom";
      els.startClassroom.setAttribute("aria-pressed", String(state.classroomMode));
    }
    if (els.toggleLock) {
      els.toggleLock.textContent = state.locked ? "Unlock" : "Lock";
      els.toggleLock.setAttribute("aria-pressed", String(state.locked));
    }
  }

  function setBoardSize(value) {
    state.boardSize = normaliseBoardSize(value);
    localStorage.setItem(BOARD_SIZE_KEY, state.boardSize);
    updateModeClasses();
  }

  function setContrastMode(value) {
    state.contrastMode = normaliseContrastMode(value);
    localStorage.setItem(CONTRAST_MODE_KEY, state.contrastMode);
    if (state.student && !state.student.anonymous) {
      state.student.settings.contrastMode = state.contrastMode;
      Data.saveStudentProfile(state.student);
    }
    updateModeClasses();
  }

  function requestFullScreen() {
    if (!document.documentElement.requestFullscreen || document.fullscreenElement) return Promise.resolve();
    return document.documentElement.requestFullscreen().then(function () {
      setMessage("Full screen is on. Press Escape to leave.");
      updateModeClasses();
    }).catch(function () {
      setMessage("Full screen was blocked. Use Start Classroom, press F11, or ask EQ IT to enable automatic full screen or kiosk mode.");
    });
  }

  function requestWakeLock(silent) {
    if (!navigator.wakeLock || state.wakeLock) return Promise.resolve();
    return navigator.wakeLock.request("screen").then(function (lock) {
      state.wakeLock = lock;
      lock.addEventListener("release", function () {
        if (state.wakeLock === lock) state.wakeLock = null;
      });
    }).catch(function () {
      if (!silent) setMessage("Screen wake lock unavailable. Check laptop power settings.");
    });
  }

  function releaseWakeLock() {
    var lock = state.wakeLock;
    state.wakeLock = null;
    if (lock && lock.release) lock.release().catch(function () {});
  }

  function enterClassroom(requestScreen) {
    state.classroomMode = true;
    if (els.teacherControls) els.teacherControls.open = false;
    updateModeClasses();
    setMessage(requestScreen ? "Starting classroom mode" : "Classroom layout ready");
    if (requestScreen) {
      requestFullScreen();
      // Wake lock is helpful but optional. Keep it silent here so a rejection
      // cannot overwrite the more important fullscreen/F11/EQ policy guidance.
      requestWakeLock(true);
    }
  }

  function exitClassroom() {
    state.classroomMode = false;
    state.locked = false;
    if (state.scanner) state.scanner.stop();
    releaseWakeLock();
    if (els.teacherControls) els.teacherControls.open = true;
    updateModeClasses();
    if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen();
    setMessage("Classroom mode off");
  }

  function toggleClassroom() {
    if (!state.classroomMode) {
      enterClassroom(true);
      return;
    }
    requestFullScreen();
  }

  function toggleLock() {
    state.locked = !state.locked;
    updateModeClasses();
    setMessage(state.locked ? "Locked for classroom use" : "Unlocked");
  }

  function lockedMessage() {
    if (!state.locked) return false;
    setMessage("Unlock classroom mode to use that control.");
    return true;
  }

  function handleSymbolImageError(event) {
    var image = event.target;
    if (!image || !image.tagName || image.tagName.toLowerCase() !== "img") return;
    var holder = image.closest(".button-symbol");
    var button = image.closest("[data-button-id]");
    var symbolId = image.getAttribute("data-symbol-id");
    if (Symbols && Symbols.getCachedSymbol && symbolId) {
      Symbols.getCachedSymbol(symbolId).then(function (cached) {
        if (cached && cached.dataUrl && holder) {
          holder.innerHTML = '<img src="' + escapeHtml(cached.dataUrl) + '" alt="" data-symbol-image data-symbol-id="' + escapeHtml(symbolId) + '">';
          return;
        }
        if (holder) holder.innerHTML = fallbackSymbolHtml(button ? button.dataset.fallbackLabel : "");
      });
      return;
    }
    if (holder) holder.innerHTML = fallbackSymbolHtml(button ? button.dataset.fallbackLabel : "");
    if (!state.symbolFallbackShown) {
      state.symbolFallbackShown = true;
      setMessage("A symbol image could not load, so text fallback is showing.");
    }
  }

  function updateConnectivity(event) {
    if (!navigator.onLine) {
      setMessage("Offline. Saved boards and cached symbols are still available.");
      return;
    }
    if (event) setMessage("Online");
  }

  function hydrateBoardSymbols() {
    if (Symbols && Symbols.hydrateImages) Symbols.hydrateImages(els.board);
  }

  function goToPage(pageId) {
    var index = state.activity.pages.findIndex(function (candidate) {
      return candidate.id === pageId;
    });
    if (index >= 0) {
      state.pageIndex = index;
      render();
    }
  }

  function previousPage() {
    state.pageIndex = Math.max(0, state.pageIndex - 1);
    render();
  }

  function nextPage() {
    state.pageIndex = Math.min(state.activity.pages.length - 1, state.pageIndex + 1);
    render();
  }

  function flashButton(buttonId, result) {
    var element = els.board.querySelector("[data-button-id='" + cssEscape(buttonId) + "']");
    if (!element) return;
    var className = "feedback-" + (result || "selected");
    element.classList.remove("feedback-selected", "feedback-correct", "feedback-incorrect");
    void element.offsetWidth;
    element.classList.add(className);
    setTimeout(function () {
      element.classList.remove(className);
    }, 700);
  }

  function animateButton(buttonId, animation) {
    var element = els.board.querySelector("[data-button-id='" + cssEscape(buttonId) + "']");
    if (!element) return;
    var className = "animation-" + (animation || "pulse");
    element.classList.remove("animation-pulse", "animation-pop", "animation-shake");
    void element.offsetWidth;
    element.classList.add(className);
    setTimeout(function () {
      element.classList.remove(className);
    }, 900);
  }

  function openUrl(url) {
    var safeUrl = String(url || "").trim();
    if (!safeUrl) return;
    if (!/^https?:\/\//i.test(safeUrl) && safeUrl.indexOf("mailto:") !== 0) {
      setMessage("Only http, https, or mail links can open.");
      return;
    }
    global.open(safeUrl, "_blank", "noopener,noreferrer");
  }

  function playAudio(src) {
    var url = String(src || "").trim();
    if (!url) return;
    try {
      var audio = new Audio(url);
      audio.play().catch(function () {
        setMessage("Audio could not play.");
      });
    } catch (error) {
      setMessage("Audio could not play.");
    }
  }

  function activate(buttonId, method) {
    var currentPage = page();
    var button = buttonById(buttonId);
    if (!button || button.state === "disabled" || button.state === "hidden") return;
    Actions.runActions(button, {
      activity: state.activity,
      page: currentPage,
      method: method,
      goToPage: goToPage,
      nextPage: nextPage,
      previousPage: previousPage,
      flashButton: flashButton,
      animateButton: animateButton,
      openUrl: openUrl,
      playAudio: playAudio,
      saveActivity: function () {
        state.activity = Data.saveCurrentActivity(state.activity);
      },
      setMessage: setMessage,
      logAttempt: function (clickedButton, result) {
        Data.addSessionAttempt(state.activity, currentPage, clickedButton, method, result, state.student);
        updateLog();
      }
    });
  }

  function updateLog() {
    var rows = sessionRows();
    var correct = rows.filter(function (row) { return row.result === "correct"; }).length;
    var incorrect = rows.filter(function (row) { return row.result === "incorrect"; }).length;
    els.attemptCount.textContent = String(rows.length);
    els.correctCount.textContent = String(correct);
    els.incorrectCount.textContent = String(incorrect);
    renderSessionSummary(rows, correct, incorrect);
    els.recentLog.innerHTML = rows.slice(-8).reverse().map(function (row) {
      var time = new Date(row.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      return '<div class="log-entry"><strong>' + escapeHtml(row.label) + '</strong><span>' + time + " | " + escapeHtml(row.method) + " | " + escapeHtml(row.result) + "</span></div>";
    }).join("");
  }

  function studentLabel() {
    return state.student && !state.student.anonymous ? state.student.name : "Anonymous";
  }

  function renderSessionSummary(rows, correct, incorrect) {
    var scored = correct + incorrect;
    var accuracy = scored ? Math.round((correct / scored) * 100) + "%" : "Not scored";
    var attempts = rows.length + " attempt" + (rows.length === 1 ? "" : "s");
    var accuracyText = scored ? accuracy + " accuracy" : accuracy;
    els.sessionSummary.innerHTML = '<strong>' + escapeHtml(studentLabel()) + '</strong>' +
      ' <span>' + attempts + " | " + accuracyText + "</span>";
  }

  function sessionRows() {
    return Data.getSessionLog().filter(function (row) {
      var activityMatch = state.activity.id && row.activityId ? row.activityId === state.activity.id : row.activityName === state.activity.name;
      if (!activityMatch) return false;
      if (state.student && !state.student.anonymous) return row.studentId === state.student.id;
      return !row.studentId;
    });
  }

  function finishSession() {
    if (state.scanner) state.scanner.stop();
    Tts.stop();
    var rows = sessionRows();
    var correct = rows.filter(function (row) { return row.result === "correct"; }).length;
    var incorrect = rows.filter(function (row) { return row.result === "incorrect"; }).length;
    var summary = "Session complete: " + rows.length + " attempt" + (rows.length === 1 ? "" : "s");
    if (correct || incorrect) summary += ", " + correct + " correct, " + incorrect + " incorrect";
    setMessage(summary);
    els.status.textContent = "Session complete";
  }

  function sessionReportText() {
    var rows = sessionRows();
    var correct = rows.filter(function (row) { return row.result === "correct"; }).length;
    var incorrect = rows.filter(function (row) { return row.result === "incorrect"; }).length;
    var scored = correct + incorrect;
    var accuracy = scored ? Math.round((correct / scored) * 100) + "%" : "Not scored";
    var lines = [
      "Open AAC Studio Session Report",
      "",
      "Activity: " + state.activity.name,
      "Student: " + studentLabel(),
      "Generated: " + new Date().toLocaleString(),
      "Attempts: " + rows.length,
      "Correct: " + correct,
      "Incorrect: " + incorrect,
      "Accuracy: " + accuracy,
      "",
      "Attempts"
    ];
    if (!rows.length) {
      lines.push("No attempts recorded.");
    }
    rows.forEach(function (row) {
      lines.push([
        new Date(row.timestamp).toLocaleString(),
        row.pageName || "Page",
        row.label || "",
        row.method || "",
        row.result || ""
      ].join(" | "));
    });
    return lines.join("\n");
  }

  function exportReport() {
    if (!confirmPrivacyExport("session report")) return;
    var filename = Data.filenameFromName(state.activity.name + "-" + studentLabel() + "-session-report", "txt");
    FileIO.downloadText(sessionReportText(), filename, "text/plain");
  }

  function confirmPrivacyExport(kind) {
    var rows = sessionRows();
    var hasProfileData = rows.some(function (row) {
      return row.studentName || row.studentId;
    }) || (state.student && !state.student.anonymous);
    var detail = hasProfileData ? " It may include local profile names or student-specific session rows." : " It includes anonymous session rows.";
    if (global.confirm && !global.confirm("Export " + kind + " from this device?" + detail + " Check privacy before sharing.")) {
      return false;
    }
    return true;
  }

  function toggleFullScreen() {
    if (!document.fullscreenElement) {
      requestFullScreen();
      return;
    }
    if (document.exitFullscreen) document.exitFullscreen();
  }

  function currentAccessSettings() {
    return {
      dwellTimeMs: Number(els.dwellTime.value || 1200),
      ttsEnabled: Boolean(els.tts.checked),
      switchScanning: Boolean(els.enableSwitch.checked),
      scanSpeedMs: Number(els.scanSpeed.value || 1400),
      scanPattern: els.scanPattern.value || "linear",
      contrastMode: state.contrastMode
    };
  }

  function applyStudentSettings(student) {
    state.student = Data.setActiveStudent(student && student.id ? student.id : "anonymous");
    state.activity.settings.dwellTimeMs = state.student.settings.dwellTimeMs || 1200;
    state.activity.settings.switchScanning = Boolean(state.student.settings.switchScanning);
    state.activity.settings.scanSpeedMs = state.student.settings.scanSpeedMs || 1400;
    state.activity.settings.scanPattern = state.student.settings.scanPattern || "linear";
    state.ttsEnabled = state.student.settings.ttsEnabled !== false;
    state.switchEnabled = Boolean(state.student.settings.switchScanning);
    state.contrastMode = normaliseContrastMode(state.student.settings.contrastMode || localStorage.getItem(CONTRAST_MODE_KEY));
    localStorage.setItem(CONTRAST_MODE_KEY, state.contrastMode);
    Tts.setEnabled(state.ttsEnabled);
    Data.saveCurrentActivity(state.activity);
    setMessage("");
    render();
  }

  function saveStudent() {
    var name = els.studentName.value.trim();
    if (!name) {
      setMessage("Type a profile name first, or use anonymous mode.");
      return;
    }
    state.student = Data.saveStudentProfile({
      id: state.student && !state.student.anonymous ? state.student.id : null,
      name: name,
      settings: currentAccessSettings()
    });
    setMessage("Student profile saved");
    render();
  }

  function useAnonymousStudent() {
    applyStudentSettings(Data.anonymousStudent());
    els.studentName.value = "";
    setMessage("Anonymous session");
  }

  function deleteStudent() {
    if (!state.student || state.student.anonymous) {
      setMessage("No student profile selected");
      return;
    }
    var name = state.student.name;
    if (!global.confirm || global.confirm("Delete local profile for " + name + "?")) {
      Data.deleteStudentProfile(state.student.id);
      state.student = Data.setActiveStudent("anonymous");
      els.studentName.value = "";
      setMessage("Student profile deleted");
      render();
    }
  }

  function clearStudentData() {
    if (global.confirm && !global.confirm("Clear all local student profiles and session logs on this device?")) return;
    Data.clearStudentData();
    state.student = Data.anonymousStudent();
    setMessage("Student profiles and session logs cleared");
    render();
  }

  function bind() {
    var controller = Access.createController({
      isDwellEnabled: function () { return state.dwellEnabled; },
      getDwellTime: function () { return Number(els.dwellTime.value || 1200); },
      onActivate: activate,
      shouldHandleKeyboard: function () {
        return !state.switchEnabled;
      }
    });
    controller.bind(els.board);
    state.scanner = Access.createScanner({
      isEnabled: function () { return state.switchEnabled; },
      getSpeed: function () { return Number(els.scanSpeed.value || 1400); },
      getPattern: function () { return els.scanPattern.value || "linear"; },
      getColumns: function () { return page().gridColumns || 1; },
      onActivate: activate,
      onCue: function (buttonId) {
        var button = buttonById(buttonId);
        if (button && state.activity.accessibility.audioCues !== false && state.ttsEnabled) {
          Tts.speak(button.audioCue || button.label || "", { interrupt: true, rate: 1 });
        }
      },
      onStateChange: function (active) {
        els.toggleScan.textContent = active ? "Stop Scan" : "Start Scan";
        els.status.textContent = active ? "Switch scanning" : "Ready";
      }
    });
    state.scanner.bind(els.board);

    els.board.addEventListener("error", handleSymbolImageError, true);
    els.previous.addEventListener("click", function () {
      if (!lockedMessage()) previousPage();
    });
    els.next.addEventListener("click", function () {
      if (!lockedMessage()) nextPage();
    });
    els.stopSpeech.addEventListener("click", Tts.stop);
    els.startClassroom.addEventListener("click", toggleClassroom);
    els.exitClassroom.addEventListener("click", exitClassroom);
    els.toggleLock.addEventListener("click", toggleLock);
    els.fullScreen.addEventListener("click", toggleFullScreen);
    els.finishSession.addEventListener("click", finishSession);
    els.editorLink.addEventListener("click", function (event) {
      if (!state.locked) return;
      event.preventDefault();
      lockedMessage();
    });
    els.studentSelect.addEventListener("change", function () {
      applyStudentSettings(Data.loadStudentProfile(els.studentSelect.value));
    });
    els.saveStudent.addEventListener("click", saveStudent);
    els.anonymousStudent.addEventListener("click", useAnonymousStudent);
    els.deleteStudent.addEventListener("click", deleteStudent);
    els.clearStudentData.addEventListener("click", clearStudentData);
    els.enableDwell.addEventListener("change", function () {
      state.dwellEnabled = els.enableDwell.checked;
      controller.cancelDwell();
    });
    els.tts.addEventListener("change", function () {
      state.ttsEnabled = els.tts.checked;
      Tts.setEnabled(state.ttsEnabled);
    });
    els.enableSwitch.addEventListener("change", function () {
      state.switchEnabled = els.enableSwitch.checked;
      state.activity.settings.switchScanning = state.switchEnabled;
      Data.saveCurrentActivity(state.activity);
      if (!state.switchEnabled && state.scanner) state.scanner.stop();
      render();
    });
    els.dwellTime.addEventListener("input", function () {
      state.activity.settings.dwellTimeMs = Number(els.dwellTime.value);
      setRangeText(els.dwellTime, els.dwellOutput, "ms");
      Data.saveCurrentActivity(state.activity);
    });
    els.scanSpeed.addEventListener("input", function () {
      state.activity.settings.scanSpeedMs = Number(els.scanSpeed.value);
      setRangeText(els.scanSpeed, els.scanSpeedOutput, "ms");
      Data.saveCurrentActivity(state.activity);
      if (state.scanner) state.scanner.refresh();
    });
    els.scanPattern.addEventListener("change", function () {
      state.activity.settings.scanPattern = els.scanPattern.value;
      Data.saveCurrentActivity(state.activity);
      if (state.scanner) state.scanner.reset();
      render();
    });
    els.boardSize.addEventListener("change", function () {
      setBoardSize(els.boardSize.value);
    });
    els.contrastMode.addEventListener("change", function () {
      setContrastMode(els.contrastMode.value);
    });
    els.toggleScan.addEventListener("click", function () {
      if (!state.switchEnabled) {
        state.switchEnabled = true;
        state.activity.settings.switchScanning = true;
        Data.saveCurrentActivity(state.activity);
        els.enableSwitch.checked = true;
      }
      state.scanner.toggle();
      render();
    });
    els.stepScan.addEventListener("click", function () {
      if (!state.switchEnabled) {
        state.switchEnabled = true;
        state.activity.settings.switchScanning = true;
        Data.saveCurrentActivity(state.activity);
        els.enableSwitch.checked = true;
      }
      state.scanner.step();
    });
    els.selectScan.addEventListener("click", function () {
      state.scanner.select("switch");
    });
    els.exportCsv.addEventListener("click", function () {
      if (!confirmPrivacyExport("CSV log")) return;
      FileIO.downloadCsv(sessionRows(), state.activity.name);
    });
    els.exportReport.addEventListener("click", exportReport);
    els.clearLog.addEventListener("click", function () {
      if (lockedMessage()) return;
      if (global.confirm && !global.confirm("Clear the local log for this activity?")) return;
      Data.clearSessionLogForActivity(state.activity);
      updateLog();
      setMessage("");
    });
    FileIO.bindJsonInput(els.loadActivity, function (json) {
      if (lockedMessage()) return;
      state.activity = Data.saveCurrentActivity(json);
      state.switchEnabled = Boolean(state.activity.settings.switchScanning);
      state.pageIndex = 0;
      if (window.BoardmakerActions && window.BoardmakerActions.resetMessage) {
        window.BoardmakerActions.resetMessage();
      }
      render();
      setMessage("");
    }, function () {
      els.status.textContent = "Could not load JSON";
    });

    global.addEventListener("online", updateConnectivity);
    global.addEventListener("offline", updateConnectivity);
    global.addEventListener("online", updateOfflineBanner);
    global.addEventListener("offline", updateOfflineBanner);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "visible" && state.classroomMode) requestWakeLock(true);
    });
  }

  function registerServiceWorker() {
    if (!("serviceWorker" in navigator)) return;
    if (location.protocol !== "http:" && location.protocol !== "https:") return;
    navigator.serviceWorker.register("sw.js").catch(function (error) {
      console.warn("Service worker registration failed", error);
    });
  }

  function init() {
    if (window.BoardmakerActions && window.BoardmakerActions.resetMessage) {
      window.BoardmakerActions.resetMessage();
    }
    els = {
      title: document.getElementById("activity-title"),
      status: document.getElementById("player-status"),
      editorLink: document.getElementById("editor-link"),
      pageTitle: document.getElementById("page-title"),
      pageCount: document.getElementById("page-count"),
      offlineBanner: document.getElementById("offline-banner"),
      board: document.getElementById("player-board"),
      message: document.getElementById("message-bar"),
      previous: document.getElementById("previous-page"),
      next: document.getElementById("next-page"),
      stopSpeech: document.getElementById("stop-speech"),
      startClassroom: document.getElementById("start-classroom"),
      teacherControls: document.getElementById("teacher-controls"),
      exitClassroom: document.getElementById("exit-classroom"),
      toggleLock: document.getElementById("toggle-lock"),
      fullScreen: document.getElementById("full-screen"),
      finishSession: document.getElementById("finish-session"),
      exportCsv: document.getElementById("export-csv"),
      exportReport: document.getElementById("export-report"),
      clearLog: document.getElementById("clear-log"),
      loadActivity: document.getElementById("load-activity"),
      studentSelect: document.getElementById("student-select"),
      studentName: document.getElementById("student-name"),
      saveStudent: document.getElementById("save-student"),
      anonymousStudent: document.getElementById("anonymous-student"),
      deleteStudent: document.getElementById("delete-student"),
      clearStudentData: document.getElementById("clear-student-data"),
      enableDwell: document.getElementById("enable-dwell"),
      dwellTime: document.getElementById("player-dwell-time"),
      dwellOutput: document.getElementById("player-dwell-output"),
      tts: document.getElementById("enable-tts"),
      enableSwitch: document.getElementById("enable-switch"),
      scanSpeed: document.getElementById("scan-speed"),
      scanSpeedOutput: document.getElementById("scan-speed-output"),
      scanPattern: document.getElementById("scan-pattern"),
      boardSize: document.getElementById("board-size"),
      contrastMode: document.getElementById("contrast-mode"),
      toggleScan: document.getElementById("toggle-scan"),
      stepScan: document.getElementById("step-scan"),
      selectScan: document.getElementById("select-scan"),
      attemptCount: document.getElementById("attempt-count"),
      correctCount: document.getElementById("correct-count"),
      incorrectCount: document.getElementById("incorrect-count"),
      sessionSummary: document.getElementById("session-summary"),
      recentLog: document.getElementById("recent-log")
    };
    state.activity = Data.saveCurrentActivity(state.activity);
    state.switchEnabled = Boolean(state.activity.settings.switchScanning);
    state.student = Data.getActiveStudent();
    Tts.setEnabled(true);
    updateModeClasses();
    bind();
    render();
    document.addEventListener("fullscreenchange", updateModeClasses);
    if (new URLSearchParams(location.search).get("classroom") === "1") {
      // Managed Edge 132+ can allow this startup request through
      // AutomaticFullscreenAllowedForUrls. Otherwise the classroom layout
      // remains usable and Start Classroom/F11 provides the fallback.
      enterClassroom(true);
    }
    updateConnectivity();
    updateOfflineBanner();
    registerServiceWorker();
  }

  document.addEventListener("DOMContentLoaded", init);
})(window);

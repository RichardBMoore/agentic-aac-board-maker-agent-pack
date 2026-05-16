(function (global) {
  "use strict";

  var Data = global.BoardmakerData;
  var FileIO = global.BoardmakerFileIO;
  var Symbols = global.BoardmakerSymbols;

  var HISTORY_LIMIT = 40;
  var QUICK_PRESETS = {
    choice: {
      name: "Choice Board",
      labels: ["Yes", "No", "More", "Finished", "Help", "Stop"]
    },
    core: {
      name: "Core Words",
      labels: ["I want", "More", "Finished", "Help", "Yes", "No", "My turn", "Your turn"]
    },
    needs: {
      name: "Needs Board",
      labels: ["Toilet", "Drink", "Hungry", "Pain", "Break", "Help", "Finished"]
    },
    feelings: {
      name: "Feelings Board",
      labels: ["Happy", "Sad", "Angry", "Scared", "Tired", "Sick", "Calm", "Excited"]
    },
    schedule: {
      name: "Visual Schedule",
      labels: ["Arrival", "Work", "Break", "Lunch", "Outside", "Pack up", "Home"]
    }
  };

  var SEARCH_ALIASES = {
    "i want": "want",
    "i don't know": "question",
    "my turn": "turn",
    "your turn": "turn",
    "pack up": "backpack",
    arrival: "school",
    finished: "finish",
    hungry: "eat",
    toilet: "bathroom",
    outside: "playground",
    calm: "relax"
  };

  var WORD_PREDICTIONS = {
    i: ["want", "need", "like", "see", "feel", "am"],
    want: ["more", "drink", "toilet", "help", "break", "finished"],
    need: ["help", "break", "toilet", "drink", "food", "quiet"],
    more: ["please", "water", "food", "time", "music"],
    feel: ["happy", "sad", "angry", "tired", "sick", "scared"],
    go: ["outside", "home", "toilet", "class", "playground"],
    first: ["work", "reading", "maths", "writing"],
    then: ["break", "lunch", "outside", "home"],
    finished: ["all done", "next", "break", "help"]
  };

  var COMMON_WORDS = [
    "yes", "no", "more", "finished", "help", "stop", "go", "wait",
    "toilet", "drink", "eat", "break", "happy", "sad", "angry", "tired",
    "sick", "scared", "my turn", "your turn", "please", "thank you"
  ];

  var state = {
    activity: Data.loadCurrentActivity(),
    pageIndex: 0,
    selectedButtonId: null,
    undoStack: [],
    redoStack: [],
    pendingSnapshot: null,
    arasaacStatus: {
      ok: null,
      message: "Checking ARASAAC"
    },
    offlineStatus: {
      ok: null,
      message: "Not prepared"
    },
    offlineStatusTimer: null,
    symbolFallbackShown: false
  };

  var els = {};

  function page() {
    return state.activity.pages[state.pageIndex] || state.activity.pages[0];
  }

  function selectedButton() {
    var currentPage = page();
    return (currentPage.buttons || []).find(function (button) {
      return button.id === state.selectedButtonId;
    }) || (currentPage.buttons || [])[0] || null;
  }

  function snapshot() {
    return {
      activity: Data.clone(state.activity),
      pageIndex: state.pageIndex,
      selectedButtonId: state.selectedButtonId
    };
  }

  function snapshotsMatch(before, after) {
    if (!before || !after) return false;
    return before.pageIndex === after.pageIndex &&
      before.selectedButtonId === after.selectedButtonId &&
      JSON.stringify(before.activity) === JSON.stringify(after.activity);
  }

  function updateHistoryButtons() {
    if (!els.undoChange || !els.redoChange) return;
    els.undoChange.disabled = !state.undoStack.length;
    els.redoChange.disabled = !state.redoStack.length;
  }

  function pushSnapshot(item) {
    if (!item) return;
    var previous = state.undoStack[state.undoStack.length - 1];
    if (snapshotsMatch(previous, item)) return;
    state.undoStack.push(item);
    if (state.undoStack.length > HISTORY_LIMIT) state.undoStack.shift();
    state.redoStack = [];
    updateHistoryButtons();
  }

  function pushHistory() {
    pushSnapshot(snapshot());
  }

  function beginEditSnapshot() {
    if (!state.pendingSnapshot) state.pendingSnapshot = snapshot();
  }

  function commitEditSnapshot() {
    if (!state.pendingSnapshot) return;
    if (snapshotsMatch(state.pendingSnapshot, snapshot())) {
      state.pendingSnapshot = null;
      return;
    }
    pushSnapshot(state.pendingSnapshot);
    state.pendingSnapshot = null;
  }

  function restoreSnapshot(item, message) {
    if (!item) return;
    state.activity = Data.saveCurrentActivity(item.activity);
    state.pageIndex = Math.min(item.pageIndex || 0, state.activity.pages.length - 1);
    state.selectedButtonId = item.selectedButtonId;
    setStatus(message);
    render();
  }

  function undoChange() {
    commitEditSnapshot();
    var item = state.undoStack.pop();
    if (!item) return;
    state.redoStack.push(snapshot());
    restoreSnapshot(item, "Undone");
  }

  function redoChange() {
    var item = state.redoStack.pop();
    if (!item) return;
    state.undoStack.push(snapshot());
    restoreSnapshot(item, "Redone");
  }

  function setStatus(text) {
    els.status.textContent = text;
  }

  function setEditorTitle(name) {
    var safe = String(name || "").trim() || "Activity";
    document.title = safe + " - Open Boardmaker Editor";
  }

  function setRangeText(slider, output) {
    output.textContent = slider.value + " ms";
    slider.setAttribute("aria-valuetext", slider.value + " milliseconds");
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function fallbackText(label) {
    return String(label || "?").trim().slice(0, 1).toUpperCase() || "?";
  }

  function fallbackSymbolHtml(label) {
    return '<span class="symbol-fallback" aria-hidden="true">' + escapeHtml(fallbackText(label)) + "</span>";
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

  function normaliseColour(value) {
    return String(value || "").trim().toLowerCase();
  }

  function setRadioGroup(group, value) {
    var normalised = normaliseColour(value);
    Array.prototype.forEach.call(group || [], function (input) {
      input.checked = normaliseColour(input.value) === normalised;
    });
  }

  function radioGroupValue(group, fallback) {
    var checked = Array.prototype.find.call(group || [], function (input) {
      return input.checked;
    });
    return checked ? checked.value : fallback;
  }

  function forEachControl(control, callback) {
    if (!control) return;
    if (control.addEventListener) {
      callback(control);
      return;
    }
    Array.prototype.forEach.call(control, callback);
  }

  function renderButton(button) {
    var layout = button.symbolLayout || "label-bottom";
    var style = button.style || {};
    var font = button.font || {};
    var symbol = "";
    if (button.type === "symbolate" || layout === "symbolate") {
      return '<button class="board-button layout-label-only symbolate-button' + (button.id === state.selectedButtonId ? " is-selected" : "") + '" data-button-id="' + escapeHtml(button.id) + '" data-fallback-label="' + escapeHtml(button.label || "") + '" type="button" aria-label="' + escapeHtml(button.label || "Symbolate button") + '" style="' +
        "background:" + (style.fillColour || "#ffffff") + ";" +
        "border-color:" + (style.borderColour || "#17212b") + ";" +
        "border-width:" + Number(style.borderWidth || 3) + "px;" +
        "color:" + (font.colour || "#000000") + ";" +
        "font-family:" + (font.family || "Verdana") + ", Arial, sans-serif;" +
        '">' + symbolateHtml(button) + "</button>";
    }
    if (layout !== "label-only" && button.symbolSrc) {
      symbol = '<img src="' + escapeHtml(button.symbolSrc) + '" alt="" data-symbol-image data-symbol-id="' + escapeHtml(button.symbolId || "") + '">';
    } else {
      symbol = fallbackSymbolHtml(button.label);
    }
    var label = state.activity.settings.showLabels === false || layout === "symbol-only" ? "" : '<span class="button-label">' + escapeHtml(button.label || "") + "</span>";
    return '<button class="board-button layout-' + layout + (button.id === state.selectedButtonId ? " is-selected" : "") + '" data-button-id="' + escapeHtml(button.id) + '" data-fallback-label="' + escapeHtml(button.label || "") + '" type="button" aria-label="' + escapeHtml(button.label || "Board button") + '" style="' +
      "background:" + (style.fillColour || "#ffffff") + ";" +
      "border-color:" + (style.borderColour || "#17212b") + ";" +
      "border-width:" + Number(style.borderWidth || 3) + "px;" +
      "color:" + (font.colour || "#000000") + ";" +
      "font-family:" + (font.family || "Verdana") + ", Arial, sans-serif;" +
      '">' +
      '<span class="button-symbol">' + symbol + "</span>" +
      label +
      "</button>";
  }

  function renderPages() {
    els.pageList.innerHTML = state.activity.pages.map(function (item, index) {
      return '<div class="page-item' + (index === state.pageIndex ? " is-active" : "") + '" role="listitem">' +
        '<strong>' + escapeHtml(item.name || "Page " + (index + 1)) + "</strong>" +
        '<button type="button" data-page-index="' + index + '">Open</button>' +
        "</div>";
    }).join("");
  }

  function renderButtonTable() {
    var currentPage = page();
    els.buttonTable.innerHTML = (currentPage.buttons || []).map(function (button, index) {
      return '<div class="button-row-item">' +
        '<div><strong>' + escapeHtml(button.label || "Button " + (index + 1)) + '</strong><span class="status-line">' + escapeHtml(button.result || "selected") + "</span></div>" +
        '<button type="button" data-select-button="' + button.id + '">Edit</button>' +
        "</div>";
    }).join("");
  }

  function readinessItems() {
    var pages = state.activity.pages || [];
    var buttons = pages.reduce(function (items, item) {
      return items.concat(item.buttons || []);
    }, []);
    var missingLabels = buttons.filter(function (button) {
      return !String(button.label || "").trim();
    }).length;
    var missingSymbols = buttons.filter(function (button) {
      if (button.type === "symbolate" || button.symbolLayout === "symbolate") {
        return !Array.isArray(button.symbolateSegments) || button.symbolateSegments.some(function (segment) {
          return !segment.symbolSrc;
        });
      }
      return button.symbolLayout !== "label-only" && !button.symbolSrc;
    }).length;
    var quizButtons = buttons.filter(function (button) {
      return button.result === "correct" || button.result === "incorrect";
    });
    var correctButtons = buttons.filter(function (button) {
      return button.result === "correct";
    });
    return [
      {
        ok: Boolean(String(state.activity.name || "").trim()),
        label: "Named activity",
        detail: state.activity.name || "Add a clear title"
      },
      {
        ok: buttons.length > 0,
        label: "Buttons ready",
        detail: buttons.length + " button" + (buttons.length === 1 ? "" : "s")
      },
      {
        ok: missingLabels === 0,
        label: "Labels complete",
        detail: missingLabels ? missingLabels + " missing" : "All buttons named"
      },
      {
        ok: missingSymbols === 0,
        label: "Symbols complete",
        detail: missingSymbols ? missingSymbols + " need symbols" : "All visible symbols set"
      },
      {
        ok: !quizButtons.length || correctButtons.length > 0,
        label: "Quiz scoring",
        detail: quizButtons.length ? correctButtons.length + " correct answer" + (correctButtons.length === 1 ? "" : "s") : "No quiz scoring"
      },
      {
        ok: buttons.length <= 16,
        label: "Classroom density",
        detail: buttons.length <= 16 ? "Easy to scan" : "Consider splitting pages"
      },
      {
        ok: state.arasaacStatus.ok === true,
        label: "Symbol network",
        detail: state.arasaacStatus.message
      },
      {
        ok: state.offlineStatus.ok === true,
        label: "Offline symbols",
        detail: state.offlineStatus.message
      }
    ];
  }

  function renderReadiness() {
    if (!els.readinessList) return;
    els.readinessList.innerHTML = readinessItems().map(function (item) {
      return '<div class="readiness-item ' + (item.ok ? "is-ready" : "needs-work") + '">' +
        '<span aria-hidden="true">' + (item.ok ? "OK" : "Check") + "</span>" +
        '<div><strong>' + escapeHtml(item.label) + '</strong><small>' + escapeHtml(item.detail) + "</small></div>" +
        "</div>";
    }).join("");
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

  function updateOfflineBannerFromCounts(result) {
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
  }

  function buttonActionValue(button) {
    var actions = button && Array.isArray(button.actions) ? button.actions : [];
    if (actions.some(function (action) { return action.type === "next-page"; })) return "next-page";
    if (actions.some(function (action) { return action.type === "previous-page"; })) return "previous-page";
    return "stay";
  }

  function actionsForValue(value) {
    var actions = [Data.makeAction("speak-label"), Data.makeAction("log-attempt")];
    if (value === "next-page") actions.push(Data.makeAction("next-page"));
    if (value === "previous-page") actions.push(Data.makeAction("previous-page"));
    return actions;
  }

  function firstAction(button, types) {
    var actions = button && Array.isArray(button.actions) ? button.actions : [];
    return actions.find(function (action) {
      return types.indexOf(action.type) >= 0;
    }) || null;
  }

  function actionValue(action) {
    if (!action) return "";
    return action.text || action.url || action.src || "";
  }

  function setAdvancedActionFields(button) {
    var animation = firstAction(button, ["animate"]);
    var media = firstAction(button, ["speak-text", "open-url", "play-audio"]);
    var variable = firstAction(button, ["set-variable", "increment-variable"]);
    var conditional = firstAction(button, ["conditional"]);
    els.buttonAnimation.value = animation ? animation.animation || "pulse" : "";
    els.buttonMediaAction.value = media ? media.type : "";
    els.buttonMediaValue.value = actionValue(media);
    els.variableName.value = variable ? variable.name || "" : "";
    els.variableOperation.value = variable ? (variable.type === "increment-variable" ? "increment" : "set") : "";
    els.variableValue.value = variable ? String(variable.value == null ? "" : variable.value) : "";
    els.conditionVariable.value = conditional ? conditional.variable || "" : "";
    els.conditionOperator.value = conditional ? conditional.operator || "equals" : "";
    els.conditionValue.value = conditional ? String(conditional.value == null ? "" : conditional.value) : "";
    els.conditionTrueAction.value = conditional ? conditional.ifTrue || "stay" : "stay";
    els.conditionFalseAction.value = conditional ? conditional.ifFalse || "stay" : "stay";
  }

  function selectedActions() {
    var actions = actionsForValue(els.buttonAction.value);
    if (els.buttonAnimation.value) {
      actions.push(Data.makeAction("animate", { animation: els.buttonAnimation.value }));
    }
    if (els.buttonMediaAction.value && els.buttonMediaValue.value.trim()) {
      var value = els.buttonMediaValue.value.trim();
      if (els.buttonMediaAction.value === "speak-text") actions.push(Data.makeAction("speak-text", { text: value }));
      if (els.buttonMediaAction.value === "open-url") actions.push(Data.makeAction("open-url", { url: value }));
      if (els.buttonMediaAction.value === "play-audio") actions.push(Data.makeAction("play-audio", { src: value }));
    }
    if (els.variableOperation.value && els.variableName.value.trim()) {
      var variableAction = els.variableOperation.value === "increment" ? "increment-variable" : "set-variable";
      actions.push(Data.makeAction(variableAction, {
        name: els.variableName.value.trim(),
        value: els.variableValue.value.trim() || (variableAction === "increment-variable" ? "1" : "")
      }));
    }
    if (els.conditionOperator.value && els.conditionVariable.value.trim()) {
      actions.push(Data.makeAction("conditional", {
        variable: els.conditionVariable.value.trim(),
        operator: els.conditionOperator.value,
        value: els.conditionValue.value.trim(),
        ifTrue: els.conditionTrueAction.value,
        ifFalse: els.conditionFalseAction.value
      }));
    }
    return actions;
  }

  function setActionPresetFields(preset) {
    if (!preset) {
      setStatus("Choose a preset first");
      return;
    }
    pushHistory();
    if (preset === "correct-answer") {
      els.buttonResult.value = "correct";
      els.buttonAction.value = "stay";
      els.buttonAnimation.value = "pop";
      els.buttonMediaAction.value = "speak-text";
      els.buttonMediaValue.value = "Correct";
      els.variableName.value = "";
      els.variableOperation.value = "";
      els.variableValue.value = "";
      els.conditionOperator.value = "";
    }
    if (preset === "wrong-answer") {
      els.buttonResult.value = "incorrect";
      els.buttonAction.value = "stay";
      els.buttonAnimation.value = "shake";
      els.buttonMediaAction.value = "speak-text";
      els.buttonMediaValue.value = "Try again";
      els.variableName.value = "";
      els.variableOperation.value = "";
      els.variableValue.value = "";
      els.conditionOperator.value = "";
    }
    if (preset === "go-next") {
      els.buttonResult.value = "selected";
      els.buttonAction.value = "next-page";
      els.buttonAnimation.value = "pulse";
      els.buttonMediaAction.value = "";
      els.buttonMediaValue.value = "";
      els.variableName.value = "";
      els.variableOperation.value = "";
      els.variableValue.value = "";
      els.conditionOperator.value = "";
    }
    if (preset === "add-score") {
      els.buttonResult.value = "correct";
      els.buttonAction.value = "stay";
      els.buttonAnimation.value = "pop";
      els.buttonMediaAction.value = "";
      els.buttonMediaValue.value = "";
      els.variableName.value = "score";
      els.variableOperation.value = "increment";
      els.variableValue.value = "1";
      els.conditionOperator.value = "";
    }
    if (preset === "score-finish") {
      els.buttonResult.value = "correct";
      els.buttonAction.value = "stay";
      els.buttonAnimation.value = "pop";
      els.buttonMediaAction.value = "";
      els.buttonMediaValue.value = "";
      els.variableName.value = "score";
      els.variableOperation.value = "increment";
      els.variableValue.value = "1";
      els.conditionVariable.value = "score";
      els.conditionOperator.value = "greater-than";
      els.conditionValue.value = "2";
      els.conditionTrueAction.value = "next-page";
      els.conditionFalseAction.value = "stay";
    }
    if (preset === "speak-then-next") {
      els.buttonResult.value = "selected";
      els.buttonAction.value = "next-page";
      els.buttonAnimation.value = "pulse";
      els.buttonMediaAction.value = "speak-text";
      els.buttonMediaValue.value = els.buttonLabel.value || "Next";
      els.variableName.value = "";
      els.variableOperation.value = "";
      els.variableValue.value = "";
      els.conditionOperator.value = "";
    }
    updateSelectedButton();
    setStatus("Action preset applied");
  }

  function renderLibrary() {
    var selected = els.librarySelect.value;
    var items = Data.listLibraryActivities();
    if (!items.length) {
      els.librarySelect.innerHTML = '<option value="">No saved activities</option>';
      return;
    }
    els.librarySelect.innerHTML = items.map(function (item) {
      var date = item.modified ? new Date(item.modified).toLocaleDateString() : "";
      return '<option value="' + item.id + '">' + escapeHtml(item.name) + (date ? " - " + escapeHtml(date) : "") + "</option>";
    }).join("");
    if (items.some(function (item) { return item.id === selected; })) {
      els.librarySelect.value = selected;
    }
  }

  function renderForm() {
    var currentPage = page();
    var button = selectedButton();
    els.activityName.value = state.activity.name || "";
    setEditorTitle(state.activity.name);
    els.rows.value = currentPage.gridRows || 2;
    els.columns.value = currentPage.gridColumns || 2;
    els.speakLabels.checked = state.activity.settings.speakLabels !== false;
    els.showLabels.checked = state.activity.settings.showLabels !== false;
    els.dwellTime.value = state.activity.settings.dwellTimeMs || 1200;
    setRangeText(els.dwellTime, els.dwellOutput);
    els.pageName.textContent = currentPage.name || "Page " + (state.pageIndex + 1);
    els.boardMeta.textContent = (currentPage.gridRows || 2) + " by " + (currentPage.gridColumns || 2) + " grid";
    if (!button) {
      els.buttonLabel.value = "";
      els.symbolId.value = "";
      els.buttonLayout.value = "label-bottom";
      els.buttonResult.value = "selected";
      els.buttonAction.value = "stay";
      setAdvancedActionFields(null);
      renderWordPredictions("");
      setRadioGroup(els.buttonFill, "#ffffff");
      setRadioGroup(els.buttonBorder, "#17212b");
      return;
    }
    state.selectedButtonId = button.id;
    els.buttonLabel.value = button.label || "";
    els.symbolId.value = button.symbolId || "";
    els.buttonLayout.value = button.symbolLayout || "label-bottom";
    els.buttonResult.value = button.result || "selected";
    els.buttonAction.value = buttonActionValue(button);
    setAdvancedActionFields(button);
    renderWordPredictions(button.label || "");
    setRadioGroup(els.buttonFill, (button.style && button.style.fillColour) || "#ffffff");
    setRadioGroup(els.buttonBorder, (button.style && button.style.borderColour) || "#17212b");
  }

  function renderBoard() {
    var currentPage = page();
    els.board.style.setProperty("--rows", currentPage.gridRows || 2);
    els.board.style.setProperty("--cols", currentPage.gridColumns || 2);
    els.board.innerHTML = (currentPage.buttons || []).map(renderButton).join("");
    hydrateBoardSymbols();
  }

  function render() {
    if (!state.selectedButtonId && page().buttons.length) {
      state.selectedButtonId = page().buttons[0].id;
    }
    renderPages();
    renderForm();
    renderBoard();
    renderButtonTable();
    renderLibrary();
    renderReadiness();
    updateHistoryButtons();
    scheduleOfflineStatus();
  }

  function persist(message) {
    state.activity = Data.saveCurrentActivity(state.activity);
    setStatus(message || "Saved");
    renderReadiness();
    updateHistoryButtons();
  }

  function applyGrid() {
    var currentPage = page();
    var rows = Math.max(1, Math.min(8, Number(els.rows.value || 2)));
    var columns = Math.max(1, Math.min(8, Number(els.columns.value || 2)));
    var total = rows * columns;
    pushHistory();
    currentPage.gridRows = rows;
    currentPage.gridColumns = columns;
    while (currentPage.buttons.length < total) {
      currentPage.buttons.push(Data.makeButton({ label: "Button " + (currentPage.buttons.length + 1) }, currentPage.buttons.length));
    }
    if (currentPage.buttons.length > total) {
      currentPage.buttons = currentPage.buttons.slice(0, total);
    }
    state.selectedButtonId = currentPage.buttons[0] ? currentPage.buttons[0].id : null;
    persist("Grid updated");
    render();
  }

  function updateSelectedButton() {
    var button = selectedButton();
    if (!button) return;
    var previousSymbolId = button.symbolId || "";
    var nextSymbolId = els.symbolId.value.trim();
    button.label = els.buttonLabel.value || "";
    button.audioCue = button.label;
    button.symbolId = nextSymbolId;
    if (nextSymbolId !== previousSymbolId) {
      if (!nextSymbolId) {
        button.symbolSrc = "";
      } else if (/^\d+$/.test(nextSymbolId)) {
        button.symbolSrc = Data.arasaacImageUrl(nextSymbolId);
      }
    }
    button.symbolLayout = els.buttonLayout.value;
    if (button.symbolLayout === "symbolate") button.type = "symbolate";
    if (button.symbolLayout !== "symbolate" && button.type === "symbolate") button.type = "standard";
    button.result = els.buttonResult.value;
    button.actions = selectedActions();
    button.style = Object.assign({}, button.style || {}, {
      fillColour: radioGroupValue(els.buttonFill, (button.style && button.style.fillColour) || "#ffffff"),
      borderColour: radioGroupValue(els.buttonBorder, (button.style && button.style.borderColour) || "#17212b")
    });
    persist("Button updated");
    renderWordPredictions(button.label);
    renderBoard();
    renderButtonTable();
  }

  function templateFallback(path) {
    if (path.indexOf("choice-board-9") >= 0) {
      return Data.createGridActivity({
        name: "Choice Board 9",
        rows: 3,
        columns: 3,
        labels: ["Yes", "No", "More", "Stop", "Help", "Go", "Like", "Want", "Finished"],
        symbolIds: ["5584", "5526", "5508", "7196", "32648", "8142", "37826", "5441", "28429"]
      });
    }
    if (path.indexOf("visual-schedule") >= 0) {
      return Data.createGridActivity({
        name: "Visual Schedule",
        rows: 2,
        columns: 4,
        labels: ["School", "Morning", "Work", "Break", "Lunch", "Outside", "Pack Up", "Home"],
        symbolIds: ["32446", "25704", "6624", "6604", "4611", "5475", "10245", "6964"]
      });
    }
    if (path.indexOf("first-then") >= 0) {
      return Data.createGridActivity({
        name: "First Then",
        rows: 1,
        columns: 2,
        labels: ["First: Work", "Then: Break"],
        symbolIds: ["6624", "6604"]
      });
    }
    if (path.indexOf("book-reader") >= 0) {
      var activity = Data.createGridActivity({
        name: "Animal Book Reader",
        rows: 1,
        columns: 2,
        labels: ["I see a dog", "Next"],
        symbolIds: ["7202", "6630"]
      });
      activity.pages[0].name = "Dog";
      activity.pages[0].buttons[1].actions = actionsForValue("next-page");
      ["Cat", "Bird"].forEach(function (name, index) {
        var pageActivity = Data.createGridActivity({
          name: "Animal Book Reader",
          rows: 1,
          columns: 2,
          labels: [index === 0 ? "I see a cat" : "I see a bird", index === 0 ? "Next" : "Finished"],
          symbolIds: [index === 0 ? "7114" : "2490", index === 0 ? "6630" : "28429"]
        });
        var newPage = pageActivity.pages[0];
        newPage.name = name;
        if (index === 0) newPage.buttons[1].actions = actionsForValue("next-page");
        activity.pages.push(newPage);
      });
      return activity;
    }
    if (path.indexOf("quiz-4") >= 0) {
      var quiz = Data.createGridActivity({
        name: "Quiz 4",
        rows: 2,
        columns: 2,
        labels: ["Dog", "Cat", "Bird", "I don't know"],
        symbolIds: ["7202", "7114", "2490", "32648"]
      });
      quiz.pages[0].name = "Which animal says woof?";
      quiz.pages[0].buttons[0].result = "correct";
      quiz.pages[0].buttons[1].result = "incorrect";
      quiz.pages[0].buttons[2].result = "incorrect";
      return quiz;
    }
    return Data.defaultActivity();
  }

  function loadTemplate() {
    var path = els.templateSelect.value;
    var before = snapshot();
    setStatus("Loading template");
    fetch(path)
      .then(function (response) {
        if (!response.ok) throw new Error("Template unavailable");
        return response.json();
      })
      .catch(function () {
        return templateFallback(path);
      })
      .then(function (json) {
        pushSnapshot(before);
        state.activity = Data.saveCurrentActivity(json);
        state.pageIndex = 0;
        state.selectedButtonId = page().buttons[0] ? page().buttons[0].id : null;
        setStatus("Template loaded");
        render();
      });
  }

  function quickLabels() {
    return els.quickFillLabels.value
      .split(/[\n,;]+/)
      .map(function (label) { return label.trim(); })
      .filter(Boolean)
      .slice(0, 36);
  }

  function applyQuickPreset() {
    var preset = QUICK_PRESETS[els.quickBoardType.value] || QUICK_PRESETS.choice;
    els.quickBoardName.value = preset.name;
    els.quickFillLabels.value = preset.labels.join(", ");
  }

  function buildQuickBoard() {
    var labels = quickLabels();
    if (!labels.length) {
      setStatus("Paste labels first");
      return false;
    }
    pushHistory();
    var columns = Math.ceil(Math.sqrt(labels.length));
    var rows = Math.ceil(labels.length / columns);
    state.activity = Data.createGridActivity({
      name: els.quickBoardName.value.trim() || "Quick Board",
      rows: rows,
      columns: columns,
      labels: labels
    });
    state.activity.pages[0].buttons = state.activity.pages[0].buttons.slice(0, labels.length);
    state.pageIndex = 0;
    state.selectedButtonId = page().buttons[0] ? page().buttons[0].id : null;
    persist("Quick board built");
    render();
    return true;
  }

  function searchTermForLabel(label) {
    var cleaned = String(label || "")
      .replace(/^(first|then)\s*:\s*/i, "")
      .replace(/[^\w\s]/g, " ")
      .trim()
      .toLowerCase();
    if (SEARCH_ALIASES[cleaned]) return SEARCH_ALIASES[cleaned];
    var terms = cleaned.split(/\s+/).filter(Boolean);
    var last = terms.slice(-1)[0] || label;
    return SEARCH_ALIASES[last] || last;
  }

  function wordParts(text) {
    return String(text || "").trim().split(/\s+/).filter(Boolean);
  }

  function predictWords(text) {
    var parts = wordParts(text.toLowerCase());
    var current = parts.slice(-1)[0] || "";
    var previous = parts.length > 1 ? parts[parts.length - 2] : "";
    var boardWords = (page().buttons || []).map(function (button) {
      return String(button.label || "").toLowerCase();
    });
    var mapped = WORD_PREDICTIONS[current] || [];
    var previousMapped = WORD_PREDICTIONS[previous] || [];
    var pool = [];
    pool = pool.concat(mapped, previousMapped);
    pool = pool.concat(boardWords, COMMON_WORDS);
    var seen = {};
    return pool.filter(function (word) {
      var key = String(word || "").toLowerCase();
      if (!key || key === current || seen[key]) return false;
      seen[key] = true;
      return !current || key.indexOf(current) === 0 || mapped.indexOf(word) >= 0 || previousMapped.indexOf(word) >= 0;
    }).slice(0, 6);
  }

  function renderWordPredictions(text) {
    if (!els.wordPredictions) return;
    var predictions = predictWords(text);
    els.wordPredictions.innerHTML = predictions.map(function (word) {
      return '<button type="button" data-predict-word="' + escapeHtml(word) + '">' + escapeHtml(word) + "</button>";
    }).join("");
  }

  function applyPrediction(word) {
    var parts = wordParts(els.buttonLabel.value);
    var lower = word.toLowerCase();
    if (parts.length && lower.indexOf(parts[parts.length - 1].toLowerCase()) === 0) {
      parts[parts.length - 1] = word;
    } else {
      parts.push(word);
    }
    els.buttonLabel.value = parts.join(" ");
    updateSelectedButton();
    renderWordPredictions(els.buttonLabel.value);
    els.buttonLabel.focus();
  }

  function symbolateSelectedButton() {
    var button = selectedButton();
    if (!button) return Promise.resolve(false);
    var words = wordParts(button.label).slice(0, 12);
    if (!words.length) {
      setStatus("Type a label first");
      return Promise.resolve(false);
    }
    var before = snapshot();
    var segments = [];
    setStatus("Building Symbolate");
    return words.reduce(function (chain, word) {
      return chain.then(function () {
        return Symbols.searchArasaac(searchTermForLabel(word)).then(function (results) {
          if (!results.length) {
            segments.push({ text: word, symbolId: "", symbolSrc: "" });
            return null;
          }
          return Symbols.cacheImage(results[0]).then(function (result) {
            segments.push({
              text: word,
              symbolId: result.id,
              symbolSrc: result.imageUrl,
              attribution: result.attribution
            });
          });
        }).catch(function () {
          segments.push({ text: word, symbolId: "", symbolSrc: "" });
        });
      });
    }, Promise.resolve()).then(function () {
      pushSnapshot(before);
      button.type = "symbolate";
      button.symbolLayout = "symbolate";
      button.symbolateSegments = segments;
      persist("Symbolate built");
      render();
      return true;
    });
  }

  function clearSymbolate() {
    var button = selectedButton();
    if (!button) return;
    pushHistory();
    button.type = "standard";
    button.symbolLayout = "label-bottom";
    button.symbolateSegments = [];
    persist("Symbolate cleared");
    render();
  }

  function autoFillSymbols() {
    var before = snapshot();
    var currentPage = page();
    var buttons = currentPage.buttons || [];
    if (!buttons.length) {
      setStatus("No buttons to fill");
      return Promise.resolve(false);
    }
    var matched = 0;
    setStatus("Finding symbols");
    return buttons.reduce(function (chain, button) {
      return chain.then(function () {
        if (button.symbolId && button.symbolSrc) return null;
        return Symbols.searchArasaac(searchTermForLabel(button.label)).then(function (results) {
          if (!results.length) return null;
          return Symbols.cacheImage(results[0]).then(function (result) {
            matched += 1;
            button.symbolId = result.id;
            button.symbolSrc = result.imageUrl;
            button.symbolAttribution = {
              source: result.source,
              licence: result.licence,
              attribution: result.attribution
            };
            setStatus("Matched " + matched + " symbol" + (matched === 1 ? "" : "s"));
            renderBoard();
            return null;
          });
        }).catch(function () {
          return null;
        });
      });
    }, Promise.resolve()).then(function () {
      if (matched) pushSnapshot(before);
      persist(matched ? "Symbols filled" : "No new symbols found");
      render();
      return Boolean(matched);
    });
  }

  function buildWithSymbols() {
    if (!buildQuickBoard()) return;
    autoFillSymbols();
  }

  function uploadCustomSymbol() {
    var file = els.customSymbolUpload.files && els.customSymbolUpload.files[0];
    var button = selectedButton();
    if (!file || !button) return;
    var before = snapshot();
    if (!file.type || file.type.indexOf("image/") !== 0) {
      setStatus("Choose an image file");
      els.customSymbolUpload.value = "";
      return;
    }
    resizeImageFile(file, 512)
      .then(function (dataUrl) {
        pushSnapshot(before);
        button.symbolId = "custom-" + Data.uid("symbol");
        button.symbolSrc = dataUrl;
        button.symbolAttribution = {
          source: "teacher-uploaded",
          licence: "teacher-owned",
          attribution: file.name
        };
        els.symbolId.value = button.symbolId;
        persist("Custom symbol uploaded");
        renderBoard();
        els.customSymbolUpload.value = "";
      })
      .catch(function () {
        setStatus("Could not read image");
        els.customSymbolUpload.value = "";
      });
  }

  function resizeImageFile(file, maxSize) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onload = function () {
        var original = String(reader.result || "");
        if (!global.Image || !document.createElement) {
          resolve(original);
          return;
        }
        var image = new Image();
        image.onload = function () {
          var scale = Math.min(1, maxSize / Math.max(image.width, image.height));
          var canvas = document.createElement("canvas");
          canvas.width = Math.max(1, Math.round(image.width * scale));
          canvas.height = Math.max(1, Math.round(image.height * scale));
          var context = canvas.getContext("2d");
          if (!context) {
            resolve(original);
            return;
          }
          context.clearRect(0, 0, canvas.width, canvas.height);
          context.drawImage(image, 0, 0, canvas.width, canvas.height);
          resolve(canvas.toDataURL("image/png"));
        };
        image.onerror = function () {
          resolve(original);
        };
        image.src = original;
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  function saveToLibrary() {
    try {
      state.activity = Data.saveActivityToLibrary(state.activity);
      Data.saveCurrentActivity(state.activity);
      renderLibrary();
      setStatus("Saved to library");
    } catch (error) {
      setStatus("Could not save to library");
    }
  }

  function openFromLibrary() {
    var id = els.librarySelect.value;
    var activity = Data.loadActivityFromLibrary(id);
    if (!activity) {
      setStatus("Choose a saved activity");
      return;
    }
    pushHistory();
    state.activity = Data.saveCurrentActivity(activity);
    state.pageIndex = 0;
    state.selectedButtonId = page().buttons[0] ? page().buttons[0].id : null;
    setStatus("Opened from library");
    render();
  }

  function deleteFromLibrary() {
    var id = els.librarySelect.value;
    if (!id) {
      setStatus("Choose a saved activity");
      return;
    }
    var selectedName = els.librarySelect.options[els.librarySelect.selectedIndex] ? els.librarySelect.options[els.librarySelect.selectedIndex].textContent : "this activity";
    if (!global.confirm || global.confirm("Delete " + selectedName + " from the local library?")) {
      Data.deleteActivityFromLibrary(id);
      renderLibrary();
      setStatus("Deleted from library");
    }
  }

  function addButton() {
    var currentPage = page();
    pushHistory();
    currentPage.buttons.push(Data.makeButton({ label: "Button " + (currentPage.buttons.length + 1) }, currentPage.buttons.length));
    var count = currentPage.buttons.length;
    currentPage.gridRows = Math.max(1, Math.ceil(Math.sqrt(count)));
    currentPage.gridColumns = Math.max(1, Math.ceil(count / currentPage.gridRows));
    state.selectedButtonId = currentPage.buttons[currentPage.buttons.length - 1].id;
    persist("Button added");
    render();
  }

  function removeButton() {
    var currentPage = page();
    if (!currentPage.buttons.length) return;
    pushHistory();
    var index = currentPage.buttons.findIndex(function (button) {
      return button.id === state.selectedButtonId;
    });
    if (index < 0) index = currentPage.buttons.length - 1;
    currentPage.buttons.splice(index, 1);
    state.selectedButtonId = currentPage.buttons[Math.max(0, index - 1)] ? currentPage.buttons[Math.max(0, index - 1)].id : null;
    persist("Button removed");
    render();
  }

  function addPage() {
    pushHistory();
    var activity = Data.createGridActivity({ name: state.activity.name, rows: 2, columns: 2 });
    var newPage = activity.pages[0];
    newPage.name = "Page " + (state.activity.pages.length + 1);
    state.activity.pages.push(newPage);
    state.pageIndex = state.activity.pages.length - 1;
    state.selectedButtonId = newPage.buttons[0].id;
    persist("Page added");
    render();
  }

  function duplicatePage() {
    pushHistory();
    var copy = Data.clone(page());
    copy.id = Data.uid("page");
    copy.name = copy.name + " Copy";
    copy.buttons = copy.buttons.map(function (button, index) {
      button.id = Data.uid("btn");
      button.actions = (button.actions || []).map(function (action) {
        action.id = Data.uid("action");
        return action;
      });
      button.position = button.position || { x: 0, y: 0, width: 25, height: 25 };
      return Data.makeButton(button, index);
    });
    state.activity.pages.push(copy);
    state.pageIndex = state.activity.pages.length - 1;
    state.selectedButtonId = copy.buttons[0] ? copy.buttons[0].id : null;
    persist("Page duplicated");
    render();
  }

  function deletePage() {
    if (state.activity.pages.length <= 1) {
      setStatus("Activity needs one page");
      return;
    }
    pushHistory();
    state.activity.pages.splice(state.pageIndex, 1);
    state.pageIndex = Math.max(0, state.pageIndex - 1);
    state.selectedButtonId = page().buttons[0] ? page().buttons[0].id : null;
    persist("Page deleted");
    render();
  }

  function newActivity() {
    pushHistory();
    state.activity = Data.createGridActivity({
      name: "New Choice Board",
      rows: Number(els.rows.value || 2),
      columns: Number(els.columns.value || 2)
    });
    state.pageIndex = 0;
    state.selectedButtonId = state.activity.pages[0].buttons[0].id;
    persist("New activity created");
    render();
  }

  function applySymbol(result) {
    var button = selectedButton();
    if (!button) return;
    pushHistory();
    Symbols.cacheImage(result).then(function (cachedResult) {
      button.symbolId = cachedResult.id;
      button.symbolSrc = cachedResult.imageUrl;
      button.symbolAttribution = {
        source: cachedResult.source,
        licence: cachedResult.licence,
        attribution: cachedResult.attribution
      };
      if (!button.label || /^Button \d+$/.test(button.label)) {
        button.label = cachedResult.label;
        button.audioCue = cachedResult.label;
        els.buttonLabel.value = cachedResult.label;
      }
      els.symbolId.value = cachedResult.id;
      persist("Symbol applied");
      renderBoard();
      scheduleOfflineStatus();
    });
  }

  function renderSymbolResults(results) {
    if (!results.length) {
      els.symbolResults.innerHTML = '<p class="status-line">No matches</p>';
      return;
    }
    els.symbolResults.innerHTML = results.map(function (result) {
      return '<div class="symbol-result">' +
        '<img src="' + result.imageUrl + '" alt="" data-symbol-id="' + escapeHtml(result.id) + '">' +
        '<div><strong>' + escapeHtml(result.label) + '</strong><span class="status-line">ARASAAC ' + escapeHtml(result.id) + "</span></div>" +
        '<button type="button" data-symbol-id="' + result.id + '">Use</button>' +
        "</div>";
    }).join("");
    Array.prototype.forEach.call(els.symbolResults.querySelectorAll("[data-symbol-id]"), function (button) {
      button.addEventListener("click", function () {
        var result = results.find(function (item) {
          return item.id === button.dataset.symbolId;
        });
        applySymbol(result);
      });
    });
    if (Symbols.hydrateImages) Symbols.hydrateImages(els.symbolResults);
  }

  function searchSymbols(event) {
    event.preventDefault();
    var term = els.symbolSearch.value.trim() || els.buttonLabel.value.trim();
    if (!term) return;
    els.symbolResults.innerHTML = '<p class="status-line">Searching</p>';
    Symbols.searchArasaac(term)
      .then(function (results) {
        renderSymbolResults(results);
        setStatus("Symbol search complete");
      })
      .catch(function () {
        els.symbolResults.innerHTML = '<p class="status-line">Search unavailable</p>';
        setStatus("ARASAAC search unavailable");
      });
  }

  function handleSymbolImageError(event) {
    var image = event.target;
    if (!image || !image.tagName || image.tagName.toLowerCase() !== "img") return;
    var holder = image.closest(".button-symbol");
    var button = image.closest("[data-button-id]");
    var symbolId = image.getAttribute("data-symbol-id");
    if (Symbols.getCachedSymbol && symbolId) {
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
      setStatus("A symbol image could not load; text fallback is showing");
    }
  }

  function hydrateBoardSymbols() {
    if (Symbols.hydrateImages) Symbols.hydrateImages(els.board);
  }

  function scheduleOfflineStatus() {
    if (!Symbols.countActivityCached) return;
    setOfflineBanner("is-checking", "Checking app and symbol cache");
    if (state.offlineStatusTimer) global.clearTimeout(state.offlineStatusTimer);
    state.offlineStatusTimer = global.setTimeout(function () {
      Symbols.countActivityCached(state.activity).then(function (result) {
        if (!result.total) {
          state.offlineStatus = {
            ok: true,
            message: "No online symbols required"
          };
        } else {
          state.offlineStatus = {
            ok: result.missing === 0,
            message: result.cached + " of " + result.total + " cached"
          };
        }
        renderReadiness();
        updateOfflineBannerFromCounts(result);
      });
    }, 250);
  }

  function prepareOfflineSymbols() {
    if (!Symbols.cacheActivity) {
      setStatus("Offline symbol cache unavailable");
      return;
    }
    setStatus("Preparing symbols for offline use");
    Symbols.cacheActivity(state.activity, function (progress) {
      setStatus("Cached " + progress.cached + " of " + progress.total + " symbols");
    }).then(function (result) {
      state.offlineStatus = {
        ok: result.failed === 0,
        message: result.cached + " of " + result.total + " cached"
      };
      renderReadiness();
      updateOfflineBannerFromCounts({
        total: result.total,
        cached: result.cached,
        missing: result.failed
      });
      setStatus(result.failed ? "Some symbols could not be cached" : "Offline symbols ready");
    });
  }

  function checkArasaacStatus() {
    if (!Symbols.checkStatus) return;
    state.arasaacStatus = {
      ok: null,
      message: "Checking ARASAAC"
    };
    renderReadiness();
    Symbols.checkStatus().then(function (result) {
      state.arasaacStatus = result;
      renderReadiness();
    });
  }

  function registerServiceWorker() {
    if (!("serviceWorker" in navigator)) return;
    if (location.protocol !== "http:" && location.protocol !== "https:") return;
    navigator.serviceWorker.register("sw.js").catch(function (error) {
      console.warn("Service worker registration failed", error);
    });
  }

  function bind() {
    els.newActivity.addEventListener("click", newActivity);
    els.undoChange.addEventListener("click", undoChange);
    els.redoChange.addEventListener("click", redoChange);
    els.loadTemplate.addEventListener("click", loadTemplate);
    els.quickBoardType.addEventListener("change", applyQuickPreset);
    els.buildQuickBoard.addEventListener("click", buildQuickBoard);
    els.buildWithSymbols.addEventListener("click", buildWithSymbols);
    els.autoSymbols.addEventListener("click", autoFillSymbols);
    els.fixMissingSymbols.addEventListener("click", autoFillSymbols);
    els.prepareOffline.addEventListener("click", prepareOfflineSymbols);
    els.symbolateLabel.addEventListener("click", symbolateSelectedButton);
    els.clearSymbolate.addEventListener("click", clearSymbolate);
    els.applyActionPreset.addEventListener("click", function () {
      setActionPresetFields(els.actionPreset.value);
    });
    els.saveLibrary.addEventListener("click", saveToLibrary);
    els.openLibrary.addEventListener("click", openFromLibrary);
    els.deleteLibrary.addEventListener("click", deleteFromLibrary);
    els.saveLocal.addEventListener("click", function () {
      persist("Saved locally");
    });
    els.downloadJson.addEventListener("click", function () {
      FileIO.downloadJson(state.activity);
    });
    els.printCurrent.addEventListener("click", function () {
      window.print();
    });
    FileIO.bindJsonInput(els.importJson, function (json) {
      pushHistory();
      state.activity = Data.saveCurrentActivity(json);
      state.pageIndex = 0;
      state.selectedButtonId = page().buttons[0] ? page().buttons[0].id : null;
      setStatus("Activity imported");
      render();
    }, function () {
      setStatus("Could not import JSON");
    });
    els.activityName.addEventListener("input", function () {
      state.activity.name = els.activityName.value;
      persist("Activity renamed");
    });
    els.applyGrid.addEventListener("click", applyGrid);
    els.addButton.addEventListener("click", addButton);
    els.removeButton.addEventListener("click", removeButton);
    els.addPage.addEventListener("click", addPage);
    els.duplicatePage.addEventListener("click", duplicatePage);
    els.deletePage.addEventListener("click", deletePage);
    els.speakLabels.addEventListener("change", function () {
      state.activity.settings.speakLabels = els.speakLabels.checked;
      persist("Speech setting updated");
    });
    els.showLabels.addEventListener("change", function () {
      state.activity.settings.showLabels = els.showLabels.checked;
      persist("Label setting updated");
      renderBoard();
    });
    els.dwellTime.addEventListener("input", function () {
      state.activity.settings.dwellTimeMs = Number(els.dwellTime.value);
      setRangeText(els.dwellTime, els.dwellOutput);
      persist("Dwell setting updated");
    });
    ["input", "change"].forEach(function (eventName) {
      [
        els.buttonLabel,
        els.symbolId,
        els.buttonLayout,
        els.buttonResult,
        els.buttonAction,
        els.buttonAnimation,
        els.buttonMediaAction,
        els.buttonMediaValue,
        els.variableName,
        els.variableOperation,
        els.variableValue,
        els.conditionVariable,
        els.conditionOperator,
        els.conditionValue,
        els.conditionTrueAction,
        els.conditionFalseAction,
        els.buttonFill,
        els.buttonBorder
      ].forEach(function (control) {
        forEachControl(control, function (item) {
          item.addEventListener(eventName, updateSelectedButton);
        });
      });
    });
    els.board.addEventListener("click", function (event) {
      var button = event.target.closest("[data-button-id]");
      if (!button) return;
      state.selectedButtonId = button.dataset.buttonId;
      render();
    });
    els.board.addEventListener("error", handleSymbolImageError, true);
    els.wordPredictions.addEventListener("click", function (event) {
      var button = event.target.closest("[data-predict-word]");
      if (!button) return;
      applyPrediction(button.dataset.predictWord);
    });
    els.pageList.addEventListener("click", function (event) {
      var button = event.target.closest("[data-page-index]");
      if (!button) return;
      state.pageIndex = Number(button.dataset.pageIndex);
      state.selectedButtonId = page().buttons[0] ? page().buttons[0].id : null;
      render();
    });
    els.buttonTable.addEventListener("click", function (event) {
      var button = event.target.closest("[data-select-button]");
      if (!button) return;
      state.selectedButtonId = button.dataset.selectButton;
      render();
    });
    els.symbolSearchForm.addEventListener("submit", searchSymbols);
    els.customSymbolUpload.addEventListener("change", uploadCustomSymbol);

    [
      els.activityName,
      els.speakLabels,
      els.showLabels,
      els.dwellTime,
      els.buttonLabel,
      els.symbolId,
      els.buttonLayout,
      els.buttonResult,
      els.buttonAction,
      els.buttonAnimation,
      els.buttonMediaAction,
      els.buttonMediaValue,
      els.variableName,
      els.variableOperation,
      els.variableValue,
      els.conditionVariable,
      els.conditionOperator,
      els.conditionValue,
      els.conditionTrueAction,
      els.conditionFalseAction,
      els.buttonFill,
      els.buttonBorder
    ].forEach(function (control) {
      forEachControl(control, function (item) {
        item.addEventListener("focusin", beginEditSnapshot);
        item.addEventListener("change", commitEditSnapshot);
        item.addEventListener("blur", commitEditSnapshot);
      });
    });

    document.addEventListener("keydown", function (event) {
      var key = event.key.toLowerCase();
      if ((event.metaKey || event.ctrlKey) && key === "z" && !event.shiftKey) {
        event.preventDefault();
        undoChange();
      }
      if ((event.metaKey || event.ctrlKey) && (key === "y" || (key === "z" && event.shiftKey))) {
        event.preventDefault();
        redoChange();
      }
    });
    global.addEventListener("online", checkArasaacStatus);
    global.addEventListener("online", scheduleOfflineStatus);
    global.addEventListener("offline", checkArasaacStatus);
    global.addEventListener("offline", scheduleOfflineStatus);
  }

  function init() {
    els = {
      status: document.getElementById("editor-status"),
      newActivity: document.getElementById("new-activity"),
      undoChange: document.getElementById("undo-change"),
      redoChange: document.getElementById("redo-change"),
      templateSelect: document.getElementById("template-select"),
      loadTemplate: document.getElementById("load-template"),
      quickBoardType: document.getElementById("quick-board-type"),
      quickBoardName: document.getElementById("quick-board-name"),
      quickFillLabels: document.getElementById("quick-fill-labels"),
      buildQuickBoard: document.getElementById("build-quick-board"),
      buildWithSymbols: document.getElementById("build-with-symbols"),
      autoSymbols: document.getElementById("auto-symbols"),
      readinessList: document.getElementById("readiness-list"),
      fixMissingSymbols: document.getElementById("fix-missing-symbols"),
      prepareOffline: document.getElementById("prepare-offline"),
      librarySelect: document.getElementById("library-select"),
      saveLibrary: document.getElementById("save-library"),
      openLibrary: document.getElementById("open-library"),
      deleteLibrary: document.getElementById("delete-library"),
      saveLocal: document.getElementById("save-local"),
      downloadJson: document.getElementById("download-json"),
      importJson: document.getElementById("import-json"),
      printCurrent: document.getElementById("print-current"),
      activityName: document.getElementById("activity-name"),
      rows: document.getElementById("grid-rows"),
      columns: document.getElementById("grid-columns"),
      applyGrid: document.getElementById("apply-grid"),
      pageList: document.getElementById("page-list"),
      addPage: document.getElementById("add-page"),
      duplicatePage: document.getElementById("duplicate-page"),
      deletePage: document.getElementById("delete-page"),
      speakLabels: document.getElementById("speak-labels"),
      showLabels: document.getElementById("show-labels"),
      dwellTime: document.getElementById("dwell-time"),
      dwellOutput: document.getElementById("dwell-time-output"),
      pageName: document.getElementById("current-page-name"),
      boardMeta: document.getElementById("board-meta"),
      addButton: document.getElementById("add-button"),
      removeButton: document.getElementById("remove-button"),
      board: document.getElementById("editor-board"),
      offlineBanner: document.getElementById("offline-banner"),
      buttonLabel: document.getElementById("button-label"),
      wordPredictions: document.getElementById("word-predictions"),
      symbolId: document.getElementById("button-symbol-id"),
      buttonLayout: document.getElementById("button-layout"),
      symbolateLabel: document.getElementById("symbolate-label"),
      clearSymbolate: document.getElementById("clear-symbolate"),
      buttonResult: document.getElementById("button-result"),
      buttonAction: document.getElementById("button-action"),
      actionPreset: document.getElementById("action-preset"),
      applyActionPreset: document.getElementById("apply-action-preset"),
      buttonAnimation: document.getElementById("button-animation"),
      buttonMediaAction: document.getElementById("button-media-action"),
      buttonMediaValue: document.getElementById("button-media-value"),
      variableName: document.getElementById("variable-name"),
      variableOperation: document.getElementById("variable-operation"),
      variableValue: document.getElementById("variable-value"),
      conditionVariable: document.getElementById("condition-variable"),
      conditionOperator: document.getElementById("condition-operator"),
      conditionValue: document.getElementById("condition-value"),
      conditionTrueAction: document.getElementById("condition-true-action"),
      conditionFalseAction: document.getElementById("condition-false-action"),
      buttonFill: document.querySelectorAll("input[name='button-fill']"),
      buttonBorder: document.querySelectorAll("input[name='button-border']"),
      symbolSearchForm: document.getElementById("symbol-search-form"),
      symbolSearch: document.getElementById("symbol-search-term"),
      customSymbolUpload: document.getElementById("custom-symbol-upload"),
      symbolResults: document.getElementById("symbol-results"),
      buttonTable: document.getElementById("button-table")
    };
    state.activity = Data.saveCurrentActivity(state.activity);
    state.selectedButtonId = page().buttons[0] ? page().buttons[0].id : null;
    applyQuickPreset();
    bind();
    render();
    checkArasaacStatus();
    registerServiceWorker();
  }

  document.addEventListener("DOMContentLoaded", init);
})(window);

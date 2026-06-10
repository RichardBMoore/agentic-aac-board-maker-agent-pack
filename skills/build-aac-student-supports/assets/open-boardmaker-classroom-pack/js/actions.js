(function (global) {
  "use strict";

  function actionResult(button) {
    var result = button.result || "selected";
    (button.actions || []).forEach(function (action) {
      if (action.type === "mark-correct") result = "correct";
      if (action.type === "mark-incorrect") result = "incorrect";
    });
    return result;
  }

  function ensureVariables(activity) {
    if (!activity.variables || typeof activity.variables !== "object") activity.variables = {};
    return activity.variables;
  }

  function coerce(value) {
    var number = Number(value);
    return Number.isFinite(number) && String(value).trim() !== "" ? number : String(value == null ? "" : value);
  }

  function compare(actual, operator, expected) {
    var left = coerce(actual);
    var right = coerce(expected);
    if (operator === "not-equals") return left !== right;
    if (operator === "greater-than") return Number(left) > Number(right);
    if (operator === "less-than") return Number(left) < Number(right);
    return left === right;
  }

  function actionFromChoice(choice) {
    if (choice === "next-page") return { type: "next-page" };
    if (choice === "previous-page") return { type: "previous-page" };
    return { type: "stay" };
  }

  // Message-bar accumulator for sentence-builder style boards
  // (add-to-message / speak-message / remove-last-word / clear-message).
  var messageWords = [];

  function resetMessage() {
    messageWords = [];
  }

  function runActions(button, context) {
    var ctx = context || {};
    var activity = ctx.activity;
    var page = ctx.page;
    var settings = activity && activity.settings ? activity.settings : {};
    var actions = button.actions && button.actions.length ? button.actions : [{ type: "speak-label" }, { type: "log-attempt" }];
    var result = actionResult(button);
    var didSpeak = false;
    var didLog = false;
    var didMessage = false;

    function runOne(action) {
      if (action.type === "speak-label" && settings.speakLabels !== false) {
        global.BoardmakerTts.speak(button.label || button.audioCue || "");
        didSpeak = true;
      }
      if (action.type === "speak-text" && action.text) {
        global.BoardmakerTts.speak(action.text);
        didSpeak = true;
      }
      if (action.type === "navigate-page" && ctx.goToPage) {
        ctx.goToPage(action.targetPageId || action.pageId);
      }
      if (action.type === "next-page" && ctx.nextPage) {
        ctx.nextPage();
      }
      if (action.type === "previous-page" && ctx.previousPage) {
        ctx.previousPage();
      }
      if (action.type === "animate" && ctx.animateButton) {
        ctx.animateButton(button.id, action.animation || "pulse");
      }
      if (action.type === "open-url" && action.url && ctx.openUrl) {
        ctx.openUrl(action.url);
      }
      if (action.type === "play-audio" && action.src && ctx.playAudio) {
        ctx.playAudio(action.src);
      }
      if (action.type === "set-variable" && action.name) {
        ensureVariables(activity)[action.name] = coerce(action.value);
        if (ctx.saveActivity) ctx.saveActivity();
      }
      if (action.type === "increment-variable" && action.name) {
        var variables = ensureVariables(activity);
        var current = Number(variables[action.name] || 0);
        var amount = Number(action.value || 1);
        variables[action.name] = current + (Number.isFinite(amount) ? amount : 1);
        if (ctx.saveActivity) ctx.saveActivity();
      }
      if (action.type === "conditional" && action.variable) {
        var value = ensureVariables(activity)[action.variable];
        var choice = compare(value, action.operator || "equals", action.value) ? action.ifTrue : action.ifFalse;
        runOne(actionFromChoice(choice));
      }
      if (action.type === "log-attempt" && ctx.logAttempt) {
        ctx.logAttempt(button, result);
        didLog = true;
      }
      if (action.type === "add-to-message") {
        messageWords.push(action.text || button.spokenText || button.label || "");
        if (ctx.setMessage) ctx.setMessage(messageWords.join(" "));
        didMessage = true;
      }
      if (action.type === "speak-message") {
        global.BoardmakerTts.speak(messageWords.join(" "));
        didSpeak = true;
        didMessage = true;
      }
      if (action.type === "remove-last-word") {
        messageWords.pop();
        if (ctx.setMessage) ctx.setMessage(messageWords.join(" "));
        didMessage = true;
      }
      if (action.type === "clear-message") {
        messageWords = [];
        if (ctx.setMessage) ctx.setMessage("");
        didMessage = true;
      }
    }

    actions.forEach(runOne);

    if (!didSpeak && settings.speakLabels !== false) {
      global.BoardmakerTts.speak(button.label || button.audioCue || "");
    }
    if (!didLog && ctx.logAttempt) {
      ctx.logAttempt(button, result);
    }
    if (ctx.flashButton) {
      ctx.flashButton(button.id, result);
    }
    if (ctx.setMessage && !didMessage && messageWords.length === 0) {
      ctx.setMessage(button.label || "");
    }
    return result;
  }

  global.BoardmakerActions = {
    runActions: runActions,
    actionResult: actionResult,
    resetMessage: resetMessage
  };
})(window);

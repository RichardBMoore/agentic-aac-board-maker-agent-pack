/* SCORM 1.2 launch bridge for Agentic AAC Board Maker activities.
 *
 * Added beside an unchanged activity when it is packaged for an LMS (for
 * example Canvas/QLearn's SCORM tool). It only tells the LMS that the
 * activity opened (LMSInitialize) and closed (LMSFinish).
 *
 * - No scores, answers, selections or student messages are ever sent.
 * - Completion is reported only when the package was built with
 *   --report-completion (data-report-completion="true" on this script tag).
 * - With no LMS (opened from a file or a plain web page) it does nothing,
 *   so the activity behaves exactly as the standalone file does.
 *
 * Status for teachers/QA: window.AACScorm.status() in the browser console.
 */
(function () {
  "use strict";

  var MAX_PARENT_HOPS = 12;
  var script = document.currentScript;
  var reportCompletion = Boolean(script && script.getAttribute("data-report-completion") === "true");

  var state = {
    mode: "standalone",
    apiFound: false,
    initialised: false,
    finished: false,
    completionReported: false,
    reportCompletion: reportCompletion,
    calls: [],
    lastError: ""
  };

  function hasApi(win) {
    try {
      return Boolean(win && win.API && typeof win.API.LMSInitialize === "function");
    } catch (error) {
      return false; // Cross-origin frame: SCORM 1.2 cannot reach it, so stop here.
    }
  }

  function searchUp(win) {
    var hops = 0;
    var current = win;
    while (current && hops <= MAX_PARENT_HOPS) {
      if (hasApi(current)) return current.API;
      var parent;
      try {
        parent = current.parent;
      } catch (error) {
        return null;
      }
      if (!parent || parent === current) break;
      current = parent;
      hops += 1;
    }
    return null;
  }

  function findApi() {
    var api = searchUp(window);
    if (api) return api;
    try {
      var top = window.top;
      if (top && top.opener && !top.opener.closed) return searchUp(top.opener);
    } catch (error) {
      return null;
    }
    return null;
  }

  var api = findApi();

  function call(name, value) {
    if (!api) return false;
    try {
      var result = arguments.length > 2 ? api[name](value, arguments[2]) : api[name](value === undefined ? "" : value);
      state.calls.push(name);
      var ok = String(result) === "true";
      if (!ok && typeof api.LMSGetLastError === "function") {
        state.lastError = String(api.LMSGetLastError());
      }
      return ok;
    } catch (error) {
      state.lastError = String(error && error.message ? error.message : error);
      return false;
    }
  }

  if (api) {
    state.mode = "lms";
    state.apiFound = true;
    state.initialised = call("LMSInitialize", "");
    if (state.initialised && reportCompletion) {
      state.completionReported = call("LMSSetValue", "cmi.core.lesson_status", "completed") && call("LMSCommit", "");
    }
  }

  function finish() {
    if (!api || !state.initialised || state.finished) return;
    state.finished = true;
    call("LMSFinish", "");
  }

  window.addEventListener("pagehide", finish);
  window.addEventListener("beforeunload", finish);

  window.AACScorm = {
    version: "1.2",
    status: function () {
      return JSON.parse(JSON.stringify(state));
    },
    finish: finish
  };
})();

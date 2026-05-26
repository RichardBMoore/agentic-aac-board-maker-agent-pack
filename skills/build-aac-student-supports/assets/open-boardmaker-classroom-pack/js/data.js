(function (global) {
  "use strict";

  var SCHEMA_VERSION = "0.1.0";
  var CURRENT_ACTIVITY_KEY = "open-boardmaker.currentActivity";
  var SESSION_LOG_KEY = "open-boardmaker.sessionLog";
  var ACTIVITY_LIBRARY_KEY = "open-boardmaker.activityLibrary";
  var STUDENT_PROFILES_KEY = "open-boardmaker.studentProfiles";
  var ACTIVE_STUDENT_KEY = "open-boardmaker.activeStudent";
  var ARASAAC_LICENCE = "CC BY-NC-SA";
  var ARASAAC_ATTRIBUTION = "Pictograms by ARASAAC (Government of Aragon); confirm exact source licence wording for publication.";

  function nowIso() {
    return new Date().toISOString();
  }

  function uid(prefix) {
    return prefix + "-" + Math.random().toString(36).slice(2, 8) + "-" + Date.now().toString(36);
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function safeString(value, fallback, maxLength) {
    var text = String(value == null ? fallback || "" : value)
      .replace(/[\u0000-\u001f\u007f]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    if (!text) text = fallback || "";
    if (maxLength && text.length > maxLength) text = text.slice(0, maxLength).trim();
    return text;
  }

  function safeId(value, prefix) {
    var raw = safeString(value, "", 80).toLowerCase();
    var slug = raw.replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    return slug || uid(prefix || "id");
  }

  function safeNumber(value, fallback, min, max) {
    var number = Number(value);
    if (!Number.isFinite(number)) number = fallback;
    return Math.min(max, Math.max(min, number));
  }

  function safeInteger(value, fallback, min, max) {
    return Math.round(safeNumber(value, fallback, min, max));
  }

  function safeBoolean(value, fallback) {
    return typeof value === "boolean" ? value : Boolean(fallback);
  }

  function safeColour(value, fallback) {
    var text = safeString(value, fallback, 32);
    if (/^#[0-9a-f]{3}([0-9a-f]{3})?$/i.test(text)) return text;
    if (/^(black|white|yellow|blue|green|red|transparent)$/i.test(text)) return text.toLowerCase();
    return fallback;
  }

  function safeChoice(value, allowed, fallback) {
    var text = safeString(value, fallback, 40);
    return allowed.indexOf(text) >= 0 ? text : fallback;
  }

  function safeUrl(value, fallback) {
    var text = safeString(value, fallback || "", 500);
    if (!text) return "";
    if (/^(https?:|data:image\/|blob:)/i.test(text)) return text;
    return fallback || "";
  }

  function arasaacImageUrl(id) {
    if (!id) return "";
    return "https://api.arasaac.org/api/pictograms/" + encodeURIComponent(id) + "?download=false&color=true&resolution=500";
  }

  function defaultButtonStyle(index) {
    var fills = ["#ffffff", "#fff7df", "#e8f2ff", "#eaf7ed", "#f7e9ff", "#ffece7"];
    return {
      borderColour: "#17212b",
      borderWidth: 3,
      borderStyle: "solid",
      shape: "rounded-rect",
      fillColour: fills[index % fills.length],
      gradientColour: null,
      gradientType: "none"
    };
  }

  function normaliseButtonStyle(style, index) {
    var source = style || {};
    var defaults = defaultButtonStyle(index || 0);
    return {
      borderColour: safeColour(source.borderColour, defaults.borderColour),
      borderWidth: safeInteger(source.borderWidth, defaults.borderWidth, 1, 10),
      borderStyle: safeChoice(source.borderStyle, ["solid", "dashed", "dotted", "double"], defaults.borderStyle),
      shape: safeChoice(source.shape, ["rounded-rect", "rect", "circle"], defaults.shape),
      fillColour: safeColour(source.fillColour, defaults.fillColour),
      gradientColour: source.gradientColour ? safeColour(source.gradientColour, defaults.fillColour) : null,
      gradientType: safeChoice(source.gradientType, ["none", "linear", "radial"], defaults.gradientType)
    };
  }

  function normaliseFont(font) {
    var source = font || {};
    return {
      family: safeChoice(source.family, ["Verdana", "Arial", "Helvetica", "Tahoma", "Trebuchet MS"], "Verdana"),
      size: safeInteger(source.size, 18, 12, 44),
      bold: safeBoolean(source.bold, true),
      italic: safeBoolean(source.italic, false),
      colour: safeColour(source.colour, "#000000"),
      align: safeChoice(source.align, ["left", "centre", "center", "right"], "centre")
    };
  }

  function normalisePosition(position) {
    var source = position || {};
    return {
      x: safeNumber(source.x, 0, 0, 100),
      y: safeNumber(source.y, 0, 0, 100),
      width: safeNumber(source.width, 25, 1, 100),
      height: safeNumber(source.height, 25, 1, 100)
    };
  }

  function normaliseAction(action) {
    var source = action && typeof action === "object" ? action : { type: safeString(action, "speak-label", 40) };
    var type = safeChoice(source.type, [
      "speak-label",
      "speak-text",
      "log-attempt",
      "next-page",
      "previous-page",
      "navigate-page",
      "mark-correct",
      "mark-incorrect",
      "set-variable",
      "increment-variable",
      "conditional",
      "play-audio",
      "open-url",
      "animate",
      "stay"
    ], "speak-label");
    var result = Object.assign({}, source, {
      id: safeId(source.id, "action"),
      type: type
    });
    if (result.text) result.text = safeString(result.text, "", 240);
    if (result.pageId) result.pageId = safeId(result.pageId, "page");
    if (result.name) result.name = safeString(result.name, "", 80);
    if (result.url) result.url = safeUrl(result.url, "");
    if (result.src) result.src = safeUrl(result.src, "");
    if (result.animation) result.animation = safeChoice(result.animation, ["pulse", "pop", "shake"], "pulse");
    return result;
  }

  function makeAction(type, extra) {
    var action = Object.assign({ id: uid("action"), type: type }, extra || {});
    return action;
  }

  function makeButton(config, index) {
    var source = config || {};
    var symbolId = source.symbolId ? safeString(source.symbolId, "", 80) : null;
    var label = safeString(source.label, "Button", 80);
    return {
      id: source.id ? safeId(source.id, "btn") : uid("btn"),
      type: safeChoice(source.type, ["standard", "symbolate"], "standard"),
      label: label,
      symbolId: symbolId,
      symbolSrc: safeUrl(source.symbolSrc, symbolId ? arasaacImageUrl(symbolId) : ""),
      symbolLayout: safeChoice(source.symbolLayout, ["label-bottom", "label-top", "symbol-only", "label-only", "symbolate"], "label-bottom"),
      symbolateSegments: Array.isArray(source.symbolateSegments) ? source.symbolateSegments : [],
      position: normalisePosition(source.position),
      style: normaliseButtonStyle(source.style, index || 0),
      font: normaliseFont(source.font),
      state: safeChoice(source.state, ["selectable", "disabled", "hidden"], "selectable"),
      role: safeString(source.role, "", 40),
      function: safeString(source.function, "", 40),
      searchTerm: safeString(source.searchTerm, label.toLowerCase(), 80),
      audioCue: safeString(source.audioCue, label, 120),
      result: safeChoice(source.result, ["selected", "correct", "incorrect"], "selected"),
      actions: Array.isArray(source.actions) && source.actions.length ? source.actions.map(normaliseAction) : [makeAction("speak-label"), makeAction("log-attempt")]
    };
  }

  function createGridButtons(rows, columns, labels, symbolIds) {
    var total = rows * columns;
    var buttons = [];
    for (var index = 0; index < total; index += 1) {
      var row = Math.floor(index / columns);
      var column = index % columns;
      var symbolId = symbolIds && symbolIds[index] ? String(symbolIds[index]) : null;
      buttons.push(makeButton({
        label: labels && labels[index] ? labels[index] : "Button " + (index + 1),
        symbolId: symbolId,
        position: {
          x: column * (100 / columns),
          y: row * (100 / rows),
          width: 100 / columns,
          height: 100 / rows
        }
      }, index));
    }
    return buttons;
  }

  function createGridActivity(options) {
    var config = options || {};
    var rows = Number(config.rows || 2);
    var columns = Number(config.columns || 2);
    var created = nowIso();
    return {
      schemaVersion: SCHEMA_VERSION,
      app: "Open Boardmaker",
      id: config.id || uid("activity"),
      name: config.name || "Choice Board",
      type: "interactive",
      created: created,
      modified: created,
      author: config.author || "Richard Moore",
      settings: {
        orientation: "landscape",
        width: 1024,
        height: 768,
        speakLabels: true,
        showLabels: true,
        highlightColour: "#ffeb3b",
        font: "Verdana",
        fontSize: 18,
        fontColour: "#000000",
        backgroundColour: "#ffffff",
        showStopButton: true,
        dwellTimeMs: 1200,
        switchScanning: false,
        scanSpeedMs: 1400,
        scanPattern: "linear"
      },
      accessibility: {
        intendedAccess: ["touch", "mouse", "keyboard", "eye-gaze-dwell", "switch-scanning"],
        minimumTargetSizePx: 96,
        dwellSafe: true,
        scanOrder: "dom-order",
        audioCues: true
      },
      pages: [
        {
          id: uid("page"),
          name: "Page 1",
          layout: "grid",
          gridColumns: columns,
          gridRows: rows,
          margin: 10,
          backgroundColour: "#ffffff",
          backgroundImage: null,
          buttons: createGridButtons(rows, columns, config.labels, config.symbolIds)
        }
      ],
      variables: {},
      metadata: {
        tags: ["choice-board", "prototype"],
        level: "early-years",
        curriculum: "QCIA",
        privacyLevel: "anonymous"
      },
      licences: [
        {
          source: "ARASAAC",
          licence: ARASAAC_LICENCE,
          attribution: ARASAAC_ATTRIBUTION
        }
      ]
    };
  }

  function defaultActivity() {
    var activity = createGridActivity({
      name: "Yes No Choice Board",
      rows: 2,
      columns: 2,
      labels: ["Yes", "No", "More", "Finished"],
      symbolIds: ["5584", "5526", "5508", "28429"]
    });
    activity.pages[0].buttons[0].result = "correct";
    activity.pages[0].buttons[1].result = "incorrect";
    return activity;
  }

  function normaliseActivity(input) {
    var activity = input && typeof input === "object" ? clone(input) : defaultActivity();
    activity.schemaVersion = activity.schemaVersion || SCHEMA_VERSION;
    activity.app = safeString(activity.app, "Open Boardmaker", 80);
    activity.id = activity.id ? safeId(activity.id, "activity") : uid("activity");
    activity.name = safeString(activity.name, "Untitled Activity", 120);
    activity.type = safeChoice(activity.type, ["interactive", "print"], "interactive");
    activity.created = activity.created || nowIso();
    activity.modified = nowIso();
    activity.settings = Object.assign(defaultActivity().settings, activity.settings || {});
    activity.settings.dwellTimeMs = safeInteger(activity.settings.dwellTimeMs, 1200, 500, 3000);
    activity.settings.scanSpeedMs = safeInteger(activity.settings.scanSpeedMs, 1400, 600, 3000);
    activity.settings.scanPattern = safeChoice(activity.settings.scanPattern, ["linear", "row-column"], "linear");
    activity.settings.speakLabels = safeBoolean(activity.settings.speakLabels, true);
    activity.settings.showLabels = safeBoolean(activity.settings.showLabels, true);
    activity.settings.fontColour = safeColour(activity.settings.fontColour, "#000000");
    activity.settings.backgroundColour = safeColour(activity.settings.backgroundColour, "#ffffff");
    activity.accessibility = Object.assign(defaultActivity().accessibility, activity.accessibility || {});
    activity.accessibility.minimumTargetSizePx = safeInteger(activity.accessibility.minimumTargetSizePx, 96, 44, 240);
    activity.accessibility.dwellSafe = safeBoolean(activity.accessibility.dwellSafe, true);
    activity.accessibility.audioCues = safeBoolean(activity.accessibility.audioCues, true);
    activity.metadata = Object.assign({ tags: [], level: "", curriculum: "", privacyLevel: "anonymous" }, activity.metadata || {});
    activity.metadata.privacyLevel = safeChoice(activity.metadata.privacyLevel, ["anonymous", "local-profile", "sensitive-approved"], "anonymous");
    activity.licences = Array.isArray(activity.licences) && activity.licences.length ? activity.licences.map(function (licence) {
      return {
        source: safeString(licence.source, "ARASAAC", 80),
        licence: safeString(licence.licence, ARASAAC_LICENCE, 80),
        attribution: safeString(licence.attribution || licence.note, ARASAAC_ATTRIBUTION, 220)
      };
    }) : defaultActivity().licences;
    activity.pages = Array.isArray(activity.pages) && activity.pages.length ? activity.pages : defaultActivity().pages;
    activity.pages = activity.pages.map(function (page, pageIndex) {
      var rows = safeInteger(page.gridRows, 2, 1, 8);
      var columns = safeInteger(page.gridColumns, 2, 1, 8);
      var buttons = Array.isArray(page.buttons) ? page.buttons : [];
      return {
        id: page.id ? safeId(page.id, "page") : uid("page"),
        name: safeString(page.name, "Page " + (pageIndex + 1), 100),
        layout: safeChoice(page.layout, ["grid"], "grid"),
        gridColumns: columns,
        gridRows: rows,
        margin: safeInteger(page.margin, 10, 0, 40),
        backgroundColour: safeColour(page.backgroundColour, "#ffffff"),
        backgroundImage: safeUrl(page.backgroundImage, "") || null,
        buttons: buttons.map(function (button, buttonIndex) {
          var normalised = makeButton(button, buttonIndex);
          if (normalised.symbolId && !normalised.symbolSrc) {
            normalised.symbolSrc = arasaacImageUrl(normalised.symbolId);
          }
          normalised.actions = normalised.actions && normalised.actions.length ? normalised.actions.map(normaliseAction) : [makeAction("speak-label"), makeAction("log-attempt")];
          return normalised;
        })
      };
    });
    return activity;
  }

  function saveCurrentActivity(activity) {
    var normalised = normaliseActivity(activity);
    normalised.modified = nowIso();
    localStorage.setItem(CURRENT_ACTIVITY_KEY, JSON.stringify(normalised));
    return normalised;
  }

  function loadCurrentActivity() {
    var raw = localStorage.getItem(CURRENT_ACTIVITY_KEY);
    if (!raw) return defaultActivity();
    try {
      return normaliseActivity(JSON.parse(raw));
    } catch (error) {
      console.warn("Could not load current activity", error);
      return defaultActivity();
    }
  }

  function getActivityLibrary() {
    var raw = localStorage.getItem(ACTIVITY_LIBRARY_KEY);
    if (!raw) return [];
    try {
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.warn("Could not load activity library", error);
      return [];
    }
  }

  function saveActivityLibrary(items) {
    localStorage.setItem(ACTIVITY_LIBRARY_KEY, JSON.stringify(items || []));
  }

  function listLibraryActivities() {
    return getActivityLibrary()
      .map(function (item) {
        return {
          id: item.id,
          name: item.name || "Untitled Activity",
          modified: item.modified || "",
          pages: item.activity && item.activity.pages ? item.activity.pages.length : 0
        };
      })
      .sort(function (a, b) {
        return String(b.modified).localeCompare(String(a.modified));
      });
  }

  function saveActivityToLibrary(activity) {
    var normalised = normaliseActivity(activity);
    normalised.modified = nowIso();
    var library = getActivityLibrary();
    var item = {
      id: normalised.id,
      name: normalised.name,
      modified: normalised.modified,
      activity: normalised
    };
    var index = library.findIndex(function (candidate) {
      return candidate.id === item.id;
    });
    if (index >= 0) library[index] = item;
    else library.push(item);
    saveActivityLibrary(library);
    return normalised;
  }

  function loadActivityFromLibrary(id) {
    var item = getActivityLibrary().find(function (candidate) {
      return candidate.id === id;
    });
    return item ? normaliseActivity(item.activity) : null;
  }

  function deleteActivityFromLibrary(id) {
    var library = getActivityLibrary().filter(function (candidate) {
      return candidate.id !== id;
    });
    saveActivityLibrary(library);
    return library;
  }

  function anonymousStudent() {
    return {
      id: "anonymous",
      name: "Anonymous",
      anonymous: true,
      settings: {
        dwellTimeMs: 1200,
        ttsEnabled: true,
        switchScanning: false,
        scanSpeedMs: 1400,
        scanPattern: "linear",
        contrastMode: "standard"
      }
    };
  }

  function normaliseStudent(profile) {
    var source = profile || {};
    var created = source.created || nowIso();
    return {
      id: source.id || uid("student"),
      name: String(source.name || "Student").trim() || "Student",
      anonymous: false,
      created: created,
      modified: nowIso(),
      settings: Object.assign(anonymousStudent().settings, source.settings || {})
    };
  }

  function getStudentProfiles() {
    var raw = localStorage.getItem(STUDENT_PROFILES_KEY);
    if (!raw) return [];
    try {
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed.map(normaliseStudent) : [];
    } catch (error) {
      console.warn("Could not load student profiles", error);
      return [];
    }
  }

  function saveStudentProfiles(profiles) {
    localStorage.setItem(STUDENT_PROFILES_KEY, JSON.stringify(profiles || []));
  }

  function listStudentProfiles() {
    return getStudentProfiles().sort(function (a, b) {
      return a.name.localeCompare(b.name);
    });
  }

  function saveStudentProfile(profile) {
    var normalised = normaliseStudent(profile);
    var profiles = getStudentProfiles();
    var index = profiles.findIndex(function (candidate) {
      return candidate.id === normalised.id;
    });
    if (index >= 0) profiles[index] = normalised;
    else profiles.push(normalised);
    saveStudentProfiles(profiles);
    localStorage.setItem(ACTIVE_STUDENT_KEY, normalised.id);
    return normalised;
  }

  function loadStudentProfile(id) {
    if (!id || id === "anonymous") return anonymousStudent();
    return getStudentProfiles().find(function (student) {
      return student.id === id;
    }) || anonymousStudent();
  }

  function deleteStudentProfile(id) {
    var profiles = getStudentProfiles().filter(function (student) {
      return student.id !== id;
    });
    saveStudentProfiles(profiles);
    if (localStorage.getItem(ACTIVE_STUDENT_KEY) === id) {
      localStorage.setItem(ACTIVE_STUDENT_KEY, "anonymous");
    }
    return profiles;
  }

  function setActiveStudent(id) {
    localStorage.setItem(ACTIVE_STUDENT_KEY, id || "anonymous");
    return loadStudentProfile(id);
  }

  function getActiveStudent() {
    return loadStudentProfile(localStorage.getItem(ACTIVE_STUDENT_KEY) || "anonymous");
  }

  function getSessionLog() {
    var raw = localStorage.getItem(SESSION_LOG_KEY);
    if (!raw) return [];
    try {
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.warn("Could not load session log", error);
      return [];
    }
  }

  function saveSessionLog(rows) {
    localStorage.setItem(SESSION_LOG_KEY, JSON.stringify(rows || []));
  }

  function addSessionAttempt(activity, page, button, method, result, student) {
    var rows = getSessionLog();
    var activeStudent = student || anonymousStudent();
    var entry = {
      id: uid("attempt"),
      timestamp: nowIso(),
      studentId: activeStudent.anonymous ? "" : activeStudent.id,
      studentName: activeStudent.anonymous ? "" : activeStudent.name,
      activityId: activity.id || "",
      activityName: activity.name || "Untitled Activity",
      pageId: page.id || "",
      pageName: page.name || "",
      buttonId: button.id || "",
      label: button.label || "",
      method: method || "unknown",
      result: result || button.result || "selected"
    };
    rows.push(entry);
    saveSessionLog(rows);
    return entry;
  }

  function clearSessionLog() {
    saveSessionLog([]);
  }

  function clearStudentData() {
    localStorage.removeItem(STUDENT_PROFILES_KEY);
    localStorage.removeItem(ACTIVE_STUDENT_KEY);
    localStorage.removeItem(SESSION_LOG_KEY);
  }

  function clearSessionLogForActivity(activity) {
    var activityId = activity && activity.id;
    var activityName = activity && activity.name;
    var rows = getSessionLog().filter(function (row) {
      if (activityId && row.activityId) return row.activityId !== activityId;
      return row.activityName !== activityName;
    });
    saveSessionLog(rows);
  }

  function csvEscape(value) {
    var text = value == null ? "" : String(value);
    if (/[",\n]/.test(text)) {
      return '"' + text.replace(/"/g, '""') + '"';
    }
    return text;
  }

  function sessionLogToCsv(rows) {
    var headers = ["timestamp", "studentName", "activityName", "pageName", "buttonId", "label", "method", "result"];
    var lines = [headers.join(",")];
    (rows || []).forEach(function (row) {
      lines.push(headers.map(function (header) {
        return csvEscape(row[header]);
      }).join(","));
    });
    return lines.join("\n");
  }

  function filenameFromName(name, extension) {
    var safe = String(name || "open-boardmaker")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "open-boardmaker";
    return safe + "." + extension;
  }

  global.BoardmakerData = {
    SCHEMA_VERSION: SCHEMA_VERSION,
    makeAction: makeAction,
    makeButton: makeButton,
    createGridActivity: createGridActivity,
    defaultActivity: defaultActivity,
    normaliseActivity: normaliseActivity,
    saveCurrentActivity: saveCurrentActivity,
    loadCurrentActivity: loadCurrentActivity,
    listLibraryActivities: listLibraryActivities,
    saveActivityToLibrary: saveActivityToLibrary,
    loadActivityFromLibrary: loadActivityFromLibrary,
    deleteActivityFromLibrary: deleteActivityFromLibrary,
    anonymousStudent: anonymousStudent,
    listStudentProfiles: listStudentProfiles,
    saveStudentProfile: saveStudentProfile,
    loadStudentProfile: loadStudentProfile,
    deleteStudentProfile: deleteStudentProfile,
    setActiveStudent: setActiveStudent,
    getActiveStudent: getActiveStudent,
    getSessionLog: getSessionLog,
    addSessionAttempt: addSessionAttempt,
    clearSessionLog: clearSessionLog,
    clearStudentData: clearStudentData,
    clearSessionLogForActivity: clearSessionLogForActivity,
    sessionLogToCsv: sessionLogToCsv,
    filenameFromName: filenameFromName,
    arasaacImageUrl: arasaacImageUrl,
    uid: uid,
    clone: clone
  };
})(window);

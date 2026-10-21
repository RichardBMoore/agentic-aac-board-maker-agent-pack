/* Full screen / Exit full screen button for packaged activities.
 *
 * Added by build_scorm.py --fullscreen-toggle (one extra script line after the
 * SCORM bridge line). The activity itself is not changed.
 *
 * - One compact button (a 52 px square with the full screen icon) at the edge
 *   of the activity: data-position on this script tag is top-right (default),
 *   top-left, top-center, middle-right, middle-left, bottom-right, bottom-left
 *   or bottom-center, chosen so it does not cover the activity's own controls.
 *   Hovering, looking at or focusing it shows the words "Full screen" /
 *   "Exit full screen"; that is also its accessible name. Press it to fill the
 *   whole screen; press it again, or press Escape, to go back to the lesson.
 * - Inside an LMS player on the same site (for example QLearn's SCORM player)
 *   it makes the player's activity frame full screen, so the activity stays
 *   full screen while moving between its own pages.
 * - No dead buttons: if full screen is not allowed here (the page around the
 *   activity does not permit it, or the device cannot do it), the button is
 *   not shown at all.
 * - Keyboard: a real <button>, last in the tab order, with a visible focus ring.
 *   After a mouse, touch or dwell-click press, focus goes back to where it was,
 *   so game keys (Space, arrows) keep working.
 * - Presses on this button are handled first (window capture) and kept away
 *   from the activity, so an activity's own dwell, switch-scan or click guard
 *   neither blocks the button nor reacts to it.
 * - Sends nothing anywhere and stores nothing.
 *
 * Status for teachers/QA: window.AACFullscreenToggle.status() in the console.
 */
(function () {
  "use strict";

  if (window.AACFullscreenToggle) {
    return;
  }
  var script = document.currentScript;
  var POSITIONS = {
    "top-right": 1, "top-left": 1, "top-center": 1, "middle-right": 1,
    "middle-left": 1, "bottom-right": 1, "bottom-left": 1, "bottom-center": 1
  };
  var position = script && script.getAttribute("data-position");
  if (!POSITIONS[position]) {
    position = "top-right";
  }
  var SVG = "http://www.w3.org/2000/svg";
  var ENTER_PATH = "M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5";
  var EXIT_PATH = "M9 4v5H4M15 4v5h5M20 15h-5v5M4 15h5v5";
  var button = null;
  var status = null;
  var iconPath = null;
  var label = null;
  var lastState = null;
  var focusBeforePointer = null;
  var watchedDocs = [];
  var CHANGE_EVENTS = ["fullscreenchange", "webkitfullscreenchange"];

  function fullscreenElementOf(doc) {
    try {
      return doc ? (doc.fullscreenElement || doc.webkitFullscreenElement || null) : null;
    } catch (error) {
      return null;
    }
  }

  function enabledIn(doc) {
    try {
      return Boolean(doc && (doc.fullscreenEnabled || doc.webkitFullscreenEnabled));
    } catch (error) {
      return false;
    }
  }

  function canRequest(element) {
    return Boolean(element && (element.requestFullscreen || element.webkitRequestFullscreen));
  }

  // The player's frame element, when the player is on the same site and allows full screen.
  function hostFrame() {
    try {
      var frame = window.frameElement;
      if (frame && frame.ownerDocument && enabledIn(frame.ownerDocument) && canRequest(frame)) {
        return frame;
      }
    } catch (error) {
      // A player on another site: use this page instead.
    }
    return null;
  }

  function ownRoot() {
    var root = document.documentElement;
    return enabledIn(document) && canRequest(root) ? root : null;
  }

  function relatedDocs() {
    var docs = [document];
    try {
      if (window.frameElement && window.frameElement.ownerDocument) {
        docs.push(window.frameElement.ownerDocument);
      }
    } catch (error) {
      // Cross-site parent: only this page.
    }
    return docs;
  }

  function isFull() {
    var docs = relatedDocs();
    for (var i = 0; i < docs.length; i += 1) {
      if (fullscreenElementOf(docs[i])) {
        return true;
      }
    }
    return false;
  }

  function request(element) {
    var method = element.requestFullscreen || element.webkitRequestFullscreen;
    try {
      var result = method.call(element);
      return result && typeof result.then === "function" ? result : Promise.resolve();
    } catch (error) {
      return Promise.reject(error);
    }
  }

  function exitFullscreen() {
    var docs = relatedDocs();
    for (var i = 0; i < docs.length; i += 1) {
      var doc = docs[i];
      if (fullscreenElementOf(doc)) {
        var method = doc.exitFullscreen || doc.webkitExitFullscreen;
        if (method) {
          try {
            var result = method.call(doc);
            if (result && typeof result.catch === "function") {
              result.catch(function () {});
            }
          } catch (error) {
            // Already leaving full screen.
          }
        }
        return;
      }
    }
  }

  function announce(message) {
    if (!status) {
      return;
    }
    status.textContent = "";
    window.setTimeout(function () {
      status.textContent = message;
    }, 50);
  }

  function setStyles(element, styles) {
    for (var name in styles) {
      if (Object.prototype.hasOwnProperty.call(styles, name)) {
        element.style.setProperty(name, styles[name], "important");
      }
    }
  }

  function render() {
    var on = isFull();
    var words = on ? "Exit full screen" : "Full screen";
    if (iconPath) {
      iconPath.setAttribute("d", on ? EXIT_PATH : ENTER_PATH);
    }
    if (label) {
      label.textContent = words;
    }
    if (button) {
      button.setAttribute("aria-label", words);
    }
    if (lastState !== null && lastState !== on) {
      announce(on ? "Full screen on. Press Exit full screen or Escape to go back." : "Full screen off.");
    }
    lastState = on;
  }

  function goFullscreen() {
    var frame = hostFrame();
    var root = ownRoot();
    var first = frame || root;
    if (!first) {
      announce("Full screen is not available here.");
      return;
    }
    request(first).catch(function () {
      if (frame && root) {
        return request(root);
      }
      throw new Error("blocked");
    }).catch(function () {
      announce("Full screen was blocked. Press F11, or ask a helper.");
    });
  }

  function onClick(event) {
    var viaPointer = event.detail > 0;
    if (isFull()) {
      exitFullscreen();
    } else {
      goFullscreen();
    }
    if (viaPointer) {
      var previous = focusBeforePointer;
      focusBeforePointer = null;
      button.blur();
      if (previous && previous !== document.body && previous !== button && typeof previous.focus === "function") {
        try {
          previous.focus({ preventScroll: true });
        } catch (error) {
          // Nothing to restore.
        }
      }
    }
  }

  function build() {
    button = document.createElement("button");
    button.type = "button";
    button.className = "aac-fullscreen-toggle";
    button.setAttribute("data-aac-fullscreen-toggle", position);
    var icon = document.createElementNS(SVG, "svg");
    icon.setAttribute("viewBox", "0 0 24 24");
    icon.setAttribute("width", "24");
    icon.setAttribute("height", "24");
    icon.setAttribute("aria-hidden", "true");
    icon.setAttribute("focusable", "false");
    iconPath = document.createElementNS(SVG, "path");
    iconPath.setAttribute("fill", "none");
    iconPath.setAttribute("stroke", "currentColor");
    iconPath.setAttribute("stroke-width", "2.6");
    iconPath.setAttribute("stroke-linecap", "round");
    iconPath.setAttribute("stroke-linejoin", "round");
    icon.appendChild(iconPath);
    label = document.createElement("span");
    button.appendChild(icon);
    button.appendChild(label);

    var parts = position.split("-");
    var styles = {
      position: "fixed",
      "z-index": "2147483647",
      display: "inline-flex",
      "align-items": "center",
      "justify-content": "center",
      gap: "8px",
      "min-height": "52px",
      "min-width": "52px",
      margin: "0",
      padding: "0 11px",
      background: "#134451",
      color: "#ffffff",
      border: "3px solid #ffffff",
      "border-radius": "12px",
      "box-shadow": "0 2px 10px rgba(0, 0, 0, 0.45)",
      font: "700 18px/1.1 system-ui, -apple-system, \"Segoe UI\", Arial, sans-serif",
      "letter-spacing": "0",
      "text-transform": "none",
      cursor: "pointer",
      opacity: "1",
      outline: "none",
      "box-sizing": "border-box",
      width: "auto",
      height: "auto"
    };
    if (parts[0] === "middle") {
      styles.top = "50%";
      styles.transform = "translateY(-50%)";
    } else {
      styles[parts[0]] = "8px";
    }
    if (parts[1] === "center") {
      styles.left = "50%";
      styles.transform = "translateX(-50%)";
    } else {
      styles[parts[1]] = "8px";
    }
    setStyles(button, styles);
    setStyles(icon, { width: "26px", height: "26px", flex: "0 0 26px", display: "block" });
    setStyles(label, { display: "none", "white-space": "nowrap" });

    // Compact at rest; the words show while it is hovered, looked at (gaze pointer) or focused.
    function showWords(show) {
      setStyles(label, { display: show ? "inline" : "none" });
    }
    // Handled at window capture, before any activity listener: some activities guard every click
    // on the document (dwell or switch-scan engines) and would otherwise swallow or react to these.
    function isOurs(event) {
      return Boolean(button && event.target && (event.target === button || button.contains(event.target)));
    }
    window.addEventListener("pointerdown", function (event) {
      if (isOurs(event)) {
        focusBeforePointer = document.activeElement;
        event.stopPropagation();
      }
    }, true);
    ["pointerup", "mousedown", "mouseup", "touchstart", "touchend"].forEach(function (type) {
      window.addEventListener(type, function (event) {
        if (isOurs(event)) {
          event.stopPropagation();
        }
      }, { capture: true, passive: true });
    });
    ["keydown", "keyup"].forEach(function (type) {
      window.addEventListener(type, function (event) {
        if (isOurs(event) && (event.key === "Enter" || event.key === " " || event.key === "Spacebar")) {
          event.stopPropagation();
        }
      }, true);
    });
    window.addEventListener("click", function (event) {
      if (isOurs(event)) {
        event.stopPropagation();
        onClick(event);
      }
    }, true);
    var hovered = false;
    var focused = false;
    button.addEventListener("focus", function () {
      focused = true;
      setStyles(button, { outline: "4px solid #ffbf47", "outline-offset": "2px" });
      showWords(true);
    });
    button.addEventListener("blur", function () {
      focused = false;
      setStyles(button, { outline: "none" });
      showWords(hovered);
    });
    button.addEventListener("mouseenter", function () {
      hovered = true;
      setStyles(button, { background: "#1d6475" });
      showWords(true);
    });
    button.addEventListener("mouseleave", function () {
      hovered = false;
      setStyles(button, { background: "#134451" });
      showWords(focused);
    });

    status = document.createElement("div");
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.setAttribute("data-aac-fullscreen-status", "");
    setStyles(status, {
      position: "absolute",
      width: "1px",
      height: "1px",
      margin: "-1px",
      padding: "0",
      overflow: "hidden",
      clip: "rect(0 0 0 0)",
      "white-space": "nowrap",
      border: "0"
    });
    render();
  }

  function attach() {
    if (!document.body) {
      return;
    }
    if (!button.isConnected) {
      document.body.appendChild(button);
    }
    if (!status.isConnected) {
      document.body.appendChild(status);
    }
  }

  function watch() {
    relatedDocs().forEach(function (doc) {
      CHANGE_EVENTS.forEach(function (type) {
        doc.addEventListener(type, render);
      });
      watchedDocs.push(doc);
    });
    window.addEventListener("pagehide", function () {
      // The player's page outlives this page in multi-page activities: stop listening there.
      watchedDocs.forEach(function (doc) {
        CHANGE_EVENTS.forEach(function (type) {
          try {
            doc.removeEventListener(type, render);
          } catch (error) {
            // Already gone.
          }
        });
      });
      watchedDocs = [];
    });
    window.addEventListener("beforeprint", function () {
      setStyles(button, { display: "none" });
    });
    window.addEventListener("afterprint", function () {
      setStyles(button, { display: "inline-flex" });
    });
    if (window.MutationObserver && document.body) {
      // Some activities rebuild their page; put the button back if it is removed.
      new MutationObserver(attach).observe(document.body, { childList: true });
    }
  }

  function start() {
    if (!hostFrame() && !ownRoot()) {
      return; // Full screen is not allowed here: show no button rather than one that does nothing.
    }
    build();
    attach();
    watch();
  }

  window.AACFullscreenToggle = {
    status: function () {
      return {
        shown: Boolean(button && button.isConnected),
        position: position,
        target: hostFrame() ? "player frame" : (ownRoot() ? "this page" : "none"),
        fullscreen: isFull()
      };
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();

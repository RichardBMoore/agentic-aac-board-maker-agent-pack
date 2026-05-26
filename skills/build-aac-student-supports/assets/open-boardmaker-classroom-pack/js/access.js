(function (global) {
  "use strict";

  function closestButton(target) {
    return target && target.closest ? target.closest("[data-button-id]") : null;
  }

  function createController(options) {
    var config = options || {};
    var activeElement = null;
    var frame = null;
    var startedAt = 0;
    var completedFor = null;

    function dwellMs() {
      return Number(config.getDwellTime ? config.getDwellTime() : config.dwellTime || 1200);
    }

    function dwellEnabled() {
      return config.isDwellEnabled ? config.isDwellEnabled() : config.dwellEnabled !== false;
    }

    function cancelDwell() {
      if (frame) cancelAnimationFrame(frame);
      frame = null;
      if (activeElement) {
        activeElement.classList.remove("is-dwelling");
        activeElement.style.setProperty("--dwell-progress", "0");
      }
      activeElement = null;
      startedAt = 0;
    }

    function activate(element, method) {
      if (!element || element.getAttribute("aria-disabled") === "true") return;
      if (config.onActivate) {
        config.onActivate(element.dataset.buttonId, method || "unknown");
      }
    }

    function tick() {
      if (!activeElement) return;
      var elapsed = performance.now() - startedAt;
      var progress = Math.min(1, elapsed / dwellMs());
      activeElement.style.setProperty("--dwell-progress", String(Math.round(progress * 100)));
      if (progress >= 1) {
        var element = activeElement;
        completedFor = element.dataset.buttonId;
        cancelDwell();
        activate(element, "dwell");
        setTimeout(function () {
          if (completedFor === element.dataset.buttonId) completedFor = null;
        }, 400);
        return;
      }
      frame = requestAnimationFrame(tick);
    }

    function startDwell(element) {
      if (!dwellEnabled() || !element || element.dataset.buttonId === completedFor) return;
      cancelDwell();
      activeElement = element;
      startedAt = performance.now();
      element.classList.add("is-dwelling");
      element.style.setProperty("--dwell-progress", "0");
      frame = requestAnimationFrame(tick);
    }

    function moveFocus(container, delta) {
      var buttons = Array.prototype.slice.call(container.querySelectorAll("[data-button-id]:not([aria-disabled='true'])"));
      if (!buttons.length) return;
      var current = document.activeElement;
      var index = buttons.indexOf(current);
      var next = index < 0 ? 0 : (index + delta + buttons.length) % buttons.length;
      buttons[next].focus();
    }

    function bind(container) {
      container.addEventListener("click", function (event) {
        var button = closestButton(event.target);
        if (button && completedFor !== button.dataset.buttonId) {
          activate(button, "mouse-touch");
        }
      });

      container.addEventListener("pointerenter", function (event) {
        var button = closestButton(event.target);
        if (button) startDwell(button);
      }, true);

      container.addEventListener("pointerleave", function (event) {
        if (closestButton(event.target)) cancelDwell();
      }, true);

      container.addEventListener("focusout", function (event) {
        if (closestButton(event.target)) cancelDwell();
      }, true);

      container.addEventListener("keydown", function (event) {
        if (config.shouldHandleKeyboard && !config.shouldHandleKeyboard(event)) return;
        var button = closestButton(event.target);
        if (event.key === "ArrowRight" || event.key === "ArrowDown") {
          event.preventDefault();
          moveFocus(container, 1);
        }
        if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
          event.preventDefault();
          moveFocus(container, -1);
        }
        if (button && (event.key === "Enter" || event.key === " ")) {
          event.preventDefault();
          activate(button, "keyboard");
        }
      });

      global.addEventListener("blur", cancelDwell);
      document.addEventListener("visibilitychange", function () {
        if (document.visibilityState !== "visible") cancelDwell();
      });
    }

    return {
      bind: bind,
      cancelDwell: cancelDwell
    };
  }

  function createScanner(options) {
    var config = options || {};
    var container = null;
    var timer = null;
    var index = -1;
    var rowIndex = -1;
    var columnIndex = -1;
    var rowColumnPhase = "rows";
    var active = false;

    function enabled() {
      return config.isEnabled ? config.isEnabled() : false;
    }

    function speedMs() {
      return Number(config.getSpeed ? config.getSpeed() : config.speedMs || 1400);
    }

    function pattern() {
      return config.getPattern ? config.getPattern() : "linear";
    }

    function columns() {
      return Math.max(1, Number(config.getColumns ? config.getColumns() : 1));
    }

    function buttons() {
      if (!container) return [];
      return Array.prototype.slice.call(container.querySelectorAll("[data-button-id]:not([aria-disabled='true'])"));
    }

    function clearCurrent() {
      buttons().forEach(function (button) {
        button.classList.remove("is-scan-current", "is-scan-row-current");
      });
    }

    function currentButton() {
      var available = buttons();
      if (!available.length || index < 0) return null;
      return available[index % available.length];
    }

    function rowCount(available) {
      return Math.max(1, Math.ceil(available.length / columns()));
    }

    function currentRowLength(available) {
      return Math.max(1, Math.min(columns(), available.length - rowIndex * columns()));
    }

    function focusElement(element) {
      if (!element || !element.focus) return;
      try {
        element.focus({ preventScroll: true });
      } catch (error) {
        element.focus();
      }
    }

    function highlightLinear(available) {
      index = (index + 1) % available.length;
      available[index].classList.add("is-scan-current");
      focusElement(available[index]);
      cue(available[index]);
    }

    function highlightRow(available) {
      var start = rowIndex * columns();
      var end = Math.min(start + columns(), available.length);
      for (var rowItem = start; rowItem < end; rowItem += 1) {
        available[rowItem].classList.add("is-scan-row-current");
      }
      index = start;
      focusElement(available[start]);
      cue(available[start]);
    }

    function cue(element) {
      if (!element || !config.onCue) return;
      config.onCue(element.dataset.buttonId);
    }

    function step() {
      var available = buttons();
      if (!available.length) return;
      clearCurrent();
      if (pattern() !== "row-column") {
        highlightLinear(available);
        return;
      }
      if (rowColumnPhase === "rows") {
        rowIndex = (rowIndex + 1) % rowCount(available);
        columnIndex = -1;
        highlightRow(available);
        return;
      }
      columnIndex = (columnIndex + 1) % currentRowLength(available);
      index = rowIndex * columns() + columnIndex;
      available[index].classList.add("is-scan-current");
      focusElement(available[index]);
      cue(available[index]);
    }

    function schedule() {
      stopTimer();
      if (!active || !enabled()) return;
      timer = setInterval(step, speedMs());
    }

    function stopTimer() {
      if (timer) clearInterval(timer);
      timer = null;
    }

    function start() {
      if (!enabled()) return;
      active = true;
      if (index < 0) step();
      schedule();
      if (config.onStateChange) config.onStateChange(active);
    }

    function stop() {
      active = false;
      stopTimer();
      clearCurrent();
      reset();
      if (config.onStateChange) config.onStateChange(active);
    }

    function toggle() {
      if (active) stop();
      else start();
    }

    function select(method) {
      if (pattern() === "row-column" && rowColumnPhase === "rows") {
        rowColumnPhase = "cells";
        columnIndex = -1;
        step();
        schedule();
        return;
      }
      var element = currentButton();
      if (!element || !config.onActivate) return;
      config.onActivate(element.dataset.buttonId, method || "switch");
      if (pattern() === "row-column") {
        rowColumnPhase = "rows";
        rowIndex = -1;
        columnIndex = -1;
        if (active) step();
      }
    }

    function refresh() {
      var available = buttons();
      clearCurrent();
      if (!available.length) {
        reset();
        stopTimer();
        return;
      }
      if (index >= available.length) index = 0;
      if (active && enabled()) {
        if (pattern() === "row-column" && rowColumnPhase === "rows" && rowIndex >= 0) {
          highlightRow(available);
        } else if (index >= 0) {
          available[Math.max(0, index)].classList.add("is-scan-current");
        }
        schedule();
      }
    }

    function reset() {
      index = -1;
      rowIndex = -1;
      columnIndex = -1;
      rowColumnPhase = "rows";
    }

    function onKeydown(event) {
      var tagName = event.target && event.target.tagName ? event.target.tagName.toLowerCase() : "";
      if (!enabled() || tagName === "input" || tagName === "textarea" || tagName === "select") return;
      if (event.key === "Escape") {
        event.preventDefault();
        stop();
      }
      if (event.key === "s" || event.key === "S") {
        event.preventDefault();
        step();
      }
      if (event.key === " " || event.key === "Enter") {
        if (!active && !currentButton()) return;
        event.preventDefault();
        select("switch");
      }
    }

    function bind(target) {
      container = target;
      document.addEventListener("keydown", onKeydown);
    }

    return {
      bind: bind,
      refresh: refresh,
      start: start,
      stop: stop,
      toggle: toggle,
      step: step,
      select: select,
      reset: reset,
      isActive: function () {
        return active;
      }
    };
  }

  global.BoardmakerAccess = {
    createController: createController,
    createScanner: createScanner
  };
})(window);

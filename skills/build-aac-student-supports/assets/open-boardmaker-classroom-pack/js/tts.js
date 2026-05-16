(function (global) {
  "use strict";

  var enabled = true;

  function supported() {
    return "speechSynthesis" in global && "SpeechSynthesisUtterance" in global;
  }

  function setEnabled(value) {
    enabled = Boolean(value);
    if (!enabled) stop();
  }

  function stop() {
    if (supported()) {
      global.speechSynthesis.cancel();
    }
  }

  function speak(text, options) {
    var settings = options || {};
    var phrase = String(text || "").trim();
    if (!enabled || !phrase || !supported()) return;
    if (settings.interrupt !== false) stop();
    var utterance = new SpeechSynthesisUtterance(phrase);
    utterance.lang = settings.lang || "en-AU";
    utterance.rate = Number(settings.rate || 0.92);
    utterance.pitch = Number(settings.pitch || 1);
    utterance.volume = Number(settings.volume || 1);
    global.speechSynthesis.speak(utterance);
  }

  global.BoardmakerTts = {
    supported: supported,
    setEnabled: setEnabled,
    speak: speak,
    stop: stop
  };
})(window);

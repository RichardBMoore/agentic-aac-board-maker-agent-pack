(function (global) {
  "use strict";

  function downloadText(text, filename, type) {
    var blob = new Blob([text], { type: type || "text/plain" });
    var url = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function downloadJson(activity) {
    var data = global.BoardmakerData.normaliseActivity(activity);
    var filename = global.BoardmakerData.filenameFromName(data.name, "json");
    downloadText(JSON.stringify(data, null, 2), filename, "application/json");
  }

  function downloadCsv(rows, activityName) {
    var csv = global.BoardmakerData.sessionLogToCsv(rows || []);
    var filename = global.BoardmakerData.filenameFromName((activityName || "session") + "-attempts", "csv");
    downloadText(csv, filename, "text/csv");
  }

  function readJsonFile(file) {
    return new Promise(function (resolve, reject) {
      if (!file) {
        reject(new Error("No file selected"));
        return;
      }
      var reader = new FileReader();
      reader.onload = function () {
        try {
          resolve(JSON.parse(String(reader.result || "{}")));
        } catch (error) {
          reject(error);
        }
      };
      reader.onerror = function () {
        reject(reader.error || new Error("Could not read file"));
      };
      reader.readAsText(file);
    });
  }

  function bindJsonInput(input, onLoad, onError) {
    input.addEventListener("change", function () {
      var file = input.files && input.files[0];
      readJsonFile(file)
        .then(onLoad)
        .catch(function (error) {
          if (onError) onError(error);
        })
        .finally(function () {
          input.value = "";
        });
    });
  }

  global.BoardmakerFileIO = {
    downloadText: downloadText,
    downloadJson: downloadJson,
    downloadCsv: downloadCsv,
    readJsonFile: readJsonFile,
    bindJsonInput: bindJsonInput
  };
})(window);

(function (global) {
  "use strict";

  var SEARCH_CACHE_KEY = "open-boardmaker.symbolSearchCache";
  var DB_NAME = "open-boardmaker-symbol-cache";
  var DB_VERSION = 1;
  var SYMBOL_STORE = "symbols";

  function getCache() {
    try {
      return JSON.parse(localStorage.getItem(SEARCH_CACHE_KEY) || "{}");
    } catch (error) {
      return {};
    }
  }

  function setCache(cache) {
    try {
      localStorage.setItem(SEARCH_CACHE_KEY, JSON.stringify(cache));
    } catch (error) {
      console.warn("Could not cache symbol search", error);
    }
  }

  function resultLabel(item) {
    var keywords = Array.isArray(item.keywords) ? item.keywords : [];
    var keyword = keywords.find(function (entry) {
      return entry.keyword;
    });
    return keyword ? keyword.keyword : "ARASAAC " + item._id;
  }

  function mapResult(item) {
    return {
      id: String(item._id),
      label: resultLabel(item),
      imageUrl: global.BoardmakerData.arasaacImageUrl(item._id),
      source: "ARASAAC",
      licence: "CC BY-NC-SA",
      attribution: "Pictograms by ARASAAC (Government of Aragon)"
    };
  }

  function searchArasaac(term) {
    var query = String(term || "").trim().toLowerCase();
    if (!query) return Promise.resolve([]);
    var cache = getCache();
    if (cache[query]) return Promise.resolve(cache[query]);

    var url = "https://api.arasaac.org/api/pictograms/en/search/" + encodeURIComponent(query);
    return fetch(url)
      .then(function (response) {
        if (!response.ok) throw new Error("ARASAAC search failed");
        return response.json();
      })
      .then(function (data) {
        var results = Array.isArray(data) ? data.slice(0, 12).map(mapResult) : [];
        cache[query] = results;
        setCache(cache);
        return results;
      });
  }

  function openDb() {
    if (!global.indexedDB) return Promise.reject(new Error("IndexedDB unavailable"));
    return new Promise(function (resolve, reject) {
      var request = global.indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = function () {
        var db = request.result;
        if (!db.objectStoreNames.contains(SYMBOL_STORE)) {
          db.createObjectStore(SYMBOL_STORE, { keyPath: "key" });
        }
      };
      request.onsuccess = function () {
        resolve(request.result);
      };
      request.onerror = function () {
        reject(request.error || new Error("Could not open symbol cache"));
      };
    });
  }

  function withStore(mode, callback) {
    return openDb().then(function (db) {
      return new Promise(function (resolve, reject) {
        var transaction = db.transaction(SYMBOL_STORE, mode);
        var store = transaction.objectStore(SYMBOL_STORE);
        var request;
        try {
          request = callback(store);
        } catch (error) {
          reject(error);
          db.close();
          return;
        }
        transaction.oncomplete = function () {
          resolve(request && "result" in request ? request.result : undefined);
          db.close();
        };
        transaction.onerror = function () {
          reject(transaction.error || new Error("Symbol cache failed"));
          db.close();
        };
      });
    });
  }

  function symbolKey(id) {
    return "arasaac:" + String(id || "").trim();
  }

  function blobToDataUrl(blob) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onload = function () {
        resolve(String(reader.result || ""));
      };
      reader.onerror = function () {
        reject(reader.error || new Error("Could not read symbol image"));
      };
      reader.readAsDataURL(blob);
    });
  }

  function getCachedSymbol(id) {
    if (!id) return Promise.resolve(null);
    return withStore("readonly", function (store) {
      return store.get(symbolKey(id));
    }).catch(function () {
      return null;
    });
  }

  function putCachedSymbol(entry) {
    if (!entry || !entry.key || !entry.dataUrl) return Promise.resolve(null);
    return withStore("readwrite", function (store) {
      return store.put(entry);
    }).then(function () {
      return entry;
    }).catch(function () {
      return null;
    });
  }

  function cacheImage(result) {
    var item = result || {};
    var id = item.id || item.symbolId;
    if (!id) return Promise.resolve(item);
    return getCachedSymbol(id).then(function (cached) {
      if (cached && cached.dataUrl) {
        return Object.assign({}, item, {
          cachedUrl: cached.dataUrl
        });
      }
      var url = item.imageUrl || imageUrl(id);
      if (!url || /^data:/i.test(url) || !global.fetch) return item;
      return fetch(url, { cache: "force-cache" })
        .then(function (response) {
          if (!response.ok) throw new Error("Could not fetch symbol image");
          return response.blob();
        })
        .then(blobToDataUrl)
        .then(function (dataUrl) {
          return putCachedSymbol({
            key: symbolKey(id),
            id: String(id),
            dataUrl: dataUrl,
            imageUrl: url,
            label: item.label || "",
            source: item.source || "ARASAAC",
            licence: item.licence || "CC BY-NC-SA",
            cachedAt: new Date().toISOString()
          }).then(function () {
            return Object.assign({}, item, {
              cachedUrl: dataUrl
            });
          });
        })
        .catch(function () {
          return item;
        });
    });
  }

  function imageUrl(id) {
    return global.BoardmakerData.arasaacImageUrl(id);
  }

  function symbolIdsForActivity(activity) {
    var seen = {};
    var ids = [];
    ((activity && activity.pages) || []).forEach(function (page) {
      (page.buttons || []).forEach(function (button) {
        [button].concat(Array.isArray(button.symbolateSegments) ? button.symbolateSegments : []).forEach(function (item) {
          var id = String(item.symbolId || "").trim();
          if (!id || id.indexOf("custom-") === 0 || seen[id]) return;
          seen[id] = true;
          ids.push(id);
        });
      });
    });
    return ids;
  }

  function countActivityCached(activity) {
    var ids = symbolIdsForActivity(activity);
    if (!ids.length) {
      return Promise.resolve({ total: 0, cached: 0, missing: 0 });
    }
    return Promise.all(ids.map(getCachedSymbol)).then(function (rows) {
      var cached = rows.filter(function (row) {
        return row && row.dataUrl;
      }).length;
      return {
        total: ids.length,
        cached: cached,
        missing: ids.length - cached
      };
    });
  }

  function cacheActivity(activity, onProgress) {
    var ids = symbolIdsForActivity(activity);
    var cached = 0;
    var failed = 0;
    return ids.reduce(function (chain, id, index) {
      return chain.then(function () {
        return cacheImage({
          id: id,
          label: "ARASAAC " + id,
          imageUrl: imageUrl(id),
          source: "ARASAAC",
          licence: "CC BY-NC-SA",
          attribution: "Pictograms by ARASAAC (Government of Aragon)"
        }).then(function (result) {
          if (result.cachedUrl) cached += 1;
          else failed += 1;
          if (onProgress) onProgress({ total: ids.length, done: index + 1, cached: cached, failed: failed });
        });
      });
    }, Promise.resolve()).then(function () {
      return {
        total: ids.length,
        cached: cached,
        failed: failed
      };
    });
  }

  function hydrateImages(root) {
    if (!root || !root.querySelectorAll) return Promise.resolve();
    var images = Array.prototype.slice.call(root.querySelectorAll("img[data-symbol-id]"));
    return Promise.all(images.map(function (img) {
      var id = img.getAttribute("data-symbol-id");
      return getCachedSymbol(id).then(function (cached) {
        if (cached && cached.dataUrl && img.src !== cached.dataUrl) {
          img.src = cached.dataUrl;
        }
      });
    }));
  }

  function checkStatus() {
    if (navigator.onLine === false) {
      return Promise.resolve({ ok: false, message: "Browser offline" });
    }
    var controller = global.AbortController ? new AbortController() : null;
    var timeout = controller ? global.setTimeout(function () {
      controller.abort();
    }, 3500) : null;
    return fetch("https://api.arasaac.org/api/pictograms/en/search/yes", {
      cache: "no-store",
      signal: controller ? controller.signal : undefined
    }).then(function (response) {
      return {
        ok: response.ok,
        message: response.ok ? "ARASAAC reachable" : "ARASAAC returned " + response.status
      };
    }).catch(function () {
      return { ok: false, message: "ARASAAC blocked or offline" };
    }).then(function (result) {
      if (timeout) global.clearTimeout(timeout);
      return result;
    });
  }

  global.BoardmakerSymbols = {
    searchArasaac: searchArasaac,
    checkStatus: checkStatus,
    cacheImage: cacheImage,
    cacheActivity: cacheActivity,
    countActivityCached: countActivityCached,
    getCachedSymbol: getCachedSymbol,
    hydrateImages: hydrateImages,
    imageUrl: imageUrl
  };
})(window);

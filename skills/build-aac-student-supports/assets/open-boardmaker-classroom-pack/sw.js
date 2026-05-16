const CACHE_NAME = "open-boardmaker-v0-13-0";
const APP_SHELL = [
  "./",
  "./index.html",
  "./player.html",
  "./manifest.webmanifest",
  "./icons/open-boardmaker.svg",
  "./css/editor.css",
  "./css/player.css",
  "./css/print.css",
  "./js/data.js",
  "./js/file-io.js",
  "./js/symbols.js",
  "./js/tts.js",
  "./js/actions.js",
  "./js/access.js",
  "./js/editor.js",
  "./js/player.js",
  "./templates/yes-no-choice.json",
  "./templates/choice-board-9.json",
  "./templates/visual-schedule.json",
  "./templates/first-then.json",
  "./templates/book-reader.json",
  "./templates/quiz-4.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached && event.request.cache !== "no-store") return cached;
      return fetch(event.request).then((response) => {
        if (!response || (response.status !== 200 && response.type !== "opaque")) return response;
        if (event.request.cache !== "no-store") {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        }
        return response;
      }).catch(() => cached || new Response("Offline", { status: 503, statusText: "Offline" }));
    })
  );
});

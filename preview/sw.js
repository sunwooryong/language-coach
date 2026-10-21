/* RYONG 베트남어 서비스워커 — 앱 셸 선캐시 + 음성 런타임 캐시 */
var VER = "ryong-v8";
var SHELL = "shell-" + VER;
var MEDIA = "media-" + VER;
var SHELL_FILES = [
  "./",
  "./index.html",
  "./live-data.js?v=8",
  "./word-bank.js?v=8",
  "./sentence-bank.js?v=8",
  "./advanced-content.js?v=8",
  "./audio/manifest.json?v=8",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png"
];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(SHELL).then(function (c) {
    return Promise.allSettled(SHELL_FILES.map(function (u) { return c.add(u); }));
  }).then(function(){ return self.skipWaiting(); }));
});

self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.map(function (k) {
      if (k !== SHELL && k !== MEDIA) return caches.delete(k);
    }));
  }).then(function(){ return self.clients.claim(); }));
});

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // audio mp3: cache-first, store on fetch (offline after first listen)
  if (url.pathname.indexOf("/audio/") > -1 && url.pathname.endsWith(".mp3")) {
    e.respondWith(caches.open(MEDIA).then(function (c) {
      return c.match(req).then(function (hit) {
        if (hit) return hit;
        return fetch(req).then(function (res) { if (res && res.ok) c.put(req, res.clone()); return res; });
      });
    }));
    return;
  }

  // app shell & data: cache-first, revalidate in background
  e.respondWith(caches.match(req).then(function (hit) {
    var net = fetch(req).then(function (res) {
      if (res && res.ok) caches.open(SHELL).then(function (c) { c.put(req, res.clone()); });
      return res;
    }).catch(function () { return hit; });
    return hit || net;
  }));
});

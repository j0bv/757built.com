const CACHE_NAME = '757built-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json'
  // Add other core files here if needed
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});

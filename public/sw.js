/**
 * Offline support (plan §6.3 PWA): network-first for pages, falling back
 * to cache — many students study on unreliable data. Visited pages and
 * assets stay available offline.
 */
const CACHE = 'adhyayan-v2';
const CORE = ['/', '/practice/', '/practice/quiz/', '/practice/flashcards/', '/dashboard/'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(CORE)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET' || new URL(request.url).origin !== location.origin) return;

  event.respondWith(
    fetch(request)
      .then((response) => {
        // Only cache full, successful responses — a transient 404/500 must not
        // overwrite a good cached copy, and cache.put() rejects on 206 partials.
        if (response.ok && response.status !== 206) {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put(request, copy));
        }
        return response;
      })
      .catch(() =>
        caches.match(request).then((cached) => {
          if (cached) return cached;
          // Falling back to '/' is only sane for page navigations; serving
          // HTML in place of a missed CSS/JS asset breaks the page outright.
          if (request.mode === 'navigate') return caches.match('/');
          return Response.error();
        })
      )
  );
});

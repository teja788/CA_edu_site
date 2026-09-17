/**
 * Offline support (plan §6.3 PWA): network-first for pages, falling back
 * to cache — many students study on unreliable data. Visited pages and
 * assets stay available offline.
 *
 * Two caches, on purpose:
 *  - PRECACHE holds the app shell (shell routes + the hashed, immutable
 *    CSS/JS in /_astro/). It is filled at install time so the site works on a
 *    cold offline start, and its name carries a build hash so a new build
 *    replaces it wholesale. scripts/sw_precache/generate_sw.js fills in the
 *    two placeholders below at build time; in `astro dev` they stay as-is and
 *    the worker simply falls back to the old CORE behaviour.
 *  - RUNTIME holds whatever the student actually visits (chapter pages, the
 *    search index, question-bank JSON). Its name is deliberately NOT
 *    versioned: wiping it on every deploy would take away the offline library
 *    someone built up by reading. Chapter pages are never precached — 46+ of
 *    them plus the Pagefind index would be a brutal first-visit download on
 *    mobile data.
 */
const PRECACHE_VERSION = '__PRECACHE_VERSION__';
const PRECACHE_URLS = [/* __PRECACHE_MANIFEST__ */];

const PRECACHE = 'adhyayan-precache-' + PRECACHE_VERSION;
const RUNTIME = 'adhyayan-v2';
const CORE = ['/', '/practice/', '/practice/quiz/', '/practice/flashcards/', '/dashboard/'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    (PRECACHE_URLS.length
      ? caches.open(PRECACHE).then((cache) =>
          // One-by-one rather than addAll(): a single stale or missing entry
          // must not abort the whole install and leave the user with no shell.
          Promise.all(PRECACHE_URLS.map((url) => cache.add(url).catch(() => {})))
        )
      : // Unprocessed template (dev server): keep the pre-precache behaviour.
        caches.open(RUNTIME).then((cache) => Promise.all(CORE.map((url) => cache.add(url).catch(() => {}))))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          // Drop superseded precaches; never touch RUNTIME, which is the
          // student's accumulated offline reading.
          keys.filter((k) => k !== PRECACHE && k !== RUNTIME).map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  // Same-origin GETs only. This deliberately leaves analytics alone: the
  // GoatCounter script (gc.zgo.at) and its count pixel are cross-origin, so
  // they are never intercepted, cached, or replayed from cache offline.
  // Keep this guard if the handler is ever widened.
  if (request.method !== 'GET' || new URL(request.url).origin !== location.origin) return;

  // Hashed build assets are immutable — the filename changes when the bytes
  // change — so serve them cache-first. This is where the offline win is: no
  // network round trip for CSS/JS on a flaky connection.
  if (new URL(request.url).pathname.startsWith('/_astro/')) {
    event.respondWith(
      caches.match(request).then(
        (cached) =>
          cached ||
          fetch(request).then((response) => {
            if (response.ok && response.status !== 206) {
              const copy = response.clone();
              caches.open(RUNTIME).then((cache) => cache.put(request, copy));
            }
            return response;
          })
      ).catch(() => Response.error())
    );
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => {
        // Only cache full, successful responses — a transient 404/500 must not
        // overwrite a good cached copy, and cache.put() rejects on 206 partials.
        if (response.ok && response.status !== 206) {
          const copy = response.clone();
          caches.open(RUNTIME).then((cache) => cache.put(request, copy));
        }
        return response;
      })
      .catch(() =>
        // caches.match() with no cache name searches every cache, so a
        // precached shell route answers here just as a visited page does.
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

/**
 * Service worker — minimal offline-read cache.
 *
 * Strategy:
 * - App shell (HTML, JS, CSS, icons): stale-while-revalidate.
 * - Static surahs catalog (rarely changes): cache-first.
 * - Other API GETs (students, progress, etc.): network-first with cache fallback,
 *   so users keep seeing the most recent data when offline.
 * - All non-GET (POST/PUT/DELETE): network-only. We do NOT queue them — the
 *   user gets a clean failure that the OfflineBanner explains. A real offline
 *   write queue (IndexedDB + Background Sync) is a separate, bigger slice.
 *
 * Bump CACHE_VERSION whenever the shell or strategies change so old caches
 * are evicted on the next service worker install.
 */
const CACHE_VERSION = "qp-v1";
const SHELL_CACHE = `${CACHE_VERSION}-shell`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;

const SHELL_PATHS = ["/", "/dashboard", "/students", "/matrix", "/notifications"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(SHELL_CACHE)
      .then((cache) => cache.addAll(SHELL_PATHS).catch(() => undefined))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => !k.startsWith(CACHE_VERSION))
            .map((k) => caches.delete(k)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle same-origin GETs. CORS GETs to the API host are also handled
  // (api.example.com or :8000); we cache them as opaque-ok responses.
  if (request.method !== "GET") return;

  const isApi = url.pathname.startsWith("/api/v1");

  // Surahs catalog: static, cache-first.
  if (isApi && /\/api\/v1\/surahs(\/|$)/.test(url.pathname)) {
    event.respondWith(cacheFirst(request, RUNTIME_CACHE));
    return;
  }

  // Other API GETs: network-first, fall back to cache.
  if (isApi) {
    event.respondWith(networkFirst(request, RUNTIME_CACHE));
    return;
  }

  // Shell + static assets: stale-while-revalidate.
  if (request.destination === "document" || /\.(css|js|woff2?|png|svg|ico)$/.test(url.pathname)) {
    event.respondWith(staleWhileRevalidate(request, SHELL_CACHE));
    return;
  }
});

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) {
    const cache = await caches.open(cacheName);
    cache.put(request, response.clone());
  }
  return response;
}

async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (e) {
    const cached = await caches.match(request);
    if (cached) return cached;
    throw e;
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const fetchPromise = fetch(request)
    .then((response) => {
      if (response.ok) cache.put(request, response.clone());
      return response;
    })
    .catch(() => cached);
  return cached || fetchPromise;
}

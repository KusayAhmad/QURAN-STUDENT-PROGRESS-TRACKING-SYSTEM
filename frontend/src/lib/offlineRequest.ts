/**
 * Wrapper that intercepts network failures on mutations and queues them
 * for offline replay instead of throwing to the caller.
 *
 * Usage: replace direct `fetch()` in api.ts's `request()` with this for
 * non-GET methods. GETs are never queued (they're served from SW cache).
 */

import { enqueue } from "@/lib/offlineQueue";

/**
 * Returns true if the error looks like a network failure (fetch threw,
 * not an HTTP error response).
 */
function isNetworkError(err: unknown): boolean {
  if (err instanceof TypeError && /fetch|network/i.test(err.message)) return true;
  // Some browsers throw DOMException for AbortError on network drop.
  if (err instanceof DOMException && err.name === "AbortError") return true;
  return false;
}

/**
 * Attempts a fetch. If it fails due to a network error AND navigator is
 * offline, enqueues the request and returns a synthetic "queued" response.
 * Otherwise re-throws so the caller can handle real errors.
 */
export async function fetchWithOfflineQueue(
  url: string,
  init: RequestInit,
): Promise<Response | "QUEUED"> {
  try {
    return await fetch(url, init);
  } catch (err) {
    const offline =
      typeof navigator !== "undefined" && !navigator.onLine;
    if (offline && isNetworkError(err)) {
      // Extract the path relative to the API base for replay.
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const path = url.replace(`${baseUrl}/api/v1`, "");

      await enqueue({
        path,
        method: init.method ?? "POST",
        headers: (init.headers as Record<string, string>) ?? {},
        body: typeof init.body === "string" ? init.body : null,
        createdAt: Date.now(),
      });

      return "QUEUED";
    }
    throw err;
  }
}

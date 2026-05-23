"use client";

import { useOnlineStatus } from "./PWAClient";

/**
 * Slim red banner that appears when the browser reports offline.
 * Reads work from cache; mutations will fail loudly (no offline queue yet).
 */
export function OfflineBanner() {
  const online = useOnlineStatus();
  if (online) return null;
  return (
    <div className="qp-offline-banner" role="status">
      <strong>You're offline.</strong> Reads still work from cache. New changes
      can't be saved until you reconnect.
    </div>
  );
}

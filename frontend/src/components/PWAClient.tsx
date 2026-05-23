"use client";

import { useEffect, useState } from "react";

/**
 * Registers the service worker on the client. Also exposes the online/offline
 * state via a small Zustand-free hook (just useState + window listeners) so the
 * OfflineBanner can render reactively.
 */
export function PWAClient() {
  useEffect(() => {
    if (
      typeof window === "undefined" ||
      typeof navigator === "undefined" ||
      !("serviceWorker" in navigator) ||
      process.env.NODE_ENV === "development"
    ) {
      return;
    }
    // Register lazily so the initial render isn't blocked.
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        // Silent — SW registration failure should not break the app.
      });
    });
  }, []);
  return null;
}

export function useOnlineStatus(): boolean {
  // Default to true for SSR. The first client effect corrects it.
  const [online, setOnline] = useState(true);
  useEffect(() => {
    if (typeof navigator === "undefined") return;
    setOnline(navigator.onLine);
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);
  return online;
}

"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";

import { dequeue, peekAll, pendingCount } from "@/lib/offlineQueue";
import { useAuthStore } from "@/store/auth";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Drains the offline mutation queue when the browser goes online.
 * Replay: FIFO, last-write-wins. On 401 stops and redirects to login.
 * On 4xx (not 401) dequeues (irrecoverable). On 5xx/network-error stops.
 */
export function SyncManager() {
  const qc = useQueryClient();
  const [syncing, setSyncing] = useState(false);
  const [pending, setPending] = useState(0);
  const syncingRef = useRef(false);

  const refreshCount = useCallback(async () => {
    try {
      setPending(await pendingCount());
    } catch {
      // IndexedDB unavailable
    }
  }, []);

  const drain = useCallback(async () => {
    if (syncingRef.current) return;
    syncingRef.current = true;
    setSyncing(true);

    try {
      const items = await peekAll();
      for (const item of items) {
        const token = useAuthStore.getState().accessToken;
        const headers: Record<string, string> = { ...item.headers };
        if (token) headers.Authorization = `Bearer ${token}`;

        try {
          const res = await fetch(`${BASE}/api/v1${item.path}`, {
            method: item.method,
            headers,
            body: item.body ?? undefined,
          });

          if (res.status === 401) {
            useAuthStore.getState().clear();
            break;
          }

          if (res.ok || (res.status >= 400 && res.status < 500)) {
            if (item.id != null) await dequeue(item.id);
          } else {
            break; // 5xx — retry later
          }
        } catch {
          break; // network still down
        }
      }

      qc.invalidateQueries();
    } finally {
      syncingRef.current = false;
      setSyncing(false);
      await refreshCount();
    }
  }, [qc, refreshCount]);

  useEffect(() => {
    refreshCount();
    if (typeof navigator !== "undefined" && navigator.onLine) drain();

    const onOnline = () => drain();
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [drain, refreshCount]);

  // Background Sync registration (best-effort)
  useEffect(() => {
    if (
      typeof navigator !== "undefined" &&
      "serviceWorker" in navigator &&
      "SyncManager" in window
    ) {
      navigator.serviceWorker.ready
        .then((reg) => {
          // @ts-expect-error - SyncManager types not universal
          return reg.sync?.register?.("drain-offline-queue");
        })
        .catch(() => {});
    }
  }, []);

  if (pending === 0 && !syncing) return null;

  return (
    <div className="qp-sync-banner" role="status">
      {syncing ? (
        <span>Syncing {pending} queued change{pending !== 1 ? "s" : ""}...</span>
      ) : (
        <span>
          {pending} change{pending !== 1 ? "s" : ""} saved offline. Will sync
          when you reconnect.
        </span>
      )}
    </div>
  );
}

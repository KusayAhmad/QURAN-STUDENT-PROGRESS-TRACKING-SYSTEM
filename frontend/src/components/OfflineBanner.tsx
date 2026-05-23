"use client";

import { useT } from "@/lib/useT";

import { useOnlineStatus } from "./PWAClient";

export function OfflineBanner() {
  const t = useT();
  const online = useOnlineStatus();
  if (online) return null;
  return (
    <div className="qp-offline-banner" role="status">
      <strong>{t("pwa.offlineTitle")}</strong> {t("pwa.offlineDesc")}
    </div>
  );
}

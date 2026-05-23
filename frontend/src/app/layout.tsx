import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { I18nProvider } from "@/components/I18nProvider";
import { OfflineBanner } from "@/components/OfflineBanner";
import { PWAClient } from "@/components/PWAClient";
import { QueryProvider } from "@/components/QueryProvider";
import { SyncManager } from "@/components/SyncManager";
import "./globals.css";

export const metadata: Metadata = {
  title: "Quran Progress Tracker",
  description: "Track Quran memorization progress, evaluations, and analytics.",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Quran Progress",
  },
  icons: {
    icon: [
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#2563eb",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  // <html lang/dir> default to en/ltr; I18nProvider mutates them after
  // hydration based on the persisted locale store.
  return (
    <html lang="en" dir="ltr">
      <body>
        <I18nProvider>
          <QueryProvider>
            <OfflineBanner />
            <SyncManager />
            <PWAClient />
            {children}
          </QueryProvider>
        </I18nProvider>
      </body>
    </html>
  );
}

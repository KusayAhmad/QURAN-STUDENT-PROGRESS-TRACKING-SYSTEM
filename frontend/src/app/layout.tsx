import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { OfflineBanner } from "@/components/OfflineBanner";
import { PWAClient } from "@/components/PWAClient";
import { QueryProvider } from "@/components/QueryProvider";
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
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <OfflineBanner />
          <PWAClient />
          {children}
        </QueryProvider>
      </body>
    </html>
  );
}

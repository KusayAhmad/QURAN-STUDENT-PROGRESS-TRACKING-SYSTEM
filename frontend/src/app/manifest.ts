/**
 * Web App Manifest. Next.js App Router serves this from /manifest.webmanifest
 * automatically.
 */
import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Quran Progress Tracker",
    short_name: "Quran Progress",
    description:
      "Track Quran memorization progress, evaluations, and analytics for your school.",
    start_url: "/dashboard",
    display: "standalone",
    background_color: "#f7f7f9",
    theme_color: "#2563eb",
    orientation: "portrait",
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}

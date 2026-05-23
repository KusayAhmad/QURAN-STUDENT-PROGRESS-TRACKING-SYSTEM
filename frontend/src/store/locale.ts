// Locale preference, persisted to localStorage so refreshes keep it.
"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { Locale } from "@/lib/i18n";

interface LocaleState {
  locale: Locale;
  setLocale: (l: Locale) => void;
}

export const useLocaleStore = create<LocaleState>()(
  persist(
    (set) => ({
      locale: "en",
      setLocale: (locale) => set({ locale }),
    }),
    { name: "quran-locale" },
  ),
);

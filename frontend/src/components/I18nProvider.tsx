"use client";

import { type ReactNode, useEffect } from "react";

import { dirFor } from "@/lib/i18n";
import { useLocaleStore } from "@/store/locale";

/**
 * Pushes the current locale into <html lang> + <html dir> on every change.
 *
 * We can't set <html dir> at server-render time without cookies, so this
 * component does the minimum needed for a client-only locale toggle:
 * mutate the document element after hydration. The flash from default
 * "en"/"ltr" to "ar"/"rtl" is brief; cookie-driven SSR locale is a future
 * polish.
 */
export function I18nProvider({ children }: { children: ReactNode }) {
  const locale = useLocaleStore((s) => s.locale);

  useEffect(() => {
    if (typeof document === "undefined") return;
    const el = document.documentElement;
    el.lang = locale;
    el.dir = dirFor(locale);
  }, [locale]);

  return <>{children}</>;
}

"use client";

import { type TranslationKey, translate } from "@/lib/i18n";
import { useLocaleStore } from "@/store/locale";

/**
 * Hook returning a typed t(key) function bound to the current locale.
 *
 * Usage:
 *   const t = useT();
 *   t("auth.signIn")  // "Sign in" or "تسجيل الدخول"
 */
export function useT(): (key: TranslationKey) => string {
  const locale = useLocaleStore((s) => s.locale);
  return (key) => translate(locale, key);
}

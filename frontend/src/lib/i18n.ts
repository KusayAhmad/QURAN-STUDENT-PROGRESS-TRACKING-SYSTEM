/**
 * Tiny i18n: two hard-coded dictionaries (en, ar) and a t() hook.
 *
 * Why not next-intl / react-i18next:
 * - This app has ~80 user-visible strings; a full i18n stack adds bundle
 *   weight and configuration ceremony for not much win.
 * - Keys are typed (TranslationKey union), so missing translations are a
 *   compile error.
 *
 * Adding a third language = add one entry to LOCALES and one branch in the
 * dictionaries object.
 */
import { en } from "./i18n/en";
import { ar } from "./i18n/ar";

export type Locale = "en" | "ar";
export const LOCALES: { code: Locale; label: string; dir: "ltr" | "rtl" }[] = [
  { code: "en", label: "English", dir: "ltr" },
  { code: "ar", label: "العربية", dir: "rtl" },
];

// `en` is the source of truth; `ar` must mirror its keys.
export type TranslationKey = keyof typeof en;

const DICTIONARIES: Record<Locale, Record<TranslationKey, string>> = {
  en,
  ar,
};

export function translate(locale: Locale, key: TranslationKey): string {
  return DICTIONARIES[locale][key] ?? DICTIONARIES.en[key] ?? key;
}

export function dirFor(locale: Locale): "ltr" | "rtl" {
  return LOCALES.find((l) => l.code === locale)?.dir ?? "ltr";
}

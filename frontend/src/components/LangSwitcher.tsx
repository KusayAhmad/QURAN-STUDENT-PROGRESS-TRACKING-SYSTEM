"use client";

import { LOCALES } from "@/lib/i18n";
import { useLocaleStore } from "@/store/locale";

/** Tiny segmented toggle. Two options means a button row beats a <select>. */
export function LangSwitcher() {
  const locale = useLocaleStore((s) => s.locale);
  const setLocale = useLocaleStore((s) => s.setLocale);

  return (
    <div className="qp-lang-switch" role="group" aria-label="Language">
      {LOCALES.map((l) => (
        <button
          key={l.code}
          type="button"
          className={l.code === locale ? "qp-lang-btn active" : "qp-lang-btn"}
          onClick={() => setLocale(l.code)}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}

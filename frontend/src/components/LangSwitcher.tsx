"use client";

import { LOCALES } from "@/lib/i18n";
import { useT } from "@/lib/useT";
import { useLocaleStore } from "@/store/locale";

/** Tiny segmented toggle. Two options means a button row beats a <select>. */
export function LangSwitcher() {
  const locale = useLocaleStore((s) => s.locale);
  const setLocale = useLocaleStore((s) => s.setLocale);
  const t = useT();

  return (
    <div className="qp-lang-switch" role="group" aria-label={t("lang.toggle")}>
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

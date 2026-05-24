"use client";

// Smart revision suggestions (blueprint §12-C).
//
// Renders the top N (default 5) ranked surahs the student should revise,
// with a localized reason and recency tag. The list is short, dense, and
// scannable — teachers should be able to glance at it during a lesson.
//
// We use the locale-aware surah name (Arabic when locale=ar, English otherwise)
// because mixing scripts in this list looks broken on RTL.

import { useQuery } from "@tanstack/react-query";

import { revision } from "@/lib/api";
import type { RevisionReason, RevisionSuggestion } from "@/lib/types";
import { useT } from "@/lib/useT";
import { useLocaleStore } from "@/store/locale";

const DEFAULT_LIMIT = 5;

function reasonKey(reason: RevisionReason) {
  return `revision.reason.${reason}` as const;
}

function recencyLabel(
  daysSinceReview: number | null,
  t: (k: "revision.daysAgo" | "revision.neverReviewed") => string,
): string {
  if (daysSinceReview === null) return t("revision.neverReviewed");
  return t("revision.daysAgo").replace("{days}", String(daysSinceReview));
}

export function RevisionPanel({
  studentId,
  limit = DEFAULT_LIMIT,
}: {
  studentId: string;
  limit?: number;
}) {
  const t = useT();
  const locale = useLocaleStore((s) => s.locale);

  const query = useQuery({
    queryKey: ["revision", studentId, limit],
    queryFn: () => revision.suggest(studentId, limit),
    enabled: !!studentId,
    // Suggestions are derived from progress data; no need to refetch
    // aggressively. Re-render when the user lands on the page or after
    // mutations invalidate this key.
    staleTime: 60_000,
  });

  return (
    <section
      className="qp-card"
      aria-labelledby="revision-panel-title"
      style={{ marginBottom: 16 }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
          marginBottom: 8,
          gap: 12,
        }}
      >
        <div>
          <h2 id="revision-panel-title" style={{ margin: 0, fontSize: "1.1rem" }}>
            {t("revision.title")}
          </h2>
          <p
            style={{
              margin: 0,
              color: "var(--color-muted)",
              fontSize: "0.85rem",
            }}
          >
            {t("revision.subtitle")}
          </p>
        </div>
      </div>

      {query.isLoading ? (
        <p style={{ color: "var(--color-muted)" }}>{t("revision.loading")}</p>
      ) : query.error ? (
        <p className="qp-error">{(query.error as Error).message}</p>
      ) : !query.data || query.data.suggestions.length === 0 ? (
        <p style={{ color: "var(--color-muted)" }}>{t("revision.empty")}</p>
      ) : (
        <ol
          style={{
            listStyle: "none",
            padding: 0,
            margin: 0,
            display: "flex",
            flexDirection: "column",
            gap: 8,
          }}
        >
          {query.data.suggestions.map((s, idx) => (
            <RevisionRow
              key={s.surah_id}
              suggestion={s}
              rank={idx + 1}
              locale={locale}
              reasonLabel={t(reasonKey(s.reason))}
              recency={recencyLabel(s.days_since_review, t)}
              completionLabel={t("revision.completion").replace(
                "{percent}",
                String(s.completion_percent),
              )}
            />
          ))}
        </ol>
      )}
    </section>
  );
}

function RevisionRow({
  suggestion,
  rank,
  locale,
  reasonLabel,
  recency,
  completionLabel,
}: {
  suggestion: RevisionSuggestion;
  rank: number;
  locale: "en" | "ar";
  reasonLabel: string;
  recency: string;
  completionLabel: string;
}) {
  const surahName =
    locale === "ar" ? suggestion.surah_name_ar : suggestion.surah_name_en;
  const reasonClass = `qp-revision-reason qp-revision-reason-${suggestion.reason.toLowerCase()}`;

  return (
    <li
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "10px 12px",
        borderRadius: 8,
        background: "var(--color-surface, #fafafa)",
        border: "1px solid var(--color-border, #e5e7eb)",
      }}
    >
      <span
        aria-hidden
        style={{
          flex: "0 0 auto",
          width: 28,
          height: 28,
          borderRadius: "50%",
          background: "var(--color-primary, #2563eb)",
          color: "white",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "0.85rem",
          fontWeight: 600,
        }}
      >
        {rank}
      </span>
      <div style={{ flex: "1 1 auto", minWidth: 0 }}>
        <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>{surahName}</div>
        <div
          style={{
            color: "var(--color-muted)",
            fontSize: "0.8rem",
            display: "flex",
            flexWrap: "wrap",
            gap: 8,
          }}
        >
          <span className={reasonClass}>{reasonLabel}</span>
          <span>·</span>
          <span>{completionLabel}</span>
          <span>·</span>
          <span>{recency}</span>
        </div>
      </div>
    </li>
  );
}

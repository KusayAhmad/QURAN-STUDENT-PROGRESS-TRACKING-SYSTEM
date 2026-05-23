"use client";

import { useQuery } from "@tanstack/react-query";

import { analytics } from "@/lib/api";
import { useT } from "@/lib/useT";

function pct(n: number) {
  return `${n.toFixed(1)}%`;
}

export default function DashboardPage() {
  const t = useT();
  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics", "school"],
    queryFn: () => analytics.school(),
  });

  if (isLoading) return <p>{t("common.loading")}</p>;
  if (error) return <p className="qp-error">{(error as Error).message}</p>;
  if (!data) return null;

  const total = Object.values(data.counts_by_status).reduce(
    (a, b) => a + b,
    0,
  );
  const safePct = (n: number) => (total ? (n / total) * 100 : 0);

  return (
    <div>
      <h1>{t("dashboard.title")}</h1>
      <div className="qp-grid qp-grid-3" style={{ marginTop: 16 }}>
        <div className="qp-stat">
          <div className="qp-stat-label">{t("dashboard.activeStudents")}</div>
          <div className="qp-stat-value">{data.student_count}</div>
        </div>
        <div className="qp-stat">
          <div className="qp-stat-label">{t("dashboard.avgMastery")}</div>
          <div className="qp-stat-value">{pct(data.avg_mastery_percent)}</div>
        </div>
        <div className="qp-stat">
          <div className="qp-stat-label">{t("dashboard.avgCompletion")}</div>
          <div className="qp-stat-value">{pct(data.avg_completion_pct)}</div>
        </div>
      </div>

      <div className="qp-card" style={{ marginTop: 24 }}>
        <h2>{t("dashboard.statusDistribution")}</h2>
        <p style={{ color: "var(--color-muted)", margin: "0 0 12px 0" }}>
          {t("dashboard.statusHelp")}
        </p>
        {(
          [
            ["MASTERED", data.counts_by_status.MASTERED],
            ["STRONG", data.counts_by_status.STRONG],
            ["REVIEW_REQUIRED", data.counts_by_status.REVIEW_REQUIRED],
            ["IN_PROGRESS", data.counts_by_status.IN_PROGRESS],
            ["WEAK", data.counts_by_status.WEAK],
            ["NOT_STARTED", data.counts_by_status.NOT_STARTED],
          ] as const
        ).map(([key, count]) => (
          <div
            key={key}
            style={{
              display: "grid",
              gridTemplateColumns: "180px 1fr 80px",
              alignItems: "center",
              gap: 12,
              padding: "4px 0",
            }}
          >
            <span className={`qp-status qp-status-${key.toLowerCase()}`}>
              {t(`status.${key}` as const)}
            </span>
            <div
              style={{
                background: "#f3f4f6",
                height: 8,
                borderRadius: 4,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  background: "var(--color-primary)",
                  height: "100%",
                  width: `${safePct(count)}%`,
                }}
              />
            </div>
            <span style={{ textAlign: "end", color: "var(--color-muted)" }}>
              {count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

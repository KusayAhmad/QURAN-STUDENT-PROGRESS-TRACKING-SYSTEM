"use client";

// Class detail page: renders the class-level KPIs that the
// /api/v1/analytics/class/{id} endpoint has produced since MVP-2.
// Until now this endpoint had no frontend consumer.
//
// Layout mirrors the school dashboard: KPI tiles on top, status histogram
// below, then a list of assigned students linking through to their profiles.

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

import { analytics, classes, students } from "@/lib/api";
import { useT } from "@/lib/useT";

function pct(n: number) {
  return `${n.toFixed(1)}%`;
}

export default function ClassDetailPage() {
  const params = useParams<{ id: string }>();
  const classId = params.id;
  const t = useT();

  const classQuery = useQuery({
    queryKey: ["class", classId],
    queryFn: () => classes.get(classId),
    enabled: !!classId,
  });
  const analyticsQuery = useQuery({
    queryKey: ["analytics", "class", classId],
    queryFn: () => analytics.class(classId),
    enabled: !!classId,
  });
  const membersQuery = useQuery({
    queryKey: ["students", "by-class", classId],
    // Use the new class_id filter on /students. We bump limit to 200 — a
    // typical class is far smaller than that.
    queryFn: () => students.list({ class_id: classId, limit: 200 }),
    enabled: !!classId,
  });

  if (classQuery.isLoading) return <p>{t("common.loading")}</p>;
  if (classQuery.error) {
    return <p className="qp-error">{(classQuery.error as Error).message}</p>;
  }
  if (!classQuery.data) return null;

  const klass = classQuery.data;
  const a = analyticsQuery.data;
  const members = membersQuery.data?.items ?? [];

  // Sum of histogram = total slots (student_count × total_surahs); used for
  // bar-width calculation just like the school dashboard.
  const totalSlots = a
    ? Object.values(a.counts_by_status).reduce((acc, n) => acc + n, 0)
    : 0;
  const safePct = (n: number) => (totalSlots ? (n / totalSlots) * 100 : 0);

  return (
    <div>
      <div style={{ marginBottom: 8 }}>
        <Link href="/classes" style={{ fontSize: "0.85rem" }}>
          ← {t("nav.classes")}
        </Link>
      </div>
      <h1>{klass.name}</h1>
      <p style={{ color: "var(--color-muted)", marginTop: -4 }}>
        {klass.academic_year}
      </p>

      <div className="qp-grid qp-grid-3" style={{ marginTop: 16 }}>
        <div className="qp-stat">
          <div className="qp-stat-label">{t("classDetail.studentCount")}</div>
          <div className="qp-stat-value">{a ? a.student_count : "—"}</div>
        </div>
        <div className="qp-stat">
          <div className="qp-stat-label">{t("classDetail.avgMastery")}</div>
          <div className="qp-stat-value">
            {a ? pct(a.avg_mastery_percent) : "—"}
          </div>
        </div>
        <div className="qp-stat">
          <div className="qp-stat-label">{t("classDetail.avgCompletion")}</div>
          <div className="qp-stat-value">
            {a ? pct(a.avg_completion_pct) : "—"}
          </div>
        </div>
      </div>

      {a ? (
        <div className="qp-card" style={{ marginTop: 24 }}>
          <h2>{t("classDetail.statusDistribution")}</h2>
          <p style={{ color: "var(--color-muted)", margin: "0 0 12px 0" }}>
            {t("classDetail.statusHelp")}
          </p>
          {(
            [
              ["MASTERED", a.counts_by_status.MASTERED],
              ["STRONG", a.counts_by_status.STRONG],
              ["REVIEW_REQUIRED", a.counts_by_status.REVIEW_REQUIRED],
              ["IN_PROGRESS", a.counts_by_status.IN_PROGRESS],
              ["WEAK", a.counts_by_status.WEAK],
              ["NOT_STARTED", a.counts_by_status.NOT_STARTED],
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
      ) : null}

      <div className="qp-card" style={{ marginTop: 24, padding: 0 }}>
        <h2 style={{ padding: "16px 16px 0 16px" }}>
          {t("classDetail.members")}
        </h2>
        {membersQuery.isLoading ? (
          <p style={{ padding: 16 }}>{t("common.loading")}</p>
        ) : members.length === 0 ? (
          <p style={{ padding: 16, color: "var(--color-muted)" }}>
            {t("classDetail.noMembers")}
          </p>
        ) : (
          <table className="qp-table" style={{ marginTop: 8 }}>
            <thead>
              <tr>
                <th>{t("students.fullName")}</th>
                <th>{t("students.gender")}</th>
                <th>{t("students.status")}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {members.map((s) => (
                <tr key={s.id}>
                  <td style={{ fontWeight: 500 }}>{s.full_name}</td>
                  <td style={{ color: "var(--color-muted)" }}>{s.gender}</td>
                  <td>
                    <span
                      className={`qp-status qp-status-${s.status === "ACTIVE" ? "strong" : "not_started"}`}
                    >
                      {s.status}
                    </span>
                  </td>
                  <td>
                    <Link
                      href={`/students/${s.id}`}
                      style={{ fontSize: "0.85rem" }}
                    >
                      {t("classDetail.openStudent")}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { EvaluationTrendChart } from "@/components/EvaluationTrendChart";
import { EvaluationsPanel } from "@/components/EvaluationsPanel";
import { ObservationsPanel } from "@/components/ObservationsPanel";
import { ProgressMatrix } from "@/components/ProgressMatrix";
import { RevisionPanel } from "@/components/RevisionPanel";
import { analytics, students } from "@/lib/api";

type Tab = "matrix" | "evaluations" | "observations";

export default function StudentDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>("matrix");

  const studentId = params.id;

  const studentQuery = useQuery({
    queryKey: ["student", studentId],
    queryFn: () => students.get(studentId),
    enabled: !!studentId,
  });
  const analyticsQuery = useQuery({
    queryKey: ["analytics", "student", studentId],
    queryFn: () => analytics.student(studentId),
    enabled: !!studentId,
  });
  const archive = useMutation({
    mutationFn: () => students.archive(studentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["students"] });
      router.replace("/students");
    },
  });

  if (studentQuery.isLoading) return <p>Loading...</p>;
  if (studentQuery.error) {
    return (
      <p className="qp-error">{(studentQuery.error as Error).message}</p>
    );
  }
  if (!studentQuery.data) return null;
  const student = studentQuery.data;

  return (
    <div>
      <div style={{ marginBottom: 8 }}>
        <Link href="/students" style={{ fontSize: "0.85rem" }}>
          ← Students
        </Link>
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <div>
          <h1 style={{ marginBottom: 4 }}>{student.full_name}</h1>
          <div style={{ color: "var(--color-muted)" }}>
            {student.gender} ·{" "}
            <span
              className={`qp-status qp-status-${student.status === "ACTIVE" ? "strong" : "not_started"}`}
            >
              {student.status}
            </span>
            {student.guardian_name ? ` · Guardian: ${student.guardian_name}` : null}
          </div>
        </div>
        {student.status === "ACTIVE" ? (
          <button
            className="qp-btn-ghost qp-btn-danger"
            style={{ color: "white" }}
            onClick={() => {
              if (
                confirm(
                  `Archive ${student.full_name}? Their data is preserved but they will be hidden from the default list.`,
                )
              ) {
                archive.mutate();
              }
            }}
          >
            Archive
          </button>
        ) : null}
      </div>

      {analyticsQuery.data ? (
        <div className="qp-grid qp-grid-3" style={{ marginBottom: 16 }}>
          <div className="qp-stat">
            <div className="qp-stat-label">Mastery</div>
            <div className="qp-stat-value">
              {analyticsQuery.data.mastery_percent.toFixed(1)}%
            </div>
            <div style={{ color: "var(--color-muted)", fontSize: "0.8rem" }}>
              {analyticsQuery.data.counts_by_status.MASTERED} of{" "}
              {analyticsQuery.data.total_surahs} surahs
            </div>
          </div>
          <div className="qp-stat">
            <div className="qp-stat-label">Avg. completion</div>
            <div className="qp-stat-value">
              {analyticsQuery.data.avg_completion_pct.toFixed(1)}%
            </div>
            <div style={{ color: "var(--color-muted)", fontSize: "0.8rem" }}>
              across recorded surahs
            </div>
          </div>
          <div className="qp-stat">
            <div className="qp-stat-label">Recent eval avg</div>
            <div className="qp-stat-value">
              {analyticsQuery.data.recent_evaluations_avg_score?.toFixed(1) ?? "—"}
            </div>
            <div style={{ color: "var(--color-muted)", fontSize: "0.8rem" }}>
              last {analyticsQuery.data.recent_evaluations_count} evals
            </div>
          </div>
        </div>
      ) : null}

      <RevisionPanel studentId={studentId} />

      <div className="qp-tabs">
        <button
          className={tab === "matrix" ? "qp-tab active" : "qp-tab"}
          onClick={() => setTab("matrix")}
        >
          Memorization matrix
        </button>
        <button
          className={tab === "evaluations" ? "qp-tab active" : "qp-tab"}
          onClick={() => setTab("evaluations")}
        >
          Evaluations
        </button>
        <button
          className={tab === "observations" ? "qp-tab active" : "qp-tab"}
          onClick={() => setTab("observations")}
        >
          Observations
        </button>
      </div>

      {tab === "matrix" ? <ProgressMatrix studentId={studentId} /> : null}
      {tab === "evaluations" ? (
        <>
          <EvaluationTrendChart studentId={studentId} />
          <EvaluationsPanel studentId={studentId} />
        </>
      ) : null}
      {tab === "observations" ? <ObservationsPanel studentId={studentId} /> : null}
    </div>
  );
}

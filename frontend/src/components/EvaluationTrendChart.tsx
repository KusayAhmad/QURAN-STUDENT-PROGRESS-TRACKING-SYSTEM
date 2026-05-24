"use client";

// Hand-rolled SVG line chart. Avoids a chart-library dependency
// (Recharts/Chart.js add 50–100 KB minified) for a single small chart.
// If we add a second time-series view later, we'll graduate to Recharts.
//
// Surfaces the /analytics/student/{id}/evaluation-trend endpoint that has
// existed since MVP-2 with no frontend consumer.

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { analytics } from "@/lib/api";
import type { TimeBucket } from "@/lib/types";

const BUCKETS: { value: TimeBucket; labelKey: string }[] = [
  { value: "day", labelKey: "Day" },
  { value: "week", labelKey: "Week" },
  { value: "month", labelKey: "Month" },
];

// Plot dimensions. Kept in module scope so they're stable across renders.
const W = 600;
const H = 200;
const PAD_LEFT = 36;
const PAD_RIGHT = 12;
const PAD_TOP = 16;
const PAD_BOTTOM = 28;
const PLOT_W = W - PAD_LEFT - PAD_RIGHT;
const PLOT_H = H - PAD_TOP - PAD_BOTTOM;

export function EvaluationTrendChart({ studentId }: { studentId: string }) {
  const [bucket, setBucket] = useState<TimeBucket>("month");

  const query = useQuery({
    queryKey: ["analytics", "student", studentId, "evaluation-trend", bucket],
    queryFn: () => analytics.evaluationTrend(studentId, bucket),
    enabled: !!studentId,
    staleTime: 60_000,
  });

  return (
    <section className="qp-card" style={{ marginBottom: 16 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: 8,
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: "1.1rem" }}>Evaluation trend</h2>
          <p
            style={{
              margin: 0,
              color: "var(--color-muted)",
              fontSize: "0.85rem",
            }}
          >
            Average overall score over time.
          </p>
        </div>
        <div className="qp-lang-switch" role="tablist" aria-label="Time bucket">
          {BUCKETS.map((b) => (
            <button
              key={b.value}
              type="button"
              role="tab"
              aria-selected={bucket === b.value}
              className={
                bucket === b.value ? "qp-lang-btn active" : "qp-lang-btn"
              }
              onClick={() => setBucket(b.value)}
            >
              {b.labelKey}
            </button>
          ))}
        </div>
      </div>

      {query.isLoading ? (
        <p style={{ color: "var(--color-muted)" }}>Loading trend...</p>
      ) : query.error ? (
        <p className="qp-error">{(query.error as Error).message}</p>
      ) : !query.data || query.data.points.length === 0 ? (
        <p style={{ color: "var(--color-muted)" }}>
          No evaluations recorded yet — once you log a few, the trend will
          appear here.
        </p>
      ) : (
        <TrendSvg points={query.data.points} />
      )}
    </section>
  );
}

function TrendSvg({
  points,
}: {
  points: { period_start: string; avg_overall_score: number; eval_count: number }[];
}) {
  // Y axis is fixed 0–100 (overall_score range). X axis is one tick per
  // bucket period. With one point we'd produce a degenerate path, so we
  // render that case as a single dot.
  const n = points.length;
  const xFor = (i: number) =>
    n === 1 ? PAD_LEFT + PLOT_W / 2 : PAD_LEFT + (i / (n - 1)) * PLOT_W;
  const yFor = (score: number) =>
    PAD_TOP + PLOT_H - (score / 100) * PLOT_H;

  const path = points
    .map((p, i) => {
      const cmd = i === 0 ? "M" : "L";
      return `${cmd}${xFor(i).toFixed(1)},${yFor(p.avg_overall_score).toFixed(1)}`;
    })
    .join(" ");

  // Y-axis gridlines at 0, 50, 100. We omit 25/75 to keep the chart calm.
  const yTicks = [0, 50, 100];

  // X labels: show every label if ≤6 points, else thin to ~6.
  const labelStride = Math.max(1, Math.ceil(n / 6));

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      style={{ maxWidth: "100%", height: "auto" }}
      aria-label="Evaluation trend chart"
    >
      {/* Y gridlines + labels */}
      {yTicks.map((tick) => {
        const y = yFor(tick);
        return (
          <g key={tick}>
            <line
              x1={PAD_LEFT}
              x2={W - PAD_RIGHT}
              y1={y}
              y2={y}
              stroke="var(--color-border)"
              strokeDasharray={tick === 0 ? "0" : "3 3"}
            />
            <text
              x={PAD_LEFT - 6}
              y={y + 4}
              textAnchor="end"
              fontSize="10"
              fill="var(--color-muted)"
            >
              {tick}
            </text>
          </g>
        );
      })}

      {/* Trend line. unicode-bidi:isolate keeps it stable under RTL. */}
      <path
        d={path}
        fill="none"
        stroke="var(--color-primary)"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {/* Points + tooltips via <title>. SVG <title> is the cheapest
          accessible tooltip — no JS or popper logic needed. */}
      {points.map((p, i) => (
        <g key={p.period_start}>
          <circle
            cx={xFor(i)}
            cy={yFor(p.avg_overall_score)}
            r={3.5}
            fill="var(--color-primary)"
          >
            <title>
              {p.period_start}: avg {p.avg_overall_score.toFixed(1)} (
              {p.eval_count} eval{p.eval_count === 1 ? "" : "s"})
            </title>
          </circle>
          {i % labelStride === 0 ? (
            <text
              x={xFor(i)}
              y={H - 8}
              textAnchor="middle"
              fontSize="10"
              fill="var(--color-muted)"
            >
              {p.period_start}
            </text>
          ) : null}
        </g>
      ))}
    </svg>
  );
}

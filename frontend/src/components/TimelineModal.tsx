"use client";

import { useQuery } from "@tanstack/react-query";

import { progress } from "@/lib/api";
import type { Surah } from "@/lib/types";

import { StatusBadge } from "./StatusBadge";

/**
 * Shows the per-surah status timeline (blueprint §12-A).
 * Driven by GET /students/{id}/surahs/{surah_id}/timeline.
 */
export function TimelineModal({
  studentId,
  surah,
  onClose,
}: {
  studentId: string;
  surah: Surah;
  onClose: () => void;
}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["timeline", studentId, surah.id],
    queryFn: () => progress.timeline(studentId, surah.id),
  });

  return (
    <div className="qp-overlay" onClick={onClose}>
      <div className="qp-modal" onClick={(e) => e.stopPropagation()}>
        <h2>
          <span className="qp-surah-name-ar">{surah.surah_name_ar}</span>{" "}
          <span style={{ color: "var(--color-muted)", fontSize: "0.85rem" }}>
            timeline
          </span>
        </h2>

        {isLoading ? (
          <p>Loading...</p>
        ) : error ? (
          <p className="qp-error">{(error as Error).message}</p>
        ) : !data || data.length === 0 ? (
          <p style={{ color: "var(--color-muted)" }}>
            No history yet. Set this surah's status from the matrix to start
            building a timeline.
          </p>
        ) : (
          <ol
            style={{
              listStyle: "none",
              padding: 0,
              margin: 0,
              maxHeight: 360,
              overflowY: "auto",
            }}
          >
            {data.map((entry) => (
              <li
                key={entry.id}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr auto",
                  gap: 12,
                  padding: "8px 0",
                  borderBottom: "1px solid var(--color-border)",
                }}
              >
                <div>
                  <StatusBadge status={entry.status} />{" "}
                  <span style={{ color: "var(--color-muted)" }}>
                    · {entry.completion_percent}%
                    {entry.action === "CREATE" ? " · first record" : ""}
                  </span>
                  {entry.notes ? (
                    <div style={{ color: "var(--color-muted)", fontSize: "0.85rem" }}>
                      {entry.notes}
                    </div>
                  ) : null}
                </div>
                <span style={{ color: "var(--color-muted)", fontSize: "0.8rem" }}>
                  {new Date(entry.recorded_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ol>
        )}

        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 16 }}>
          <button type="button" className="qp-btn-ghost" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

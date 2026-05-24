"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { progress, surahs as surahsApi } from "@/lib/api";
import {
  MEMORIZATION_STATUSES,
  type MemorizationStatus,
  type Progress,
  type Surah,
} from "@/lib/types";

import { StatusBadge } from "./StatusBadge";
import { TimelineModal } from "./TimelineModal";

/**
 * The Excel replacement: one row per surah, current status pill, click to
 * change. Surah list is fetched once (114 rows, static); progress is fetched
 * per student.
 */
export function ProgressMatrix({ studentId }: { studentId: string }) {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<{ surah: Surah; current: Progress | undefined } | null>(
    null,
  );
  const [timeline, setTimeline] = useState<{ surah: Surah } | null>(null);

  const surahsQuery = useQuery({
    queryKey: ["surahs"],
    queryFn: () => surahsApi.list(),
    staleTime: 60 * 60 * 1000, // 1 hour — surahs are static
  });
  const progressQuery = useQuery({
    queryKey: ["progress", studentId],
    queryFn: () => progress.listForStudent(studentId),
  });

  const progressBySurah = useMemo(() => {
    const map = new Map<number, Progress>();
    progressQuery.data?.forEach((p) => map.set(p.surah_id, p));
    return map;
  }, [progressQuery.data]);

  const upsert = useMutation({
    mutationFn: (input: {
      surah_id: number;
      status: MemorizationStatus;
      completion_percent: number;
      notes?: string | null;
    }) =>
      progress.upsert(studentId, {
        surah_id: input.surah_id,
        status: input.status,
        completion_percent: input.completion_percent,
        notes: input.notes,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["progress", studentId] });
      qc.invalidateQueries({ queryKey: ["analytics", "student", studentId] });
      qc.invalidateQueries({ queryKey: ["analytics", "school"] });
      qc.invalidateQueries({ queryKey: ["revision", studentId] });
      setEditing(null);
    },
  });

  if (surahsQuery.isLoading || progressQuery.isLoading) {
    return <p>Loading matrix...</p>;
  }
  if (surahsQuery.error) {
    return <p className="qp-error">{(surahsQuery.error as Error).message}</p>;
  }
  if (!surahsQuery.data) return null;

  return (
    <div className="qp-card" style={{ padding: 0 }}>
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid var(--color-border)",
        }}
      >
        <strong>Memorization matrix</strong>{" "}
        <span style={{ color: "var(--color-muted)", marginLeft: 8 }}>
          Click any status to change it. Click "History" to see the timeline.
        </span>
      </div>
      <div style={{ maxHeight: 600, overflow: "auto" }}>
        {surahsQuery.data.map((surah) => {
          const current = progressBySurah.get(surah.id);
          const status: MemorizationStatus = current?.status ?? "NOT_STARTED";
          return (
            <div key={surah.id} className="qp-matrix-row">
              <span className="qp-surah-num">{surah.surah_order}</span>
              <div>
                <span className="qp-surah-name-ar">{surah.surah_name_ar}</span>{" "}
                <span className="qp-surah-name-en">{surah.surah_name_en}</span>
              </div>
              <StatusBadge
                status={status}
                onClick={() => setEditing({ surah, current })}
              />
              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                <span style={{ color: "var(--color-muted)" }}>
                  {current?.completion_percent ?? 0}%
                </span>
                <button
                  type="button"
                  className="qp-btn-ghost"
                  style={{ padding: "2px 10px", fontSize: "0.8rem" }}
                  onClick={() => setTimeline({ surah })}
                >
                  History
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {editing ? (
        <EditCellModal
          surah={editing.surah}
          current={editing.current}
          onClose={() => setEditing(null)}
          onSave={(status, completion) =>
            upsert.mutate({
              surah_id: editing.surah.id,
              status,
              completion_percent: completion,
              notes: editing.current?.notes,
            })
          }
          saving={upsert.isPending}
          error={upsert.error ? (upsert.error as Error).message : null}
        />
      ) : null}

      {timeline ? (
        <TimelineModal
          studentId={studentId}
          surah={timeline.surah}
          onClose={() => setTimeline(null)}
        />
      ) : null}
    </div>
  );
}

function EditCellModal({
  surah,
  current,
  onClose,
  onSave,
  saving,
  error,
}: {
  surah: Surah;
  current: Progress | undefined;
  onClose: () => void;
  onSave: (status: MemorizationStatus, completion: number) => void;
  saving: boolean;
  error: string | null;
}) {
  const [status, setStatus] = useState<MemorizationStatus>(
    current?.status ?? "NOT_STARTED",
  );
  const [completion, setCompletion] = useState<number>(
    current?.completion_percent ?? 0,
  );

  return (
    <div className="qp-overlay" onClick={onClose}>
      <div className="qp-modal" onClick={(e) => e.stopPropagation()}>
        <h2>
          <span className="qp-surah-name-ar">{surah.surah_name_ar}</span>{" "}
          <span style={{ color: "var(--color-muted)", fontSize: "0.85rem" }}>
            {surah.surah_name_en}
          </span>
        </h2>
        <p style={{ color: "var(--color-muted)", marginTop: 0 }}>
          Surah #{surah.surah_order} · {surah.ayah_count} ayahs · Juz {surah.juz_no}
        </p>

        <div className="qp-form">
          <div>
            <label>Status</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {MEMORIZATION_STATUSES.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setStatus(s)}
                  className={`qp-status qp-status-${s.toLowerCase()}`}
                  style={{
                    opacity: s === status ? 1 : 0.55,
                    transform: s === status ? "scale(1.05)" : "scale(1)",
                  }}
                >
                  {s.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label>Completion %</label>
            <input
              type="number"
              min={0}
              max={100}
              value={completion}
              onChange={(e) => setCompletion(Number(e.target.value))}
            />
          </div>
          {error ? <div className="qp-error">{error}</div> : null}
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button type="button" className="qp-btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button
              type="button"
              className="qp-btn"
              disabled={saving}
              onClick={() => onSave(status, completion)}
            >
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

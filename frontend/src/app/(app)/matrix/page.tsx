"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo, useState } from "react";

import { matrixApi, progress as progressApi, type MatrixCell } from "@/lib/api";
import {
  MEMORIZATION_STATUSES,
  type MemorizationStatus,
  type Surah,
} from "@/lib/types";

const STATUS_LETTER: Record<MemorizationStatus, string> = {
  NOT_STARTED: "",
  IN_PROGRESS: "P",
  REVIEW_REQUIRED: "R",
  WEAK: "W",
  STRONG: "S",
  MASTERED: "M",
};

const LEGEND: { status: MemorizationStatus; label: string }[] = [
  { status: "MASTERED", label: "Mastered" },
  { status: "STRONG", label: "Strong" },
  { status: "REVIEW_REQUIRED", label: "Review" },
  { status: "WEAK", label: "Weak" },
  { status: "IN_PROGRESS", label: "In progress" },
  { status: "NOT_STARTED", label: "Not started" },
];

interface EditTarget {
  studentId: string;
  studentName: string;
  surah: Surah;
  current: MatrixCell | undefined;
}

export default function MatrixPage() {
  const qc = useQueryClient();
  const [includeArchived, setIncludeArchived] = useState(false);
  const [editing, setEditing] = useState<EditTarget | null>(null);

  const matrixQuery = useQuery({
    queryKey: ["matrix", { includeArchived }],
    queryFn: () => matrixApi.get({ include_archived: includeArchived }),
  });

  const upsert = useMutation({
    mutationFn: (input: {
      student_id: string;
      surah_id: number;
      status: MemorizationStatus;
      completion_percent: number;
    }) =>
      progressApi.upsert(input.student_id, {
        surah_id: input.surah_id,
        status: input.status,
        completion_percent: input.completion_percent,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["matrix"] });
      qc.invalidateQueries({ queryKey: ["analytics", "school"] });
      setEditing(null);
    },
  });

  // Build a lookup of (studentId -> surahId -> MatrixCell) for quick render.
  const cellLookup = useMemo(() => {
    const map = new Map<string, Map<number, MatrixCell>>();
    matrixQuery.data?.students.forEach((s) => {
      const inner = new Map<number, MatrixCell>();
      s.cells.forEach((c) => inner.set(c.surah_id, c));
      map.set(s.id, inner);
    });
    return map;
  }, [matrixQuery.data]);

  if (matrixQuery.isLoading) return <p>Loading matrix...</p>;
  if (matrixQuery.error) {
    return <p className="qp-error">{(matrixQuery.error as Error).message}</p>;
  }
  if (!matrixQuery.data) return null;
  const { surahs, students } = matrixQuery.data;

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 12,
        }}
      >
        <h1 style={{ margin: 0 }}>Matrix</h1>
        <label style={{ fontSize: "0.85rem" }}>
          <input
            type="checkbox"
            checked={includeArchived}
            onChange={(e) => setIncludeArchived(e.target.checked)}
            style={{ width: "auto", marginRight: 6 }}
          />
          Include archived
        </label>
      </div>

      <div className="qp-card" style={{ marginBottom: 12, padding: 12 }}>
        <span style={{ color: "var(--color-muted)", marginRight: 12 }}>
          Legend:
        </span>
        {LEGEND.map((l) => (
          <span
            key={l.status}
            className={`qp-status qp-status-${l.status.toLowerCase()}`}
            style={{ marginRight: 6 }}
          >
            {l.label}
          </span>
        ))}
      </div>

      {students.length === 0 ? (
        <div className="qp-card">
          <p style={{ color: "var(--color-muted)", margin: 0 }}>
            No students yet.{" "}
            <Link href="/students">Add some on the Students page</Link>.
          </p>
        </div>
      ) : (
        <div className="qp-grid-wrap">
          <table className="qp-grid-table">
            <thead>
              <tr>
                <th className="qp-grid-corner">Student ↓ / Surah →</th>
                {surahs.map((s) => (
                  <th key={s.id} title={`${s.surah_order}. ${s.surah_name_en}`}>
                    {s.surah_order}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {students.map((student) => {
                const studentCells = cellLookup.get(student.id);
                return (
                  <tr key={student.id}>
                    <th scope="row" className="qp-grid-rowhead">
                      <Link href={`/students/${student.id}`}>
                        {student.full_name}
                      </Link>
                    </th>
                    {surahs.map((surah) => {
                      const cell = studentCells?.get(surah.id);
                      const status: MemorizationStatus =
                        cell?.status ?? "NOT_STARTED";
                      const isEmpty = !cell;
                      return (
                        <td key={surah.id}>
                          <button
                            type="button"
                            className={
                              isEmpty
                                ? "qp-grid-cell qp-grid-cell-empty"
                                : `qp-grid-cell qp-status-${status.toLowerCase()}`
                            }
                            title={`${student.full_name} · ${surah.surah_name_en} · ${status}${
                              cell ? ` · ${cell.completion_percent}%` : ""
                            }`}
                            aria-label={`${student.full_name} – ${surah.surah_name_en}: ${status}`}
                            onClick={() =>
                              setEditing({
                                studentId: student.id,
                                studentName: student.full_name,
                                surah,
                                current: cell,
                              })
                            }
                          >
                            {STATUS_LETTER[status]}
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {editing ? (
        <CellEditModal
          target={editing}
          onClose={() => setEditing(null)}
          onSave={(status, completion) =>
            upsert.mutate({
              student_id: editing.studentId,
              surah_id: editing.surah.id,
              status,
              completion_percent: completion,
            })
          }
          saving={upsert.isPending}
          error={upsert.error ? (upsert.error as Error).message : null}
        />
      ) : null}
    </div>
  );
}

function CellEditModal({
  target,
  onClose,
  onSave,
  saving,
  error,
}: {
  target: EditTarget;
  onClose: () => void;
  onSave: (status: MemorizationStatus, completion: number) => void;
  saving: boolean;
  error: string | null;
}) {
  const [status, setStatus] = useState<MemorizationStatus>(
    target.current?.status ?? "NOT_STARTED",
  );
  const [completion, setCompletion] = useState<number>(
    target.current?.completion_percent ?? 0,
  );

  return (
    <div className="qp-overlay" onClick={onClose}>
      <div className="qp-modal" onClick={(e) => e.stopPropagation()}>
        <h2 style={{ marginBottom: 4 }}>{target.studentName}</h2>
        <p style={{ color: "var(--color-muted)", marginTop: 0 }}>
          <span className="qp-surah-name-ar">{target.surah.surah_name_ar}</span>{" "}
          · {target.surah.surah_name_en} · Surah #{target.surah.surah_order}
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

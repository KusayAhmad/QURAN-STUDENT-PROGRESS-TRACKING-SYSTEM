"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";

import { evaluations } from "@/lib/api";
import type { EvaluationType } from "@/lib/types";

const TYPES: { value: EvaluationType; label: string }[] = [
  { value: "ORAL_RECITATION", label: "Oral recitation" },
  { value: "REVISION_EXAM", label: "Revision exam" },
  { value: "MONTHLY_REVIEW", label: "Monthly review" },
  { value: "ACCURACY_TEST", label: "Accuracy test" },
  { value: "OTHER", label: "Other" },
];

export function EvaluationsPanel({ studentId }: { studentId: string }) {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const list = useQuery({
    queryKey: ["evaluations", studentId],
    queryFn: () => evaluations.list(studentId),
  });
  const remove = useMutation({
    mutationFn: (id: string) => evaluations.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["evaluations", studentId] });
      qc.invalidateQueries({ queryKey: ["analytics", "student", studentId] });
    },
  });

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
        <h2 style={{ margin: 0 }}>Evaluations</h2>
        <button className="qp-btn" onClick={() => setShowForm(true)}>
          New evaluation
        </button>
      </div>

      <div className="qp-card" style={{ padding: 0 }}>
        {list.isLoading ? (
          <p style={{ padding: 16 }}>Loading...</p>
        ) : list.data && list.data.items.length === 0 ? (
          <p style={{ padding: 16, color: "var(--color-muted)" }}>
            No evaluations recorded yet.
          </p>
        ) : (
          <table className="qp-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Overall</th>
                <th>Tajweed</th>
                <th>Accuracy</th>
                <th>Fluency</th>
                <th>Notes</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {list.data?.items.map((e) => (
                <tr key={e.id}>
                  <td>{e.exam_date}</td>
                  <td style={{ fontSize: "0.85rem" }}>
                    {TYPES.find((t) => t.value === e.type)?.label ?? e.type}
                  </td>
                  <td>
                    <strong>{e.overall_score ?? "-"}</strong>
                  </td>
                  <td>{e.tajweed_score ?? "-"}</td>
                  <td>{e.accuracy_score ?? "-"}</td>
                  <td>{e.fluency_score ?? "-"}</td>
                  <td style={{ color: "var(--color-muted)" }}>
                    {e.notes ?? "-"}
                  </td>
                  <td>
                    <button
                      className="qp-btn-ghost"
                      style={{ color: "var(--color-danger)" }}
                      onClick={() => {
                        if (confirm("Delete this evaluation?")) remove.mutate(e.id);
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showForm ? (
        <NewEvaluationModal
          studentId={studentId}
          onClose={() => setShowForm(false)}
          onCreated={() => {
            setShowForm(false);
            qc.invalidateQueries({ queryKey: ["evaluations", studentId] });
            qc.invalidateQueries({ queryKey: ["analytics", "student", studentId] });
          }}
        />
      ) : null}
    </div>
  );
}

function NewEvaluationModal({
  studentId,
  onClose,
  onCreated,
}: {
  studentId: string;
  onClose: () => void;
  onCreated: () => void;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const [type, setType] = useState<EvaluationType>("ORAL_RECITATION");
  const [examDate, setExamDate] = useState<string>(today);
  const [tajweed, setTajweed] = useState<string>("");
  const [accuracy, setAccuracy] = useState<string>("");
  const [fluency, setFluency] = useState<string>("");
  const [retention, setRetention] = useState<string>("");
  const [speed, setSpeed] = useState<string>("");
  const [confidence, setConfidence] = useState<string>("");
  const [notes, setNotes] = useState<string>("");

  const toNum = (v: string) => (v === "" ? null : Number(v));

  const mutation = useMutation({
    mutationFn: () =>
      evaluations.create(studentId, {
        type,
        exam_date: examDate,
        tajweed_score: toNum(tajweed),
        accuracy_score: toNum(accuracy),
        fluency_score: toNum(fluency),
        retention_score: toNum(retention),
        speed_score: toNum(speed),
        confidence_score: toNum(confidence),
        notes: notes || null,
      }),
    onSuccess: onCreated,
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    mutation.mutate();
  }

  function ScoreInput({
    label,
    value,
    set,
  }: {
    label: string;
    value: string;
    set: (v: string) => void;
  }) {
    return (
      <div>
        <label>{label}</label>
        <input
          type="number"
          min={0}
          max={100}
          value={value}
          onChange={(e) => set(e.target.value)}
        />
      </div>
    );
  }

  return (
    <div className="qp-overlay" onClick={onClose}>
      <div className="qp-modal" onClick={(e) => e.stopPropagation()}>
        <h2>New evaluation</h2>
        <form onSubmit={handleSubmit} className="qp-form">
          <div className="qp-row">
            <div>
              <label>Type</label>
              <select value={type} onChange={(e) => setType(e.target.value as EvaluationType)}>
                {TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>Exam date</label>
              <input
                type="date"
                value={examDate}
                onChange={(e) => setExamDate(e.target.value)}
              />
            </div>
          </div>
          <p style={{ color: "var(--color-muted)", fontSize: "0.85rem", margin: 0 }}>
            All scores 0–100, optional. If you leave overall blank, the backend
            averages whatever axes you provide.
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: 8,
            }}
          >
            <ScoreInput label="Tajweed" value={tajweed} set={setTajweed} />
            <ScoreInput label="Accuracy" value={accuracy} set={setAccuracy} />
            <ScoreInput label="Fluency" value={fluency} set={setFluency} />
            <ScoreInput label="Retention" value={retention} set={setRetention} />
            <ScoreInput label="Speed" value={speed} set={setSpeed} />
            <ScoreInput label="Confidence" value={confidence} set={setConfidence} />
          </div>
          <div>
            <label>Notes (optional)</label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
          {mutation.error ? (
            <div className="qp-error">{(mutation.error as Error).message}</div>
          ) : null}
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button type="button" className="qp-btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="qp-btn" disabled={mutation.isPending}>
              {mutation.isPending ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

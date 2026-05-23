"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";

import { observations } from "@/lib/api";
import type { ObservationType } from "@/lib/types";

const TYPES: { value: ObservationType; label: string }[] = [
  { value: "GENERAL", label: "General" },
  { value: "DAILY_NOTE", label: "Daily note" },
  { value: "WEAK_PRONUNCIATION", label: "Weak pronunciation" },
  { value: "MISSING_REVISION", label: "Missing revision" },
  { value: "IMPROVEMENT", label: "Improvement" },
  { value: "PARENT_DISCUSSION", label: "Parent discussion" },
];

export function ObservationsPanel({ studentId }: { studentId: string }) {
  const qc = useQueryClient();
  const [type, setType] = useState<ObservationType>("GENERAL");
  const [message, setMessage] = useState("");

  const list = useQuery({
    queryKey: ["observations", studentId],
    queryFn: () => observations.list(studentId),
  });
  const create = useMutation({
    mutationFn: () => observations.create(studentId, { type, message }),
    onSuccess: () => {
      setMessage("");
      qc.invalidateQueries({ queryKey: ["observations", studentId] });
    },
  });
  const remove = useMutation({
    mutationFn: (id: string) => observations.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["observations", studentId] }),
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (message.trim()) create.mutate();
  }

  return (
    <div>
      <h2>Observations</h2>
      <div className="qp-card" style={{ marginBottom: 16 }}>
        <form onSubmit={handleSubmit} className="qp-form">
          <div className="qp-row">
            <div style={{ flex: "0 0 220px" }}>
              <label>Type</label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value as ObservationType)}
              >
                {TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>Note</label>
              <textarea
                rows={2}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="What did you observe?"
              />
            </div>
          </div>
          {create.error ? (
            <div className="qp-error">{(create.error as Error).message}</div>
          ) : null}
          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button
              type="submit"
              className="qp-btn"
              disabled={create.isPending || !message.trim()}
            >
              {create.isPending ? "Saving..." : "Add note"}
            </button>
          </div>
        </form>
      </div>

      <div className="qp-card" style={{ padding: 0 }}>
        {list.isLoading ? (
          <p style={{ padding: 16 }}>Loading...</p>
        ) : list.data && list.data.items.length === 0 ? (
          <p style={{ padding: 16, color: "var(--color-muted)" }}>
            No notes yet.
          </p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {list.data?.items.map((o) => (
              <li
                key={o.id}
                style={{
                  padding: "12px 16px",
                  borderBottom: "1px solid var(--color-border)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "baseline",
                    gap: 12,
                  }}
                >
                  <span style={{ color: "var(--color-muted)", fontSize: "0.8rem" }}>
                    {TYPES.find((t) => t.value === o.type)?.label ?? o.type} ·{" "}
                    {new Date(o.created_at).toLocaleString()}
                  </span>
                  <button
                    className="qp-btn-ghost"
                    style={{ color: "var(--color-danger)", fontSize: "0.8rem" }}
                    onClick={() => {
                      if (confirm("Delete this note?")) remove.mutate(o.id);
                    }}
                  >
                    Delete
                  </button>
                </div>
                <p style={{ margin: "4px 0 0 0" }}>{o.message}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

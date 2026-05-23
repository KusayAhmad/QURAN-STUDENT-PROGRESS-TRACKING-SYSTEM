"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useRef, useState } from "react";

import { admin, type ImportResult } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

export default function ImportPage() {
  const router = useRouter();
  const me = useAuthStore((s) => s.user);
  const qc = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);

  useEffect(() => {
    if (me && me.role !== "ADMIN") router.replace("/dashboard");
  }, [me, router]);

  const mutation = useMutation({
    mutationFn: (f: File) => admin.importExcel(f),
    onSuccess: (data) => {
      setResult(data);
      // Anything that depends on student/progress/analytics state should
      // refetch.
      qc.invalidateQueries({ queryKey: ["students"] });
      qc.invalidateQueries({ queryKey: ["matrix"] });
      qc.invalidateQueries({ queryKey: ["analytics"] });
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (file) mutation.mutate(file);
  }

  function reset() {
    setFile(null);
    setResult(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  if (me && me.role !== "ADMIN") return null;

  return (
    <div>
      <h1>Import Excel</h1>
      <p style={{ color: "var(--color-muted)" }}>
        Upload a workbook (<code>.xlsx</code> or <code>.xlsm</code>) with one or both
        of the following sheets. Column names are case-insensitive and tolerate
        common variants (e.g. <code>name</code> instead of <code>full_name</code>).
      </p>

      <div className="qp-card" style={{ marginBottom: 16 }}>
        <h2>Expected sheets</h2>
        <h3 style={{ fontSize: "1rem" }}>students (optional)</h3>
        <pre
          style={{
            background: "var(--color-bg)",
            padding: 12,
            borderRadius: 8,
            overflow: "auto",
          }}
        >
{`full_name      | gender (MALE/FEMALE/M/F) | guardian_name | guardian_phone
Ali Hassan     | MALE                     | Hassan Sr.    | 0501234567
Fatima Khalid  | F                        |               |`}
        </pre>
        <h3 style={{ fontSize: "1rem" }}>progress (optional)</h3>
        <pre
          style={{
            background: "var(--color-bg)",
            padding: 12,
            borderRadius: 8,
            overflow: "auto",
          }}
        >
{`student_full_name | surah_order | status                                                            | completion_percent
Ali Hassan        | 1           | MASTERED                                                          | 100
Ali Hassan        | 2           | WEAK                                                              | 30`}
        </pre>
        <p style={{ color: "var(--color-muted)", fontSize: "0.85rem" }}>
          Valid statuses: NOT_STARTED, IN_PROGRESS, REVIEW_REQUIRED, WEAK, STRONG,
          MASTERED. Students are matched by name (case-insensitive) within your
          school; missing students in the progress sheet produce a per-row error
          but do not abort the import. Imported progress also writes to the
          per-surah timeline and audit log.
        </p>
      </div>

      <div className="qp-card">
        <form onSubmit={handleSubmit} className="qp-form">
          <div>
            <label>Workbook</label>
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx,.xlsm,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel.sheet.macroenabled.12"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
          {mutation.error ? (
            <div className="qp-error">{(mutation.error as Error).message}</div>
          ) : null}
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button
              type="button"
              className="qp-btn-ghost"
              onClick={reset}
              disabled={mutation.isPending}
            >
              Reset
            </button>
            <button
              type="submit"
              className="qp-btn"
              disabled={!file || mutation.isPending}
            >
              {mutation.isPending ? "Importing..." : "Import"}
            </button>
          </div>
        </form>
      </div>

      {result ? <ResultSummary result={result} /> : null}
    </div>
  );
}

function ResultSummary({ result }: { result: ImportResult }) {
  return (
    <div className="qp-card" style={{ marginTop: 16 }}>
      <h2>Import result</h2>
      <div className="qp-grid qp-grid-3">
        <div className="qp-stat">
          <div className="qp-stat-label">Students created</div>
          <div className="qp-stat-value">{result.students_created}</div>
        </div>
        <div className="qp-stat">
          <div className="qp-stat-label">Students matched</div>
          <div className="qp-stat-value">{result.students_matched}</div>
        </div>
        <div className="qp-stat">
          <div className="qp-stat-label">Progress rows</div>
          <div className="qp-stat-value">{result.progress_recorded}</div>
        </div>
      </div>
      {result.errors.length > 0 ? (
        <div style={{ marginTop: 16 }}>
          <h3>Errors ({result.errors.length})</h3>
          <table className="qp-table">
            <thead>
              <tr>
                <th style={{ width: 100 }}>Sheet</th>
                <th style={{ width: 80 }}>Row</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {result.errors.map((e, idx) => (
                <tr key={idx}>
                  <td>{e.sheet}</td>
                  <td>{e.row}</td>
                  <td style={{ color: "var(--color-danger)" }}>{e.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p style={{ color: "var(--color-muted)" }}>
          No errors. Imported records are now visible across the app.
        </p>
      )}
    </div>
  );
}

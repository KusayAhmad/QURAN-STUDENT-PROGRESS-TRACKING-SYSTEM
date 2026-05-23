"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { type FormEvent, useState } from "react";

import { students } from "@/lib/api";
import type { StudentGender } from "@/lib/types";

export default function StudentsPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [showCreate, setShowCreate] = useState(false);

  const listQuery = useQuery({
    queryKey: ["students", { search, includeArchived }],
    queryFn: () => students.list({ search: search || undefined, include_archived: includeArchived }),
  });

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <h1 style={{ margin: 0 }}>Students</h1>
        <button className="qp-btn" onClick={() => setShowCreate(true)}>
          New student
        </button>
      </div>

      <div className="qp-card" style={{ marginBottom: 16 }}>
        <div className="qp-row">
          <div>
            <label htmlFor="search">Search</label>
            <input
              id="search"
              placeholder="Name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div style={{ flex: "0 0 auto" }}>
            <label>
              <input
                type="checkbox"
                checked={includeArchived}
                onChange={(e) => setIncludeArchived(e.target.checked)}
                style={{ width: "auto", marginRight: 8 }}
              />
              Show archived
            </label>
          </div>
        </div>
      </div>

      <div className="qp-card" style={{ padding: 0 }}>
        {listQuery.isLoading ? (
          <p style={{ padding: 16 }}>Loading...</p>
        ) : listQuery.error ? (
          <p className="qp-error" style={{ padding: 16 }}>
            {(listQuery.error as Error).message}
          </p>
        ) : (
          <table className="qp-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Gender</th>
                <th>Status</th>
                <th>Guardian</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {listQuery.data?.items.map((s) => (
                <tr key={s.id}>
                  <td>
                    <Link href={`/students/${s.id}`}>{s.full_name}</Link>
                  </td>
                  <td>{s.gender}</td>
                  <td>{s.status}</td>
                  <td style={{ color: "var(--color-muted)" }}>
                    {s.guardian_name ?? "-"}
                  </td>
                  <td>
                    <Link href={`/students/${s.id}`}>Open</Link>
                  </td>
                </tr>
              ))}
              {listQuery.data && listQuery.data.items.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    style={{ padding: 24, textAlign: "center", color: "var(--color-muted)" }}
                  >
                    No students yet. Click <strong>New student</strong> to add one.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        )}
      </div>

      {showCreate ? (
        <CreateStudentModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            qc.invalidateQueries({ queryKey: ["students"] });
          }}
        />
      ) : null}
    </div>
  );
}

function CreateStudentModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [fullName, setFullName] = useState("");
  const [gender, setGender] = useState<StudentGender>("MALE");
  const [guardianName, setGuardianName] = useState("");
  const [guardianPhone, setGuardianPhone] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      students.create({
        full_name: fullName,
        gender,
        guardian_name: guardianName || undefined,
        guardian_phone: guardianPhone || undefined,
      }),
    onSuccess: onCreated,
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    mutation.mutate();
  }

  return (
    <div className="qp-overlay" onClick={onClose}>
      <div className="qp-modal" onClick={(e) => e.stopPropagation()}>
        <h2>New student</h2>
        <form onSubmit={handleSubmit} className="qp-form">
          <div>
            <label>Full name</label>
            <input
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
          <div>
            <label>Gender</label>
            <select
              value={gender}
              onChange={(e) => setGender(e.target.value as StudentGender)}
            >
              <option value="MALE">Male</option>
              <option value="FEMALE">Female</option>
            </select>
          </div>
          <div>
            <label>Guardian name (optional)</label>
            <input
              value={guardianName}
              onChange={(e) => setGuardianName(e.target.value)}
            />
          </div>
          <div>
            <label>Guardian phone (optional)</label>
            <input
              value={guardianPhone}
              onChange={(e) => setGuardianPhone(e.target.value)}
            />
          </div>
          {mutation.error ? (
            <div className="qp-error">{(mutation.error as Error).message}</div>
          ) : null}
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button type="button" className="qp-btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="qp-btn"
              disabled={mutation.isPending}
            >
              {mutation.isPending ? "Creating..." : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

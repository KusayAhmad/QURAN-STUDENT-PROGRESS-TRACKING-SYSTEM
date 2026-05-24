"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { type FormEvent, useState } from "react";

import { classes, students, type ClassItem } from "@/lib/api";
import { useT } from "@/lib/useT";
import { useAuthStore } from "@/store/auth";

export default function ClassesPage() {
  const qc = useQueryClient();
  const t = useT();
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "ADMIN";
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<ClassItem | null>(null);
  const [assigning, setAssigning] = useState<ClassItem | null>(null);

  const listQuery = useQuery({
    queryKey: ["classes"],
    queryFn: () => classes.list(),
  });

  const removeMut = useMutation({
    mutationFn: (id: string) => classes.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["classes"] }),
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
        <h1 style={{ margin: 0 }}>{t("classes.title")}</h1>
        {isAdmin ? (
          <button className="qp-btn" onClick={() => setShowCreate(true)}>
            {t("classes.new")}
          </button>
        ) : null}
      </div>

      <div className="qp-card" style={{ padding: 0 }}>
        {listQuery.isLoading ? (
          <p style={{ padding: 16 }}>{t("common.loading")}</p>
        ) : listQuery.data && listQuery.data.length === 0 ? (
          <p style={{ padding: 16, color: "var(--color-muted)" }}>
            {isAdmin ? t("classes.emptyAdmin") : t("classes.empty")}
          </p>
        ) : (
          <table className="qp-table">
            <thead>
              <tr>
                <th>{t("classes.colName")}</th>
                <th>{t("classes.colYear")}</th>
                <th>{t("classes.colActions")}</th>
              </tr>
            </thead>
            <tbody>
              {listQuery.data?.map((c) => (
                <tr key={c.id}>
                  <td style={{ fontWeight: 500 }}>
                    <Link href={`/classes/${c.id}`}>{c.name}</Link>
                  </td>
                  <td style={{ color: "var(--color-muted)" }}>{c.academic_year}</td>
                  <td>
                    <div style={{ display: "flex", gap: 8 }}>
                      <button
                        className="qp-btn-ghost"
                        onClick={() => setAssigning(c)}
                      >
                        {t("classes.assignStudents")}
                      </button>
                      {isAdmin ? (
                        <>
                          <button
                            className="qp-btn-ghost"
                            onClick={() => setEditing(c)}
                          >
                            {t("common.edit")}
                          </button>
                          <button
                            className="qp-btn-ghost"
                            style={{ color: "var(--color-danger)" }}
                            onClick={() => {
                              if (
                                confirm(
                                  t("classes.deleteConfirm").replace(
                                    "{name}",
                                    c.name,
                                  ),
                                )
                              )
                                removeMut.mutate(c.id);
                            }}
                          >
                            {t("common.delete")}
                          </button>
                        </>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showCreate ? (
        <ClassFormModal
          onClose={() => setShowCreate(false)}
          onSaved={() => {
            setShowCreate(false);
            qc.invalidateQueries({ queryKey: ["classes"] });
          }}
        />
      ) : null}

      {editing ? (
        <ClassFormModal
          existing={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            qc.invalidateQueries({ queryKey: ["classes"] });
          }}
        />
      ) : null}

      {assigning ? (
        <AssignStudentsModal
          classItem={assigning}
          onClose={() => setAssigning(null)}
        />
      ) : null}
    </div>
  );
}

function ClassFormModal({
  existing,
  onClose,
  onSaved,
}: {
  existing?: ClassItem;
  onClose: () => void;
  onSaved: () => void;
}) {
  const t = useT();
  const [name, setName] = useState(existing?.name ?? "");
  const [year, setYear] = useState(existing?.academic_year ?? "2025-2026");

  const mutation = useMutation({
    mutationFn: () =>
      existing
        ? classes.update(existing.id, { name, academic_year: year })
        : classes.create({ name, academic_year: year }),
    onSuccess: onSaved,
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    mutation.mutate();
  }

  return (
    <div className="qp-overlay" onClick={onClose}>
      <div className="qp-modal" onClick={(e) => e.stopPropagation()}>
        <h2>{existing ? t("classes.editClass") : t("classes.newClass")}</h2>
        <form onSubmit={handleSubmit} className="qp-form">
          <div>
            <label>{t("classes.className")}</label>
            <input required value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label>{t("classes.academicYear")}</label>
            <input required value={year} onChange={(e) => setYear(e.target.value)} />
          </div>
          {mutation.error ? (
            <div className="qp-error">{(mutation.error as Error).message}</div>
          ) : null}
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button type="button" className="qp-btn-ghost" onClick={onClose}>
              {t("common.cancel")}
            </button>
            <button type="submit" className="qp-btn" disabled={mutation.isPending}>
              {mutation.isPending ? t("common.saving") : t("common.save")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function AssignStudentsModal({
  classItem,
  onClose,
}: {
  classItem: ClassItem;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const t = useT();

  // Load ALL students including archived so admins can manage membership
  // for archived students who may still be assigned to a class.
  const studentsQuery = useQuery({
    queryKey: ["students", "all-for-assign"],
    queryFn: () => students.list({ limit: 200, include_archived: true }),
  });

  const assignMut = useMutation({
    // Use a properly typed payload — `class_id` is part of StudentUpdate.
    mutationFn: (vars: { studentId: string; classId: string | null }) =>
      students.update(vars.studentId, { class_id: vars.classId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["students"] });
      qc.invalidateQueries({ queryKey: ["matrix"] });
    },
  });

  const allStudents = studentsQuery.data?.items ?? [];
  const inClass = allStudents.filter((s) => s.class_id === classItem.id);
  const notInClass = allStudents.filter((s) => s.class_id !== classItem.id);

  return (
    <div className="qp-overlay" onClick={onClose}>
      <div
        className="qp-modal"
        style={{ maxWidth: 600, maxHeight: "80vh", overflow: "auto" }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2>
          {t("classes.assignTitle").replace("{name}", classItem.name)}
        </h2>
        <p style={{ color: "var(--color-muted)", marginTop: 0 }}>
          {t("classes.assignHint")}
        </p>

        {studentsQuery.isLoading ? (
          <p>{t("common.loading")}</p>
        ) : (
          <>
            <h3 style={{ fontSize: "0.95rem", marginTop: 16 }}>
              {t("classes.inClass").replace("{count}", String(inClass.length))}
            </h3>
            {inClass.length === 0 ? (
              <p style={{ color: "var(--color-muted)" }}>{t("classes.noneInClass")}</p>
            ) : (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {inClass.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    className="qp-status qp-status-strong"
                    style={{ cursor: "pointer" }}
                    onClick={() =>
                      assignMut.mutate({ studentId: s.id, classId: null })
                    }
                    title={t("classes.removeHint")}
                  >
                    {s.full_name} ✕
                  </button>
                ))}
              </div>
            )}

            <h3 style={{ fontSize: "0.95rem", marginTop: 16 }}>
              {t("classes.available").replace("{count}", String(notInClass.length))}
            </h3>
            {notInClass.length === 0 ? (
              <p style={{ color: "var(--color-muted)" }}>
                {t("classes.allAssigned")}
              </p>
            ) : (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {notInClass.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    className="qp-status qp-status-not_started"
                    style={{ cursor: "pointer" }}
                    onClick={() =>
                      assignMut.mutate({ studentId: s.id, classId: classItem.id })
                    }
                    title={t("classes.addHint")}
                  >
                    {s.full_name} +
                  </button>
                ))}
              </div>
            )}
          </>
        )}

        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 16 }}>
          <button type="button" className="qp-btn-ghost" onClick={onClose}>
            {t("common.close")}
          </button>
        </div>
      </div>
    </div>
  );
}

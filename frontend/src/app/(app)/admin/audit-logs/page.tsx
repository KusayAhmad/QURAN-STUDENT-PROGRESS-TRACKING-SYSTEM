"use client";

// Admin-only audit log viewer. Surfaces GET /api/v1/admin/audit-logs which
// has been recording every mutation since MVP-3 with no UI consumer.
//
// Pattern mirrors the notifications inbox: filters at the top, paginated
// list below, expandable diff per row. We deliberately don't render the
// raw old/new JSON in the table — it's noisy. Instead we show a compact
// summary line and let the row expand to show the diff blocks.

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Fragment, useState } from "react";

import { admin } from "@/lib/api";
import type { AuditEntityType } from "@/lib/types";
import { useAuthStore } from "@/store/auth";

const ENTITY_TYPES: AuditEntityType[] = [
  "STUDENT",
  "EVALUATION",
  "OBSERVATION",
  "PROGRESS",
  "USER",
  "CLASS",
];

const ACTION_BG: Record<string, string> = {
  CREATE: "var(--status-mastered)",
  UPDATE: "var(--status-in-progress)",
  DELETE: "var(--status-weak)",
  ARCHIVE: "var(--status-review-required)",
};

const PAGE_SIZE = 50;

export default function AuditLogsPage() {
  const user = useAuthStore((s) => s.user);
  const [entityType, setEntityType] = useState<AuditEntityType | "">("");
  const [entityId, setEntityId] = useState("");
  const [offset, setOffset] = useState(0);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["audit-logs", entityType, entityId, offset],
    queryFn: () =>
      admin.listAuditLogs({
        entity_type: entityType || undefined,
        entity_id: entityId || undefined,
        limit: PAGE_SIZE,
        offset,
      }),
    enabled: user?.role === "ADMIN",
  });

  if (user?.role !== "ADMIN") {
    return (
      <div>
        <h1>Audit logs</h1>
        <p className="qp-error">Admins only.</p>
      </div>
    );
  }

  const total = query.data?.total ?? 0;
  const items = query.data?.items ?? [];
  const hasPrev = offset > 0;
  const hasNext = offset + PAGE_SIZE < total;

  return (
    <div>
      <h1>Audit logs</h1>
      <p style={{ color: "var(--color-muted)", marginTop: -4 }}>
        Every mutation that touched the database, oldest-first within each
        page. Filters apply across all pages.
      </p>

      <div className="qp-card" style={{ marginBottom: 16 }}>
        <div className="qp-row">
          <div>
            <label>Entity type</label>
            <select
              value={entityType}
              onChange={(e) => {
                setEntityType(e.target.value as AuditEntityType | "");
                setOffset(0);
              }}
            >
              <option value="">All</option>
              {ENTITY_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Entity ID (optional)</label>
            <input
              value={entityId}
              placeholder="UUID — paste from a row to filter"
              onChange={(e) => {
                setEntityId(e.target.value.trim());
                setOffset(0);
              }}
            />
          </div>
        </div>
      </div>

      <div className="qp-card" style={{ padding: 0 }}>
        {query.isLoading ? (
          <p style={{ padding: 16 }}>Loading...</p>
        ) : query.error ? (
          <p className="qp-error" style={{ padding: 16 }}>
            {(query.error as Error).message}
          </p>
        ) : items.length === 0 ? (
          <p style={{ padding: 16, color: "var(--color-muted)" }}>
            No audit log entries match these filters.
          </p>
        ) : (
          <table className="qp-table">
            <thead>
              <tr>
                <th>When</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Entity ID</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((entry) => {
                const expanded = expandedId === entry.id;
                return (
                  <Fragment key={entry.id}>
                    <tr>
                      <td style={{ whiteSpace: "nowrap", fontSize: "0.85rem" }}>
                        {new Date(entry.created_at).toLocaleString()}
                      </td>
                      <td>
                        <span
                          className="qp-status"
                          style={{
                            background:
                              ACTION_BG[entry.action] ?? "var(--color-muted)",
                          }}
                        >
                          {entry.action}
                        </span>
                      </td>
                      <td style={{ fontSize: "0.85rem" }}>
                        {entry.entity_type}
                      </td>
                      <td
                        style={{
                          fontSize: "0.75rem",
                          fontFamily: "monospace",
                          color: "var(--color-muted)",
                          // Long UUIDs would blow out the column width.
                          maxWidth: 220,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {entry.entity_type === "STUDENT" ? (
                          <Link href={`/students/${entry.entity_id}`}>
                            {entry.entity_id}
                          </Link>
                        ) : (
                          entry.entity_id
                        )}
                      </td>
                      <td>
                        <button
                          className="qp-btn-ghost"
                          style={{ fontSize: "0.8rem" }}
                          onClick={() =>
                            setExpandedId(expanded ? null : entry.id)
                          }
                        >
                          {expanded ? "Hide" : "Diff"}
                        </button>
                      </td>
                    </tr>
                    {expanded ? (
                      <tr>
                        <td colSpan={5} style={{ background: "#fafafa" }}>
                          <DiffPanel entry={entry} />
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <div
        style={{
          display: "flex",
          gap: 8,
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <span style={{ color: "var(--color-muted)", fontSize: "0.85rem" }}>
          {total === 0
            ? "0 entries"
            : `Showing ${offset + 1}–${Math.min(offset + PAGE_SIZE, total)} of ${total}`}
        </span>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className="qp-btn-ghost"
            disabled={!hasPrev}
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
          >
            Previous
          </button>
          <button
            className="qp-btn-ghost"
            disabled={!hasNext}
            onClick={() => setOffset(offset + PAGE_SIZE)}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

// Side-by-side diff. We don't try to highlight per-key changes — keys with
// the same value in both columns are present in both blocks, but JSON is
// short enough that visual scan is fine. If diffs grow large we can add
// per-key delta highlighting later.
function DiffPanel({
  entry,
}: {
  entry: {
    old_value: Record<string, unknown> | null;
    new_value: Record<string, unknown> | null;
  };
}) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 12,
        padding: 12,
      }}
    >
      <DiffBlock title="Before" data={entry.old_value} />
      <DiffBlock title="After" data={entry.new_value} />
    </div>
  );
}

function DiffBlock({
  title,
  data,
}: {
  title: string;
  data: Record<string, unknown> | null;
}) {
  return (
    <div>
      <div
        style={{
          fontSize: "0.75rem",
          color: "var(--color-muted)",
          marginBottom: 4,
          textTransform: "uppercase",
          letterSpacing: "0.05em",
        }}
      >
        {title}
      </div>
      <pre
        style={{
          margin: 0,
          padding: 8,
          background: "white",
          border: "1px solid var(--color-border)",
          borderRadius: 4,
          fontSize: "0.75rem",
          maxHeight: 240,
          overflow: "auto",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {data ? JSON.stringify(data, null, 2) : "(empty)"}
      </pre>
    </div>
  );
}

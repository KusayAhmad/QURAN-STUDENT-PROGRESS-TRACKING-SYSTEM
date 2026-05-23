"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { notifications } from "@/lib/api";
import { TYPE_LABEL } from "@/lib/notifications";

export default function NotificationsPage() {
  const qc = useQueryClient();
  const [unreadOnly, setUnreadOnly] = useState(false);

  const list = useQuery({
    queryKey: ["notifications", "list", { unreadOnly }],
    queryFn: () => notifications.list({ unread_only: unreadOnly, limit: 100 }),
  });

  const markRead = useMutation({
    mutationFn: (id: string) => notifications.markRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAll = useMutation({
    mutationFn: () => notifications.markAllRead(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
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
        <h1 style={{ margin: 0 }}>Notifications</h1>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <label style={{ fontSize: "0.85rem" }}>
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={(e) => setUnreadOnly(e.target.checked)}
              style={{ width: "auto", marginRight: 6 }}
            />
            Unread only
          </label>
          <button
            type="button"
            className="qp-btn-ghost"
            onClick={() => markAll.mutate()}
            disabled={markAll.isPending}
          >
            Mark all read
          </button>
        </div>
      </div>

      <div className="qp-card" style={{ padding: 0 }}>
        {list.isLoading ? (
          <p style={{ padding: 16 }}>Loading...</p>
        ) : list.data && list.data.items.length === 0 ? (
          <p style={{ padding: 16, color: "var(--color-muted)" }}>
            {unreadOnly ? "No unread notifications." : "No notifications yet."}
          </p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {list.data?.items.map((n) => {
              const studentId =
                typeof n.payload?.student_id === "string"
                  ? n.payload.student_id
                  : null;
              return (
                <li
                  key={n.id}
                  className={n.read_at ? "" : "qp-bell-item-unread"}
                  style={{
                    padding: "12px 16px",
                    borderBottom: "1px solid var(--color-border)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 12,
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div
                        style={{
                          display: "flex",
                          gap: 8,
                          alignItems: "center",
                          marginBottom: 4,
                        }}
                      >
                        <span className="qp-role">{TYPE_LABEL[n.type]}</span>
                        <span style={{ color: "var(--color-muted)", fontSize: "0.75rem" }}>
                          {new Date(n.created_at).toLocaleString()}
                        </span>
                        {n.read_at ? null : (
                          <span
                            style={{
                              width: 8,
                              height: 8,
                              borderRadius: 999,
                              background: "var(--color-primary)",
                            }}
                          />
                        )}
                      </div>
                      <div style={{ fontWeight: 500 }}>{n.title}</div>
                      <div style={{ color: "var(--color-muted)", fontSize: "0.85rem" }}>
                        {n.message}
                      </div>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      {studentId ? (
                        <Link
                          href={`/students/${studentId}`}
                          style={{ fontSize: "0.85rem" }}
                          onClick={() => {
                            if (!n.read_at) markRead.mutate(n.id);
                          }}
                        >
                          Open student →
                        </Link>
                      ) : null}
                      {!n.read_at ? (
                        <button
                          type="button"
                          className="qp-btn-ghost"
                          style={{ padding: "2px 8px", fontSize: "0.75rem" }}
                          onClick={() => markRead.mutate(n.id)}
                        >
                          Mark read
                        </button>
                      ) : null}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { notifications, type Notification, type NotificationType } from "@/lib/api";
import { useT } from "@/lib/useT";

export function NotificationBell() {
  const qc = useQueryClient();
  const t = useT();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const countQuery = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: () => notifications.unreadCount(),
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
  });

  const listQuery = useQuery({
    queryKey: ["notifications", "preview"],
    queryFn: () => notifications.list({ limit: 5 }),
    enabled: open,
  });

  const markRead = useMutation({
    mutationFn: (id: string) => notifications.markRead(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const markAll = useMutation({
    mutationFn: () => notifications.markAllRead(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  const unread = countQuery.data?.unread ?? 0;
  const shortLabel = (type: NotificationType) => t(`notifType.${type}` as const);

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        type="button"
        className="qp-bell"
        aria-label={`${t("notifications.title")} (${unread})`}
        onClick={() => setOpen((o) => !o)}
      >
        <span aria-hidden>🔔</span>
        {unread > 0 ? (
          <span className="qp-bell-badge">{unread > 99 ? "99+" : unread}</span>
        ) : null}
      </button>
      {open ? (
        <div className="qp-bell-popover">
          <div className="qp-bell-header">
            <strong>{t("notifications.title")}</strong>
            {unread > 0 ? (
              <button
                type="button"
                className="qp-btn-ghost"
                style={{ padding: "2px 8px", fontSize: "0.75rem" }}
                onClick={() => markAll.mutate()}
                disabled={markAll.isPending}
              >
                {t("notifications.markAllRead")}
              </button>
            ) : null}
          </div>
          {listQuery.isLoading ? (
            <p style={{ padding: 12, color: "var(--color-muted)" }}>{t("common.loading")}</p>
          ) : listQuery.data && listQuery.data.items.length > 0 ? (
            <ul className="qp-bell-list">
              {listQuery.data.items.map((n) => (
                <BellItem
                  key={n.id}
                  notification={n}
                  shortLabel={shortLabel(n.type)}
                  onClick={() => {
                    if (!n.read_at) markRead.mutate(n.id);
                    setOpen(false);
                  }}
                />
              ))}
            </ul>
          ) : (
            <p style={{ padding: 12, color: "var(--color-muted)" }}>
              {t("notifications.allCaughtUp")}
            </p>
          )}
          <div className="qp-bell-footer">
            <Link
              href="/notifications"
              onClick={() => setOpen(false)}
              style={{ fontSize: "0.85rem" }}
            >
              {t("notifications.viewAll")}
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function BellItem({
  notification,
  shortLabel,
  onClick,
}: {
  notification: Notification;
  shortLabel: string;
  onClick: () => void;
}) {
  const studentId =
    typeof notification.payload?.student_id === "string"
      ? notification.payload.student_id
      : null;
  const href = studentId ? `/students/${studentId}` : "/notifications";
  return (
    <li
      className={`qp-bell-item ${notification.read_at ? "" : "qp-bell-item-unread"}`}
    >
      <Link href={href} onClick={onClick}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
          <strong style={{ fontSize: "0.85rem" }}>{shortLabel}</strong>
          <span style={{ color: "var(--color-muted)", fontSize: "0.7rem" }}>
            {new Date(notification.created_at).toLocaleDateString()}
          </span>
        </div>
        <div style={{ fontSize: "0.85rem", marginTop: 2 }}>{notification.title}</div>
        <div
          style={{
            color: "var(--color-muted)",
            fontSize: "0.75rem",
            marginTop: 2,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {notification.message}
        </div>
      </Link>
    </li>
  );
}

"use client";

import { useT } from "@/lib/useT";
import type { MemorizationStatus } from "@/lib/types";

export function StatusBadge({
  status,
  onClick,
}: {
  status: MemorizationStatus;
  onClick?: () => void;
}) {
  const t = useT();
  const cls = `qp-status qp-status-${status.toLowerCase()}`;
  const label = t(`status.${status}` as const);
  if (onClick) {
    return (
      <button type="button" className={cls} onClick={onClick}>
        {label}
      </button>
    );
  }
  return <span className={cls}>{label}</span>;
}

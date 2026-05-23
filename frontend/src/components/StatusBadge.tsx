import type { MemorizationStatus } from "@/lib/types";

const LABELS: Record<MemorizationStatus, string> = {
  NOT_STARTED: "Not started",
  IN_PROGRESS: "In progress",
  REVIEW_REQUIRED: "Review required",
  WEAK: "Weak",
  STRONG: "Strong",
  MASTERED: "Mastered",
};

export function StatusBadge({
  status,
  onClick,
}: {
  status: MemorizationStatus;
  onClick?: () => void;
}) {
  const cls = `qp-status qp-status-${status.toLowerCase()}`;
  if (onClick) {
    return (
      <button type="button" className={cls} onClick={onClick}>
        {LABELS[status]}
      </button>
    );
  }
  return <span className={cls}>{LABELS[status]}</span>;
}

export const STATUS_LABEL = LABELS;

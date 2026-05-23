import type { NotificationType } from "@/lib/api";

/** Centralized human-readable labels for notification types. */
export const TYPE_LABEL: Record<NotificationType, string> = {
  PROGRESS_REGRESSED: "Regression",
  LOW_EVALUATION: "Low evaluation",
  STUDENT_ADDED: "New student",
  OVERDUE_REVIEW: "Overdue review",
  MANUAL: "Notice",
};

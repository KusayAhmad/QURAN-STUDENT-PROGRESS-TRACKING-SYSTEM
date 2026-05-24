// Types mirroring the FastAPI v1 schemas. Kept hand-written (small surface)
// rather than generated, to avoid a build-time dependency on the OpenAPI spec.

export type UserRole = "ADMIN" | "TEACHER";

export type StudentGender = "MALE" | "FEMALE";
export type StudentStatus = "ACTIVE" | "ARCHIVED" | "GRADUATED";

export type MemorizationStatus =
  | "NOT_STARTED"
  | "IN_PROGRESS"
  | "REVIEW_REQUIRED"
  | "WEAK"
  | "STRONG"
  | "MASTERED";

export const MEMORIZATION_STATUSES: MemorizationStatus[] = [
  "NOT_STARTED",
  "IN_PROGRESS",
  "REVIEW_REQUIRED",
  "WEAK",
  "STRONG",
  "MASTERED",
];

export type EvaluationType =
  | "ORAL_RECITATION"
  | "REVISION_EXAM"
  | "MONTHLY_REVIEW"
  | "ACCURACY_TEST"
  | "OTHER";

export type ObservationType =
  | "DAILY_NOTE"
  | "WEAK_PRONUNCIATION"
  | "MISSING_REVISION"
  | "IMPROVEMENT"
  | "PARENT_DISCUSSION"
  | "GENERAL";

export type AuditAction = "CREATE" | "UPDATE" | "DELETE" | "ARCHIVE";

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface CurrentUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  school_id: string | null;
  is_active: boolean;
}

export interface Student {
  id: string;
  school_id: string;
  class_id: string | null;
  full_name: string;
  gender: StudentGender;
  birth_date: string | null;
  enrollment_date: string | null;
  guardian_name: string | null;
  guardian_phone: string | null;
  notes: string | null;
  status: StudentStatus;
  created_at: string;
  updated_at: string;
}

export interface PaginatedStudents {
  total: number;
  limit: number;
  offset: number;
  items: Student[];
}

export interface Surah {
  id: number;
  surah_order: number;
  surah_name_ar: string;
  surah_name_en: string;
  ayah_count: number;
  juz_no: number;
  hizb_no: number;
}

export interface Progress {
  id: string;
  student_id: string;
  surah_id: number;
  teacher_id: string | null;
  status: MemorizationStatus;
  score: number | null;
  completion_percent: number;
  last_reviewed_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Evaluation {
  id: string;
  student_id: string;
  teacher_id: string | null;
  type: EvaluationType;
  exam_date: string;
  tajweed_score: number | null;
  accuracy_score: number | null;
  fluency_score: number | null;
  retention_score: number | null;
  speed_score: number | null;
  confidence_score: number | null;
  overall_score: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedEvaluations {
  total: number;
  limit: number;
  offset: number;
  items: Evaluation[];
}

export interface Observation {
  id: string;
  student_id: string;
  teacher_id: string | null;
  type: ObservationType;
  message: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedObservations {
  total: number;
  limit: number;
  offset: number;
  items: Observation[];
}

export interface ProgressHistoryEntry {
  id: string;
  progress_id: string;
  student_id: string;
  surah_id: number;
  teacher_id: string | null;
  status: MemorizationStatus;
  score: number | null;
  completion_percent: number;
  notes: string | null;
  action: AuditAction;
  recorded_at: string;
}

export interface StatusCounts {
  NOT_STARTED: number;
  IN_PROGRESS: number;
  REVIEW_REQUIRED: number;
  WEAK: number;
  STRONG: number;
  MASTERED: number;
}

export interface StudentAnalytics {
  student_id: string;
  full_name: string;
  total_surahs: number;
  counts_by_status: StatusCounts;
  mastery_percent: number;
  avg_completion_pct: number;
  mastered_surah_ids: number[];
  weak_surah_ids: number[];
  review_required_surah_ids: number[];
  last_activity_at: string | null;
  recent_evaluations_avg_score: number | null;
  recent_evaluations_count: number;
}

export interface SchoolAnalytics {
  school_id: string;
  student_count: number;
  avg_mastery_percent: number;
  avg_completion_pct: number;
  counts_by_status: StatusCounts;
}

// ---- Revision suggestions (§12-C) ----
export type RevisionReason =
  | "WEAK"
  | "REVIEW_REQUIRED"
  | "STALE_MASTERED"
  | "STALE_STRONG"
  | "IN_PROGRESS";

export interface RevisionSuggestion {
  surah_id: number;
  surah_name_en: string;
  surah_name_ar: string;
  current_status: MemorizationStatus;
  completion_percent: number;
  last_reviewed_at: string | null;
  days_since_review: number | null;
  reason: RevisionReason;
  priority_score: number;
}

export interface RevisionSuggestionList {
  student_id: string;
  generated_at: string;
  suggestions: RevisionSuggestion[];
}

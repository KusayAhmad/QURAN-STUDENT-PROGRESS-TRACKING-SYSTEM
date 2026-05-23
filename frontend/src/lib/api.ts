// Typed fetch wrapper. Reads the token from the auth store on every request,
// so once a user logs in, every subsequent request is authorized automatically.
// On 401 we clear the auth store; the AuthGuard component then redirects to /login.

import { useAuthStore } from "@/store/auth";
import type {
  CurrentUser,
  Evaluation,
  EvaluationType,
  MemorizationStatus,
  Observation,
  ObservationType,
  PaginatedEvaluations,
  PaginatedObservations,
  PaginatedStudents,
  Progress,
  ProgressHistoryEntry,
  SchoolAnalytics,
  Student,
  StudentAnalytics,
  StudentGender,
  Surah,
  TokenPair,
  UserRole,
} from "@/lib/types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown, message: string) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

let refreshPromise: Promise<TokenPair | null> | null = null;

async function attemptTokenRefresh(): Promise<TokenPair | null> {
  const { refreshToken } = useAuthStore.getState();
  if (!refreshToken) return null;
  try {
    const res = await fetch(`${BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return null;
    const tokens: TokenPair = await res.json();
    useAuthStore.getState().setTokens(tokens.access_token, tokens.refresh_token);
    return tokens;
  } catch {
    return null;
  }
}

async function request<T>(
  path: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...((init.headers as Record<string, string>) ?? {}),
  };

  const token = useAuthStore.getState().accessToken;
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }

  let body: BodyInit | undefined = init.body as BodyInit | undefined;
  if (init.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(init.json);
  }

  const res = await fetch(`${BASE}/api/v1${path}`, {
    ...init,
    headers,
    body,
  });

  if (res.status === 401) {
    // Attempt a single-flight token refresh before clearing auth
    if (!refreshPromise) {
      refreshPromise = attemptTokenRefresh().finally(() => {
        refreshPromise = null;
      });
    }
    const refreshed = await refreshPromise;
    if (refreshed) {
      // Retry the original request with the new token
      headers.Authorization = `Bearer ${refreshed.access_token}`;
      const retry = await fetch(`${BASE}/api/v1${path}`, {
        ...init,
        headers,
        body,
      });
      if (retry.status === 204) return undefined as T;
      const retryText = await retry.text();
      let retryParsed: unknown = null;
      try {
        retryParsed = retryText ? JSON.parse(retryText) : null;
      } catch {
        if (!retry.ok) throw new ApiError(retry.status, null, `HTTP ${retry.status}`);
        throw new ApiError(retry.status, null, "Invalid JSON response");
      }
      if (!retry.ok) {
        if (retry.status === 401) {
          useAuthStore.getState().clear();
        }
        const detail =
          (retryParsed && typeof retryParsed === "object" && "detail" in retryParsed
            ? (retryParsed as { detail: unknown }).detail
            : null) ?? `HTTP ${retry.status}`;
        const msg = typeof detail === "string" ? detail : JSON.stringify(detail);
        throw new ApiError(retry.status, retryParsed, msg);
      }
      return retryParsed as T;
    }
    useAuthStore.getState().clear();
  }

  if (res.status === 204) {
    return undefined as T;
  }

  const text = await res.text();
  let parsed: unknown = null;
  try {
    parsed = text ? JSON.parse(text) : null;
  } catch {
    if (!res.ok) throw new ApiError(res.status, null, `HTTP ${res.status}`);
    throw new ApiError(res.status, null, "Invalid JSON response");
  }

  if (!res.ok) {
    const detail =
      (parsed && typeof parsed === "object" && "detail" in parsed
        ? (parsed as { detail: unknown }).detail
        : null) ?? `HTTP ${res.status}`;
    const msg = typeof detail === "string" ? detail : JSON.stringify(detail);
    throw new ApiError(res.status, parsed, msg);
  }

  return parsed as T;
}

// ---- Auth ----
export const auth = {
  login: (email: string, password: string) =>
    request<TokenPair>("/auth/login", { method: "POST", json: { email, password } }),
  me: () => request<CurrentUser>("/auth/me"),
  refresh: (refresh_token: string) =>
    request<TokenPair>("/auth/refresh", { method: "POST", json: { refresh_token } }),
};

// ---- Students ----
export const students = {
  list: (params: {
    search?: string;
    include_archived?: boolean;
    limit?: number;
    offset?: number;
  } = {}) => {
    const qs = new URLSearchParams();
    if (params.search) qs.set("search", params.search);
    if (params.include_archived) qs.set("include_archived", "true");
    qs.set("limit", String(params.limit ?? 50));
    qs.set("offset", String(params.offset ?? 0));
    return request<PaginatedStudents>(`/students?${qs.toString()}`);
  },
  get: (id: string) => request<Student>(`/students/${id}`),
  create: (data: {
    full_name: string;
    gender: StudentGender;
    guardian_name?: string;
    guardian_phone?: string;
    notes?: string;
  }) => request<Student>("/students", { method: "POST", json: data }),
  update: (id: string, data: Partial<Student>) =>
    request<Student>(`/students/${id}`, { method: "PUT", json: data }),
  archive: (id: string) =>
    request<void>(`/students/${id}`, { method: "DELETE" }),
};

// ---- Surahs ----
export const surahs = {
  list: () => request<Surah[]>("/surahs"),
  get: (id: number) => request<Surah>(`/surahs/${id}`),
};

// ---- Progress ----
export const progress = {
  listForStudent: (studentId: string) =>
    request<Progress[]>(`/students/${studentId}/progress`),
  upsert: (
    studentId: string,
    data: {
      surah_id: number;
      status: MemorizationStatus;
      score?: number | null;
      completion_percent: number;
      notes?: string | null;
    },
  ) =>
    request<Progress>(`/students/${studentId}/progress`, {
      method: "POST",
      json: data,
    }),
  update: (
    progressId: string,
    data: { status?: MemorizationStatus; score?: number | null; completion_percent?: number },
  ) => request<Progress>(`/progress/${progressId}`, { method: "PUT", json: data }),
  timeline: (studentId: string, surahId: number) =>
    request<ProgressHistoryEntry[]>(
      `/students/${studentId}/surahs/${surahId}/timeline`,
    ),
};

// ---- Evaluations ----
export const evaluations = {
  list: (studentId: string, limit = 50) =>
    request<PaginatedEvaluations>(
      `/students/${studentId}/evaluations?limit=${limit}`,
    ),
  create: (
    studentId: string,
    data: {
      type: EvaluationType;
      exam_date: string;
      tajweed_score?: number | null;
      accuracy_score?: number | null;
      fluency_score?: number | null;
      retention_score?: number | null;
      speed_score?: number | null;
      confidence_score?: number | null;
      overall_score?: number | null;
      notes?: string | null;
    },
  ) =>
    request<Evaluation>(`/students/${studentId}/evaluations`, {
      method: "POST",
      json: data,
    }),
  remove: (evaluationId: string) =>
    request<void>(`/evaluations/${evaluationId}`, { method: "DELETE" }),
};

// ---- Observations ----
export const observations = {
  list: (studentId: string, limit = 50) =>
    request<PaginatedObservations>(
      `/students/${studentId}/observations?limit=${limit}`,
    ),
  create: (
    studentId: string,
    data: { type?: ObservationType; message: string },
  ) =>
    request<Observation>(`/students/${studentId}/observations`, {
      method: "POST",
      json: data,
    }),
  remove: (observationId: string) =>
    request<void>(`/observations/${observationId}`, { method: "DELETE" }),
};

// ---- Analytics ----
export const analytics = {
  student: (studentId: string) =>
    request<StudentAnalytics>(`/analytics/student/${studentId}`),
  school: () => request<SchoolAnalytics>("/analytics/school"),
};

// ---- Admin ----
export interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  school_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ImportResult {
  students_created: number;
  students_matched: number;
  progress_recorded: number;
  errors: { sheet: string; row: number; message: string }[];
}

// ---- Matrix ----
export interface MatrixCell {
  surah_id: number;
  status: MemorizationStatus;
  completion_percent: number;
}

export interface MatrixStudent {
  id: string;
  full_name: string;
  class_id: string | null;
  cells: MatrixCell[];
}

export interface MatrixView {
  surahs: Surah[];
  students: MatrixStudent[];
}

export const matrixApi = {
  get: (params: { class_id?: string; include_archived?: boolean } = {}) => {
    const qs = new URLSearchParams();
    if (params.class_id) qs.set("class_id", params.class_id);
    if (params.include_archived) qs.set("include_archived", "true");
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<MatrixView>(`/students/matrix${suffix}`);
  },
};

export const admin = {
  listUsers: () => request<AdminUser[]>("/admin/users"),
  createUser: (data: {
    name: string;
    email: string;
    password: string;
    role?: UserRole;
  }) => request<AdminUser>("/admin/users", { method: "POST", json: data }),
  updateUser: (
    userId: string,
    data: {
      name?: string;
      role?: UserRole;
      is_active?: boolean;
      password?: string;
    },
  ) =>
    request<AdminUser>(`/admin/users/${userId}`, { method: "PUT", json: data }),
  // The import endpoint is multipart, so it needs its own fetch path that
  // skips the JSON Content-Type the request() helper would otherwise set.
  importExcel: async (file: File): Promise<ImportResult> => {
    const token = useAuthStore.getState().accessToken;
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`${BASE}/api/v1/admin/import`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body: fd,
    });
    if (res.status === 401) useAuthStore.getState().clear();
    const text = await res.text();
    let parsed: unknown = null;
    try {
      parsed = text ? JSON.parse(text) : null;
    } catch {
      if (!res.ok) throw new ApiError(res.status, null, `HTTP ${res.status}`);
      throw new ApiError(res.status, null, "Invalid JSON response");
    }
    if (!res.ok) {
      const detail =
        (parsed && typeof parsed === "object" && "detail" in parsed
          ? (parsed as { detail: unknown }).detail
          : null) ?? `HTTP ${res.status}`;
      const msg = typeof detail === "string" ? detail : JSON.stringify(detail);
      throw new ApiError(res.status, parsed, msg);
    }
    return parsed as ImportResult;
  },
};

// ---- Notifications ----
export type NotificationType =
  | "PROGRESS_REGRESSED"
  | "LOW_EVALUATION"
  | "STUDENT_ADDED"
  | "OVERDUE_REVIEW"
  | "MANUAL";

export interface Notification {
  id: string;
  recipient_user_id: string;
  school_id: string | null;
  type: NotificationType;
  title: string;
  message: string;
  payload: Record<string, unknown> | null;
  read_at: string | null;
  created_at: string;
}

export interface PaginatedNotifications {
  total: number;
  limit: number;
  offset: number;
  items: Notification[];
}

export const notifications = {
  list: (params: { unread_only?: boolean; limit?: number; offset?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.unread_only) qs.set("unread_only", "true");
    qs.set("limit", String(params.limit ?? 50));
    qs.set("offset", String(params.offset ?? 0));
    return request<PaginatedNotifications>(`/notifications?${qs.toString()}`);
  },
  unreadCount: () => request<{ unread: number }>("/notifications/unread-count"),
  markRead: (id: string) =>
    request<Notification>(`/notifications/${id}/read`, { method: "POST" }),
  markAllRead: () =>
    request<{ updated: number }>("/notifications/read-all", { method: "POST" }),
};

export { ApiError };

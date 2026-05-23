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
    useAuthStore.getState().clear();
  }

  if (res.status === 204) {
    return undefined as T;
  }

  const text = await res.text();
  const parsed = text ? JSON.parse(text) : null;

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
    request<Student>(`/students/${id}`, { method: "DELETE" }),
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

export { ApiError };

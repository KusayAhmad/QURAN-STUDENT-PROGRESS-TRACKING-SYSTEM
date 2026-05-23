# Architecture

This document captures the long-term blueprint for the Quran Student Progress
Tracking System. MVP-1 (this repository's current state) implements the
foundational slice; later phases extend from here without re-architecting.

## 1. Vision

A multi-tenant Quran memorization & progress intelligence platform that
replaces color-coded Excel spreadsheets with a queryable database, multi-user
access, audit trails, historical tracking, and analytics.

Core formula: **Student × Surah × Status × Time → Progress Intelligence**

## 2. Domain model

```
School (tenant)
 └── Class
      └── Student
           ├── MemorizationProgress(student, surah) -- core "Excel cell"
           ├── Evaluation                            -- exam scores (MVP-2)
           └── Observation                           -- teacher notes (MVP-2)

User (Admin | Teacher) ─ belongs to School
QuranSurah (114, seeded, read-only)
AuditLog (MVP-3)
```

### Memorization status (replaces Excel cell colors)

```
NOT_STARTED → IN_PROGRESS → REVIEW_REQUIRED → WEAK → STRONG → MASTERED
```

This enum is the single source of truth — no color-as-data anti-patterns.

## 3. Technology stack

| Layer | Choice | Rationale |
|---|---|---|
| Backend framework | FastAPI | Async, OpenAPI for free, ergonomic Pydantic integration |
| ORM | SQLAlchemy 2.0 (async) | Mature, supports async + sync, portable across DBs |
| Migrations | Alembic | Standard pairing with SQLAlchemy |
| Database | PostgreSQL 16 | Native UUID, JSONB for audit logs, mature |
| Validation | Pydantic 2 | Fast, ergonomic, used by FastAPI |
| Auth | JWT (HS256) + Argon2 | Argon2 for password hashing, JWT for stateless API |
| Frontend | Next.js 15 + TypeScript | App Router, RSC, good RTL support |
| Cache / queue | Redis + Celery (MVP-3+) | For analytics caching and async notifications |
| Container | Docker + docker-compose (dev), K8s (prod, later) | |

## 4. Layering

```
HTTP request
 ↓
API router (app/api/v1/routes/*.py)
 ↓
Service (app/services/*.py)        -- business rules
 ↓
Repository (app/repositories/*.py) -- data access
 ↓
ORM model (app/models/*.py)
 ↓
Database
```

Routers are thin: parse input, call a service, serialize output. Services own
the business rules and tenant checks. Repositories are pure SQL/ORM.

## 5. Multi-tenancy

Every `Student` and (transitively) every `MemorizationProgress` row carries a
`school_id`. The `SchoolUser` FastAPI dependency rejects callers without a
school. Every service-layer query filters by `school_id`. There is no global
view; cross-tenant access requires an Admin endpoint that does not yet exist.

## 6. Key design choices

### Idempotent progress upsert

`POST /students/{id}/progress` is keyed by `(student_id, surah_id)`. Re-posting
with the same surah does not duplicate — it overwrites. This matches the
mental model of "click a cell, change its color".

### Soft delete

`DELETE /students/{id}` flips `status` to `ARCHIVED`. Hard delete is
intentionally not exposed — student history must survive.

### Portable UUID type

The custom `GUID` SQLAlchemy type uses native PostgreSQL `UUID` in production
and `CHAR(36)` in SQLite tests. This lets the entire test suite run in-memory
in ~10 seconds without a Postgres container.

### Token strategy

- Access token: 60 min, carries `sub` (user id) + `role`.
- Refresh token: 14 days, carries only `sub`.
- Token type is encoded in the `type` claim so a stolen access token cannot be
  used at the refresh endpoint and vice versa.

### Audit by explicit call (MVP-3)

Every mutating service function calls `audit_service.record(...)` after the
write. We considered SQLAlchemy `before_flush` event listeners, but the
explicit-call pattern is easier to reason about: actor is unambiguous, diffs
are human-readable JSON, and tests can assert on audit records without
ContextVar tricks. The trade-off is forgetting to call `record()` in a new
mutation — caught in tests for the happy path.

### Append-only progress history (MVP-3)

`memorization_progress` holds the *current* state. `progress_history` holds
every prior version, written by the same service that updates the live row.
This is what powers the per-surah timeline endpoint
(blueprint §12-A: `Baqarah: Weak → Review → Strong → Mastered`). Hard delete
of `memorization_progress` cascades to history; we currently never hard-delete
progress, so history is effectively immutable.

## 7. Database schema (current, MVP-3)

| Table | Purpose | Key constraints |
|---|---|---|
| `schools` | Tenants | — |
| `users` | Login accounts | `email` unique |
| `classes` | Group of students under a teacher | FK school, FK teacher |
| `students` | Person being tracked | FK school, FK class (nullable), `status` enum |
| `quran_surahs` | 114 surahs, read-only | `surah_order` unique |
| `memorization_progress` | Core (student, surah) row | UNIQUE(student_id, surah_id), CHECK score 0–100, CHECK percent 0–100 |
| `evaluations` | Exam scoring (6 axes + overall + type + date) | CHECK each score 0–100, FK student, FK teacher |
| `observations` | Typed teacher notes | FK student, FK teacher |
| `progress_history` | Append-only snapshot per progress write | FK progress, FK teacher |
| `audit_logs` | Append-only mutation trail (actor, action, old/new JSON) | FK actor, FK school |

## 7a. Analytics definitions (MVP-2)

The `AnalyticsService` exposes three views: per-student, per-class, per-school.
All KPIs are computed at request time (no caching yet — Redis comes in MVP-3+).

| Metric | Formula |
|---|---|
| `total_surahs` | `SELECT count(*) FROM quran_surahs` (114 in prod) |
| `mastery_percent` | `count(status=MASTERED) / total_surahs * 100` |
| `avg_completion_pct` | `mean(completion_percent)` over recorded surahs |
| `counts_by_status` | Histogram. Surahs without a row roll into `NOT_STARTED`. |
| `recent_evaluations_avg_score` | `mean(overall_score)` over the 5 most-recent evaluations |
| `last_activity_at` | `max(updated_at)` across `memorization_progress` and `evaluations` |

Class- and school-level KPIs aggregate the above across all `ACTIVE` students
(archived students are excluded). For class/school `counts_by_status`, the
"expected slot count" is `total_surahs × student_count` so percentages remain
meaningful when not all students have touched all surahs.

## 8. RBAC

MVP-1 defines two roles:

- `ADMIN`: future cross-tenant ops.
- `TEACHER`: tenant-scoped CRUD.

The `require_roles(...)` dependency enforces role allow-lists. Most endpoints
just require `SchoolUser` (any role + has school).

## 9. Roadmap

| Phase | Slice | Adds |
|---|---|---|
| **MVP-1** ✓ | Auth + Students + Surahs + Progress | The Excel replacement |
| **MVP-2** ✓ | Evaluations + Observations + Analytics | 6-axis exam scoring, typed teacher notes, student/class/school KPIs, evaluation-trend time series, evaluation update endpoint |
| **MVP-3** ✓ | Audit logs + Versioned progress history + Admin endpoints | Per-mutation audit trail, per-surah status timeline, classes CRUD, admin user list |
| Phase-2 | Multi-school admin, notifications, PWA, Excel import | Scale & onboarding |
| Phase-3 | AI revision suggestions, predictive risk, parent/student portals | Differentiators |

## 10. Known limitations & deferred work

- `quran_surahs.juz_no` / `hizb_no` store the *starting* juz/hizb. A full
  ayah-level mapping (so a query like "all ayahs in juz 1" works) is deferred
  to a future migration.
- No rate limiting yet (planned: `slowapi`).
- No notifications (Celery + email/push planned for Phase-2).
- No analytics caching yet — every `/analytics/...` request hits Postgres.
  Redis-backed read-through caching is planned for Phase-2 once query volume
  warrants it.
- No public CRUD for users yet (only `GET /admin/users`); creating teacher
  accounts still requires the seed script. Full admin user management
  (create/disable/role change) is a Phase-2 task.
- Frontend is a skeleton — the Quran matrix UI, login form, student profile,
  and admin screens are not yet built. The backend is feature-complete for
  MVP-3 and is the priority of the next slice.



## 11. Frontend (current state)

Built on Next.js 16 + React 19 with the App Router, in pure client-component
mode for simplicity. The frontend talks to the backend via a hand-written
typed fetch wrapper (`src/lib/api.ts`); we deliberately did not generate
types from the OpenAPI spec to avoid a build-time dependency.

Pages:
- `/login` — email + password against `/auth/login`, tokens persisted in
  `localStorage` via Zustand.
- `/dashboard` — school KPI tiles + status histogram.
- `/students` — list, search, archive filter, modal-based create.
- `/students/[id]` — three tabs:
  1. *Memorization matrix*: 114 rows, click any status pill to edit.
     Click "History" to open the per-surah timeline modal.
  2. *Evaluations*: 6-axis form + list + delete.
  3. *Observations*: typed teacher notes.

Decisions worth flagging:
- No Tailwind / no MUI. Hand-rolled CSS in `globals.css`. Fast to ship and
  trivial to swap later if we add MUI DataGrid for a multi-student matrix.
- Auth guard is client-side only (`AuthGuard` component reads the Zustand
  store and redirects). Server-side auth would require shipping the token
  via cookies; deferred.
- The "matrix" is rendered as a vertical list of 114 rows for one student,
  not the original Excel two-axis grid. Single-student is the more common
  view in a school day; the multi-student grid (rows = students, cols = 114
  surahs) needs a virtualized DataGrid and is a Phase-2 add.

## 12. Source of truth

If this document and the code disagree, the code wins. Keep this document in
sync via PR.

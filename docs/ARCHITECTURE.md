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
in ~2 seconds without a Postgres container.

### Token strategy

- Access token: 60 min, carries `sub` (user id) + `role`.
- Refresh token: 14 days, carries only `sub`.
- Token type is encoded in the `type` claim so a stolen access token cannot be
  used at the refresh endpoint and vice versa.

## 7. Database schema (current, MVP-1)

| Table | Purpose | Key constraints |
|---|---|---|
| `schools` | Tenants | — |
| `users` | Login accounts | `email` unique |
| `classes` | Group of students under a teacher | FK school, FK teacher |
| `students` | Person being tracked | FK school, FK class (nullable), `status` enum |
| `quran_surahs` | 114 surahs, read-only | `surah_order` unique |
| `memorization_progress` | Core (student, surah) row | UNIQUE(student_id, surah_id), CHECK score 0–100, CHECK percent 0–100 |

Tables planned for later phases: `evaluations`, `observations`, `audit_logs`,
`progress_history`.

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
| MVP-2 | Evaluations + Notes + Basic analytics | Tajweed/fluency scores, completion %, weak surahs |
| MVP-3 | Audit logs + Versioned progress history + Admin UI | Production-ready observability |
| Phase-2 | Multi-school admin, notifications, PWA, Excel import | Scale & onboarding |
| Phase-3 | AI revision suggestions, predictive risk, parent/student portals | Differentiators |

## 10. Known limitations & deferred work

- `quran_surahs.juz_no` / `hizb_no` store the *starting* juz/hizb. A full
  ayah-level mapping (so a query like "all ayahs in juz 1" works) is deferred
  to a future migration.
- No rate limiting yet (planned: `slowapi`).
- No audit logging yet (MVP-3).
- No notifications (Celery + email/push planned for Phase-2).
- Frontend is a skeleton — the Quran matrix UI, login form, and student
  profile screens are not yet built.

## 11. Source of truth

If this document and the code disagree, the code wins. Keep this document in
sync via PR.

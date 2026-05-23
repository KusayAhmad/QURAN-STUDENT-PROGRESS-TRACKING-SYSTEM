# Quran Student Progress Tracking System

A web platform for teachers and supervisors to track Quran memorization
progress, replacing color-coded Excel spreadsheets with a real database,
multi-user access, audit trails, and analytics.

This repository contains **MVP-1**: authentication, student management, the
Quran surah catalog, and the memorization progress engine — i.e. the direct
Excel-replacement slice. See `docs/ARCHITECTURE.md` for the full long-term
blueprint and roadmap.

## Status

| Slice | Module | Status |
|---|---|---|
| MVP-1 | Auth (login, refresh, /me, RBAC) | Done |
| MVP-1 | Students CRUD (tenant-scoped, soft delete) | Done |
| MVP-1 | Quran surahs (114 seeded) | Done |
| MVP-1 | Memorization progress upsert + list | Done |
| MVP-1 | Frontend skeleton (Next.js) | Done |
| MVP-2 | Evaluations (6-axis scoring) | Done |
| MVP-2 | Observations / teacher notes | Done |
| MVP-2 | Analytics (student / class / school KPIs) | Done |
| MVP-3 | Audit logs on every mutation | Done |
| MVP-3 | Versioned progress history + timeline endpoint | Done |
| MVP-3 | Classes CRUD (admin-only writes) | Done |
| MVP-3 | Admin user list + role-gated routes | Done |
| Frontend | Login + auth (JWT in Zustand) | Done |
| Frontend | Dashboard (school-wide KPIs) | Done |
| Frontend | Students list + create + archive | Done |
| Frontend | Student profile with Quran matrix UI | Done |
| Frontend | Evaluations panel (6-axis form, list, delete) | Done |
| Frontend | Observations panel (typed notes) | Done |
| Frontend | Per-surah timeline modal | Done |

## Repository layout

```
backend/      FastAPI + SQLAlchemy + Alembic (Python 3.11)
frontend/     Next.js 15 + TypeScript skeleton
infra/        docker-compose for local dev
docs/         Architecture & design docs
```

## Quickstart (Docker)

```bash
cd infra
docker compose up --build
```

Then:

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

The backend container automatically:
1. Applies Alembic migrations
2. Seeds the 114 surahs
3. Creates demo users:
   - `admin@example.com` / `admin123!` (ADMIN)
   - `teacher@example.com` / `teacher123!` (TEACHER)

## Quickstart (local, no Docker)

### Backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Tests run against in-memory SQLite — no Postgres needed
pytest

# To run the server, set DATABASE_URL to a real Postgres
export DATABASE_URL='postgresql+asyncpg://quran:quran@localhost:5432/quran'
export JWT_SECRET_KEY='replace-with-long-random-string'
alembic upgrade head
python -m seeds.seed --demo-users
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local   # points at http://localhost:8000 by default
npm install
npm run dev                        # http://localhost:3000
```

The login page accepts the demo credentials seeded by the backend
(`teacher@example.com` / `teacher123!` or `admin@example.com` / `admin123!`).
After login the app stores tokens in `localStorage` so refresh keeps you in.

### Frontend stack
- Next.js 16 + React 19 (App Router, client components)
- TanStack Query for server state, Zustand for auth tokens
- Plain CSS — no Tailwind/MUI for the MVP. The Quran matrix is rendered
  as a simple list of 114 rows (one per surah) with a click-to-edit
  status pill, which is faster to ship than a real DataGrid and
  performs fine for a single-student view. A multi-student matrix
  (à la the original Excel) would be a future addition on top of MUI
  DataGrid.

## API summary (v1)

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/auth/login` | Returns access + refresh token |
| POST | `/api/v1/auth/refresh` | Rotate access token |
| GET | `/api/v1/auth/me` | Current user |
| GET | `/api/v1/students` | Paginated, tenant-scoped, search + archive filter |
| POST | `/api/v1/students` | Create student |
| GET | `/api/v1/students/{id}` | Get one |
| PUT | `/api/v1/students/{id}` | Partial update |
| DELETE | `/api/v1/students/{id}` | Soft delete (archive) |
| GET | `/api/v1/surahs` | List all 114 |
| GET | `/api/v1/surahs/{id}` | Get one |
| GET | `/api/v1/students/{id}/progress` | List a student's surah progress |
| POST | `/api/v1/students/{id}/progress` | Upsert (student + surah) progress |
| PUT | `/api/v1/progress/{id}` | Partial update by progress id |
| GET, POST | `/api/v1/students/{id}/evaluations` | List or create evaluation (6-axis scoring) |
| GET, PUT, DELETE | `/api/v1/evaluations/{id}` | Get / update / delete evaluation |
| GET, POST | `/api/v1/students/{id}/observations` | List or create teacher note |
| DELETE | `/api/v1/observations/{id}` | Delete observation |
| GET | `/api/v1/analytics/student/{id}` | Per-student KPIs (mastery %, counts, recent eval avg) |
| GET | `/api/v1/analytics/student/{id}/evaluation-trend` | Time-bucketed eval scores (`?bucket=day\|week\|month`) |
| GET | `/api/v1/analytics/class/{id}` | Class-level aggregates |
| GET | `/api/v1/analytics/school` | School-level aggregates (current user's school) |
| GET | `/api/v1/students/{id}/surahs/{surah_id}/timeline` | Per-surah status history (every change recorded) |
| GET, POST | `/api/v1/classes` | List classes / create (admin only) |
| GET, PUT, DELETE | `/api/v1/classes/{id}` | Read for any school user; write admin only |
| GET | `/api/v1/admin/audit-logs` | Audit trail, admin only, filter by entity_type/entity_id |
| GET | `/api/v1/admin/users` | School user list, admin only |

Full schemas live in Swagger at `/docs`.

## Design principles enforced in MVP-1

- **Multi-tenant by school**: every student/progress query is filtered by the caller's `school_id`.
- **Soft delete**: `DELETE /students/{id}` archives, never destroys.
- **Idempotent progress updates**: `(student_id, surah_id)` is unique; re-posting overwrites the same row.
- **DB-portable models**: the `GUID` type works on Postgres (native UUID) and SQLite (CHAR-36) so tests run without Postgres.
- **Argon2 password hashing + JWT access/refresh tokens**.

## Testing

```bash
cd backend
pytest -q
```

64 tests cover auth, students CRUD, progress upsert + timeline, evaluations, observations, analytics, classes, admin user list, audit logs, and cross-tenant isolation.

## Roadmap

See `docs/ARCHITECTURE.md` §Roadmap.

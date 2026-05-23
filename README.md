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
| MVP-2 | Evaluations, notes, basic analytics | Not started |
| MVP-3 | Audit logs, versioned history, admin UI | Not started |

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
npm install
npm run dev
```

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

17 tests cover auth, students CRUD, and progress upsert paths.

## Roadmap

See `docs/ARCHITECTURE.md` §Roadmap.

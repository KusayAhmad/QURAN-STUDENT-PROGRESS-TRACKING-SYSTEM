FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps for asyncpg / argon2 / cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install -e .

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY seeds ./seeds

EXPOSE 8000

# Apply migrations + seed surahs + start API.
# In production, separate these into init containers/jobs.
CMD ["sh", "-c", "alembic upgrade head && python -m seeds.seed --demo-users && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

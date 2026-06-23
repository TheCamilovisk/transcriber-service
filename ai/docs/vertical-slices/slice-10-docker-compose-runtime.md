# Slice 10 — Docker Compose Local Runtime

> Source: `vertical-slice-implementation-plan.md` Slice 10

## Goal

Make the full system runnable with Docker Compose.

## Scope

This slice adds `Dockerfile`, `docker-compose.yml`, `.dockerignore`, and validates one-line runtime startup after `.env` exists.

## Tasks

Create `Dockerfile`.

Requirements:

- Base image `python:3.13-slim`
- Fallback documented as `python:3.12-slim`
- Install `ffmpeg`
- Copy `uv` from `ghcr.io/astral-sh/uv`
- Set `UV_PROJECT_ENVIRONMENT=/opt/venv`
- Set `PATH=/opt/venv/bin:$PATH`
- Install dependencies with `uv sync --frozen --no-dev`
- Use `/app` as workdir

Expected Dockerfile shape:

```dockerfile
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
```

Create `docker-compose.yml`.

Services:

- `migrate`
- `api`
- `worker`

Use same image/build for all services.

Use:

```yaml
env_file:
  - .env
```

Use volumes:

```yaml
volumes:
  - .:/app
  - ./data:/app/data
```

Commands:

```yaml
migrate:
  command: uv run alembic upgrade head

api:
  command: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

worker:
  command: uv run python -m app.worker.main
```

Dependencies:

```yaml
api:
  depends_on:
    migrate:
      condition: service_completed_successfully

worker:
  depends_on:
    migrate:
      condition: service_completed_successfully
```

Restart policies:

```yaml
migrate:
  restart: "no"

api:
  restart: unless-stopped

worker:
  restart: unless-stopped
```

API health check:

```yaml
healthcheck:
  test:
    [
      "CMD",
      "python",
      "-c",
      "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()",
    ]
  interval: 30s
  timeout: 10s
  retries: 3
```

Create `.dockerignore`:

```dockerignore
.venv
__pycache__
.pytest_cache
.ruff_cache
.mypy_cache
.coverage
htmlcov
data
.env
.git
```

## Tests

Manual test:

```bash
cp .env.example .env
docker compose up --build
```

Then:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{
  "status": "ok",
  "database": "ok",
  "upload_dir": "ok"
}
```

Upload test:

```bash
curl -X POST http://localhost:8000/api/v1/transcriptions \
  -F 'audio=@sample.mp3' \
  -F 'language=pt'
```

## Acceptance Criteria

This slice is complete when:

1. `docker compose up --build` starts `migrate`, `api`, and `worker`.
2. Migrations run before API and worker.
3. API responds to `/health`.
4. API and worker share `./data`.
5. Uploaded files are visible to worker.
6. API has Docker health check.
7. Worker logs show startup/model loading.

# Architecture — Docker, Dockerignore, and Gitignore Architecture

> Source: `architecture-specification.md` §20–22

## 20.1 Docker Image

Use a single Docker image for:

- API
- Worker
- Migration service

Base image:

```dockerfile
FROM python:3.13-slim
```

Fallback if dependency compatibility fails:

```dockerfile
FROM python:3.12-slim
```

## 20.2 System Dependencies

The Docker image installs `ffmpeg`.

Expected Dockerfile section:

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
```

## 20.3 UV Installation

Copy `uv` from the official Astral image:

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
```

## 20.4 Docker Virtual Environment

The Docker virtual environment is outside the project directory:

```text
/opt/venv
```

Expected Dockerfile environment:

```dockerfile
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
```

This prevents the source-code bind mount from hiding installed dependencies.

## 20.5 Dependency Installation

Docker installs runtime dependencies only:

```bash
uv sync --frozen --no-dev
```

The image build requires:

```text
uv.lock
```

## 20.6 Docker Compose Services

Docker Compose defines three services:

- `migrate`
- `api`
- `worker`

### `migrate`

Responsibilities:

- Run Alembic migrations
- Exit successfully

Command:

```bash
uv run alembic upgrade head
```

Restart policy:

```yaml
restart: "no"
```

### `api`

Responsibilities:

- Run FastAPI application
- Expose HTTP port
- Auto-reload during local development

Command:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Restart policy:

```yaml
restart: unless-stopped
```

Depends on:

```text
migrate completed successfully
```

### `worker`

Responsibilities:

- Run worker polling loop
- Load Faster Whisper
- Process jobs

Command:

```bash
uv run python -m app.worker.main
```

Restart policy:

```yaml
restart: unless-stopped
```

Depends on:

```text
migrate completed successfully
```

## 20.7 Docker Volumes

Docker Compose uses bind mounts.

```yaml
volumes:
  - .:/app
  - ./data:/app/data
```

This means:

- Source code is mounted into the API and worker containers
- API reload can detect source changes
- SQLite database persists in `./data/app.db`
- Uploaded audio temporarily lives in `./data/uploads`

## 20.8 Docker Env File

Docker Compose uses:

```yaml
env_file:
  - .env
```

`.env.example` is committed.

`.env` is not committed.

## 20.9 `.env.example`

Docker settings are active by default.

Direct UV settings are included as commented alternatives.

```env
# Docker Compose defaults
DATABASE_URL=sqlite:////app/data/app.db
UPLOAD_DIR=/app/data/uploads

# Direct UV local defaults
# DATABASE_URL=sqlite:///./data/app.db
# UPLOAD_DIR=./data/uploads

MAX_UPLOAD_SIZE_MB=25
WORKER_POLL_INTERVAL_SECONDS=3

FASTER_WHISPER_MODEL_SIZE=small
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8

API_HOST=0.0.0.0
API_PORT=8000
```

## 20.10 API Health Check

Docker Compose defines a health check for the API service.

Prefer Python-based health check to avoid installing curl:

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

No worker health check is required in v1.

Worker health is inspected through logs.

## 21. Docker Ignore Architecture

Use `.dockerignore` to prevent local artifacts from entering the build context.

Recommended `.dockerignore`:

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

The `data/` directory should not be copied into the image because it may contain:

- SQLite database
- Uploaded audio files

## 22. Git Ignore Architecture

The user will generate `.gitignore` using the `ignr` tool.

The generated `.gitignore` should conceptually exclude:

- `.env`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.ruff_cache/`
- `.coverage`
- `htmlcov/`
- `data/`
- `*.pyc`

The specs should not require manual maintenance of a full `.gitignore`.

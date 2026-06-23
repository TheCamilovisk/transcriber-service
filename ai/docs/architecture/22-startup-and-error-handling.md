# Architecture — Local Development, Startup, and Error Handling

> Source: `architecture-specification.md` §28–31

## 28. Local Development Architecture

### 28.1 Docker Compose Path

First-time setup:

```bash
cp .env.example .env
docker compose up --build
```

Regular startup:

```bash
docker compose up --build
```

The Docker Compose path starts:

- Migrations
- API
- Worker

### 28.2 Direct UV Path

Commands:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run python -m app.worker.main
```

### 28.3 Worker Restart During Development

API uses Uvicorn reload in Docker.

Worker does not auto-reload.

When worker code changes:

```bash
docker compose restart worker
```

## 29. API Startup Architecture

When the API starts, it should:

1. Load settings.
2. Configure logging.
3. Validate database connectivity.
4. Create/validate upload directory.
5. Start serving requests.

The API should fail fast if:

- SQLite database cannot be reached
- Upload directory cannot be created
- Upload directory is not writable

The API does not run migrations on startup.

Migrations are handled by Alembic directly or by the Docker Compose `migrate` service.

## 30. Worker Startup Architecture

When the worker starts, it should:

1. Load settings.
2. Configure logging.
3. Validate database connectivity.
4. Create/validate upload directory.
5. Load Faster Whisper model.
6. Reset processing jobs to pending.
7. Enter polling loop.

The worker should fail fast if:

- SQLite database cannot be reached
- Upload directory cannot be created or written to
- Faster Whisper model cannot be loaded

## 31. Error Handling Architecture

### 31.1 API Errors

API errors use FastAPI's default format.

Example:

```json
{
  "detail": "Unsupported audio format. Allowed formats: mp3, wav, m4a, ogg, webm."
}
```

### 31.2 Job Errors

Failed jobs store a clean client-facing `error_message`.

No `error_code` field in v1.

Full exception details are logged by the worker.

The API must not expose stack traces.

### 31.3 Missing Audio File

If a job's audio file is missing, the worker marks the job as failed.

Stored message:

```text
Audio file is no longer available.
```

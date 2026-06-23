# Architecture Specification — Audio Transcription API

## 1. Purpose

This document defines the technical architecture for the **Audio Transcription API**.

The system is an internal REST API for asynchronous audio transcription using **FastAPI**, **SQLite**, **local filesystem storage**, and a single **Faster Whisper** worker process.

This architecture intentionally stays simple. It uses a straightforward layered design, not full hexagonal architecture or heavy domain-driven design.

---

## 2. Architectural Goals

The architecture should optimize for:

- Simplicity
- Clear separation of concerns
- Easy local development
- One-line Docker Compose startup after `.env` exists
- Predictable worker behavior
- Testability without requiring real Faster Whisper in the default test suite
- Future extensibility without overengineering v1

The system should be easy to understand for a developer reading the codebase for the first time.

---

## 3. High-Level System Design

The application has two main runtime processes:

1. **API process**
   - FastAPI application
   - Receives audio uploads
   - Creates transcription jobs
   - Exposes job retrieval/listing endpoints
   - Exposes health check endpoint

2. **Worker process**
   - Loads Faster Whisper model
   - Polls SQLite for pending jobs
   - Processes one job at a time
   - Stores transcription results
   - Deletes uploaded audio files after processing

There is no external queue in v1.

SQLite acts as both:

- The persistence database
- The simple job queue

Local filesystem storage is used for temporary uploaded audio files.

---

## 4. Runtime Architecture

## 4.1 Runtime Components

```text
Client
  ↓
FastAPI API process
  ↓
SQLite database
  ↓
Polling worker process
  ↓
Faster Whisper
  ↓
SQLite database updated with result
```

The API and worker communicate indirectly through the database.

The API does not call the worker directly.

The worker does not call the API.

## 4.2 Process Responsibilities

### API Process

The API process is responsible for:

- Receiving HTTP requests
- Validating uploaded audio files
- Saving uploaded audio to local storage
- Creating transcription job records
- Listing transcription jobs
- Fetching transcription jobs by ID
- Exposing application health

The API process does not perform transcription.

### Worker Process

The worker process is responsible for:

- Loading Faster Whisper at startup
- Resetting stuck processing jobs to pending on startup
- Polling for pending jobs
- Claiming the oldest pending job
- Marking jobs as processing
- Transcribing audio files
- Saving transcription text
- Marking jobs as completed or failed
- Deleting uploaded audio after processing

The worker processes one job at a time.

---

## 5. Layered Architecture

The application uses a simple layered architecture.

```text
API layer
  ↓
Application service layer
  ↓
Repository / storage / transcriber layer
  ↓
SQLite / filesystem / Faster Whisper
```

The worker also uses the application service layer.

```text
Worker entrypoint
  ↓
Application service layer
  ↓
Repository / storage / transcriber layer
  ↓
SQLite / filesystem / Faster Whisper
```

## 5.1 Layer Responsibilities

### API Layer

Responsible for:

- FastAPI routes
- Request parsing
- Response schemas
- HTTP status codes
- Dependency injection

The API layer should not contain business workflow logic.

It should delegate use cases to the application service.

### Application Service Layer

Responsible for:

- Creating jobs
- Validating application-level decisions
- Coordinating file storage and database writes
- Listing jobs
- Fetching jobs
- Claiming jobs
- Processing jobs
- Setting lifecycle timestamps
- Owning database transactions

The service layer owns transaction boundaries.

Repositories do not commit internally.

### Repository Layer

Responsible for:

- SQLAlchemy queries
- Adding job records
- Updating job records
- Listing jobs
- Counting jobs
- Fetching jobs by ID

Repositories receive an active SQLAlchemy session.

Repositories do not create sessions.

Repositories do not commit.

### Storage Layer

Responsible for:

- Creating upload directory
- Validating upload directory writability
- Saving uploaded audio files
- Checking file existence
- Deleting files after processing

The v1 storage implementation is local filesystem only.

### Transcriber Layer

Responsible for:

- Loading Faster Whisper
- Transcribing audio files
- Normalizing transcription text
- Returning text and language result

The v1 transcriber implementation is concrete Faster Whisper integration only.

No generic transcriber interface is required in v1.

---

## 6. Proposed Project Structure

```text
transcription-api/
  app/
    __init__.py

    main.py
    settings.py

    api/
      __init__.py
      dependencies.py
      routes/
        __init__.py
        health.py
        transcriptions.py
      schemas/
        __init__.py
        transcription.py

    application/
      __init__.py
      services/
        __init__.py
        transcription_service.py

    domain/
      __init__.py
      enums.py

    infrastructure/
      __init__.py

      database/
        __init__.py
        base.py
        session.py
        models.py

      repositories/
        __init__.py
        transcription_job_repository.py

      storage/
        __init__.py
        local_audio_storage.py

      transcriber/
        __init__.py
        faster_whisper_transcriber.py

    worker/
      __init__.py
      main.py

    utils/
      __init__.py
      time.py
      logging.py

  alembic/
    versions/

  tests/
    unit/
    api/
    worker/
    integration/

  .github/
    workflows/
      ci.yml

  .env.example
  .dockerignore
  docker-compose.yml
  Dockerfile
  alembic.ini
  pyproject.toml
  uv.lock
  README.md
```

## 6.1 Notes on Structure

The API and worker live in the same repository and share the same codebase.

The API entrypoint is:

```text
app/main.py
```

The worker entrypoint is:

```text
app/worker/main.py
```

The database model is kept under infrastructure because it is a persistence concern.

The only domain-level concept needed in v1 is the job status enum.

---

## 7. API Architecture

## 7.1 API Framework

The API uses **FastAPI**.

OpenAPI metadata:

```text
title: Audio Transcription API
version: 0.1.0
description: Internal REST API for asynchronous audio transcription using Faster Whisper.
```

## 7.2 API Routes

Application endpoints use the `/api/v1` prefix.

Health endpoint remains unversioned.

```http
POST /api/v1/transcriptions
GET /api/v1/transcriptions/{job_id}
GET /api/v1/transcriptions
GET /health
```

## 7.3 Route Modules

Expected route modules:

```text
app/api/routes/transcriptions.py
app/api/routes/health.py
```

`transcriptions.py` contains:

- Create transcription job endpoint
- Get transcription job endpoint
- List transcription jobs endpoint

`health.py` contains:

- Health check endpoint

## 7.4 API Schemas

Schemas live in:

```text
app/api/schemas/transcription.py
```

Expected schemas:

- `TranscriptionJobResponse`
- `TranscriptionJobListItem`
- `TranscriptionJobListResponse`

The API should not return raw SQLAlchemy models directly.

The API uses `snake_case` JSON fields.

## 7.5 Dependency Injection

API dependencies live in:

```text
app/api/dependencies.py
```

Expected dependencies:

- `get_db_session()`
- `get_transcription_service()`

The route layer receives dependencies and delegates use cases to `TranscriptionService`.

---

## 8. Application Service Architecture

## 8.1 Main Service

The application uses a single service class in v1:

```text
TranscriptionService
```

Expected location:

```text
app/application/services/transcription_service.py
```

## 8.2 Service Responsibilities

The service should expose methods similar to:

```python
class TranscriptionService:
    def create_transcription_job(...):
        ...

    def get_transcription_job(...):
        ...

    def list_transcription_jobs(...):
        ...

    def claim_next_pending_job(...):
        ...

    def reset_processing_jobs_to_pending(...):
        ...

    def process_job(...):
        ...
```

## 8.3 Transaction Ownership

The service layer owns database transactions.

Repositories do not call `commit()`.

Routes do not contain transaction logic.

Worker entrypoints do not contain transaction logic beyond opening and closing sessions.

Expected pattern:

```text
Route or worker opens session
  ↓
Service performs use case
  ↓
Repository mutates/query objects
  ↓
Service commits or rolls back
```

## 8.4 File and Database Consistency

For job creation:

1. Generate UUID.
2. Save file.
3. Create database row.
4. Commit transaction.
5. If database creation fails, delete saved file.

This avoids creating a pending job without a corresponding audio file.

For job processing:

1. Mark job processing.
2. Commit.
3. Transcribe.
4. Mark completed or failed.
5. Delete audio file.
6. Commit final state.

The exact implementation may split commits around status transitions to make job state visible to clients.

`process_job()` uses a single session for the whole call, but commits at each phase boundary rather than once at the end: commit immediately after marking `processing`, then commit again after marking the final `completed`/`failed` state. This makes the `processing` transition durably visible to API readers as soon as it happens, without needing to open and close a separate session per phase.

---

## 9. Domain Model

## 9.1 Status Enum

The application uses a Python enum for job statuses.

Expected location:

```text
app/domain/enums.py
```

Expected enum:

```python
from enum import StrEnum


class TranscriptionJobStatus(StrEnum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
```

The database stores the enum value as a string.

## 9.2 No Separate Domain Dataclasses

Version 1 does not define separate domain dataclasses for transcription jobs.

The SQLAlchemy model acts as the internal persisted job representation.

Pydantic schemas control API output.

---

## 10. Database Architecture

## 10.1 Database Engine

Version 1 uses **SQLite**.

Default direct local database URL:

```env
DATABASE_URL=sqlite:///./data/app.db
```

Default Docker database URL:

```env
DATABASE_URL=sqlite:////app/data/app.db
```

The database URL is configurable through environment variables.

## 10.2 SQLAlchemy Style

The application uses SQLAlchemy 2.0 ORM style.

Use:

- `Mapped`
- `mapped_column`
- `select`
- modern `Session` patterns

Do not use SQLModel.

Do not use classic query-style ORM as the default.

## 10.3 Session Management

Database setup lives in:

```text
app/infrastructure/database/session.py
```

Expected responsibilities:

- Create SQLAlchemy engine
- Create sessionmaker
- Expose session dependency/helper

API routes receive database sessions through FastAPI dependency injection.

Worker code creates sessions through the same session factory.

## 10.4 Database Model

The transcription job model lives in:

```text
app/infrastructure/database/models.py
```

Expected table:

```text
transcription_jobs
```

Fields:

- `id`
- `status`
- `original_filename`
- `stored_audio_path`
- `content_type`
- `file_size_bytes`
- `language`
- `text`
- `error_message`
- `created_at`
- `updated_at`
- `started_at`
- `finished_at`

### 10.4.1 Column Types and Lengths

```python
id: Mapped[str] = mapped_column(String(36), primary_key=True)
status: Mapped[str] = mapped_column(String(20), nullable=False)
original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
stored_audio_path: Mapped[str] = mapped_column(String(512), nullable=False)
content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
language: Mapped[str | None] = mapped_column(String(10), nullable=True)
text: Mapped[str | None] = mapped_column(Text, nullable=True)
error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

`file_size_bytes` is always derived from bytes actually written to disk during upload, never from a client-supplied header.

## 10.5 UUID Storage

SQLite stores UUID values as strings.

Database field:

```python
id: Mapped[str] = mapped_column(String(36), primary_key=True)
```

API schemas expose IDs as UUID values.

The service layer converts between `UUID` and `str` where needed.

## 10.6 Indexes

The database should define indexes for the main query patterns.

Required indexes:

- `status`
- `created_at`
- `status + created_at`

These support:

- Worker claiming oldest pending job
- Status-filtered listing
- Newest-first listing

## 10.7 Migrations

The project uses Alembic from the beginning.

Migrations live in:

```text
alembic/
```

The initial migration creates the `transcription_jobs` table and indexes.

Docker Compose runs:

```bash
uv run alembic upgrade head
```

before starting API and worker.

Direct local development also requires:

```bash
uv run alembic upgrade head
```

---

## 11. Repository Architecture

## 11.1 Repository Class

The repository is a concrete class:

```text
TranscriptionJobRepository
```

Expected location:

```text
app/infrastructure/repositories/transcription_job_repository.py
```

No repository interface/protocol is required in v1.

## 11.2 Repository Responsibilities

Expected repository methods:

```python
class TranscriptionJobRepository:
    def add(self, job):
        ...

    def get_by_id(self, job_id: str):
        ...

    def list(self, *, status: str | None, limit: int, offset: int):
        ...

    def count(self, *, status: str | None):
        ...

    def get_oldest_pending(self):
        ...

    def list_processing_jobs(self):
        ...
```

Repository methods should:

- Query SQLAlchemy models
- Update SQLAlchemy model fields
- Return ORM objects

Repository methods should not:

- Commit transactions
- Own session lifecycle
- Perform file operations
- Call Faster Whisper

---

## 12. Storage Architecture

## 12.1 Storage Implementation

The storage implementation is a concrete class:

```text
LocalAudioStorage
```

Expected location:

```text
app/infrastructure/storage/local_audio_storage.py
```

No generic storage abstraction is required in v1.

## 12.2 Storage Responsibilities

Expected methods:

```python
class LocalAudioStorage:
    def ensure_upload_dir_exists(self) -> None:
        ...

    def validate_writable(self) -> None:
        ...

    def save_upload(...):
        ...

    def exists(self, path: str) -> bool:
        ...

    def delete(self, path: str) -> None:
        ...
```

## 12.3 File Naming

The saved file uses:

```text
{job_id}.{extension}
```

Example:

```text
/app/data/uploads/8f4b2d6e-91b5-4d3a-a36f-78f2f3c1c9a1.mp3
```

The original filename is stored only as metadata.

### 12.3.1 Extension Extraction Rule

The extension is the last suffix of the original filename, extracted case-insensitively (e.g. via `Path(filename).suffix.lower().lstrip('.')`) and compared against the allowed list in lowercase:

- A filename with no extension (`meeting`) is treated as an unsupported format.
- A filename with multiple suffixes (`meeting.mp3.exe`) uses only the last one (`exe`) for validation.
- The stored filename always uses the lowercased extension, regardless of the case the client sent (`AUDIO.MP3` → stored as `{job_id}.mp3`).

## 12.4 Storage Path Configuration

Default Docker path:

```env
UPLOAD_DIR=/app/data/uploads
```

Default local direct path:

```env
UPLOAD_DIR=./data/uploads
```

Both API and worker must use the same configured upload directory.

## 12.5 Cleanup

The worker deletes uploaded audio after both success and failure.

The storage class should make deletion safe:

- Deleting a missing file should not crash final failure handling
- Deletion errors should be logged

---

## 13. Transcriber Architecture

## 13.1 Transcriber Implementation

The transcriber is a concrete class:

```text
FasterWhisperTranscriber
```

Expected location:

```text
app/infrastructure/transcriber/faster_whisper_transcriber.py
```

No generic transcriber interface is required in v1.

## 13.2 Model Lifecycle

The worker creates one `FasterWhisperTranscriber` instance at startup.

The Faster Whisper model loads during transcriber initialization.

If loading fails:

- Worker exits with an error
- Worker does not start polling
- Jobs are not marked failed

## 13.3 Transcriber Method Shape

Expected shape:

```python
from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    text: str
    language: str | None


class FasterWhisperTranscriber:
    def __init__(
        self,
        model_size: str,
        device: str,
        compute_type: str,
    ) -> None:
        ...

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
    ) -> TranscriptionResult:
        ...
```

## 13.4 Text Normalization

The transcriber should:

- Collect segment texts
- Join them
- Strip leading/trailing whitespace
- Collapse repeated whitespace

The service stores only the normalized plain text.

## 13.5 Language Behavior

If the job already has `language`, the service passes it to the transcriber and keeps it.

If the job language is `null`, the transcriber result language is stored back into the job.

---

## 14. Worker Architecture

## 14.1 Worker Entrypoint

Worker entrypoint:

```text
app/worker/main.py
```

Run directly:

```bash
uv run python -m app.worker.main
```

Docker Compose command:

```bash
uv run python -m app.worker.main
```

## 14.2 Worker Lifecycle

Worker startup sequence:

1. Load settings.
2. Configure logging.
3. Create/validate upload directory.
4. Validate database connectivity.
5. Load Faster Whisper model.
6. Reset processing jobs to pending.
7. Enter polling loop.

## 14.3 Polling Loop

Conceptual loop:

```python
while not shutdown_requested:
    job = service.claim_next_pending_job()

    if job is None:
        sleep(settings.worker_poll_interval_seconds)
        continue

    service.process_job(job.id)
```

## 14.4 Single-Worker Assumption

The worker design assumes:

- One worker process
- One job at a time

Because of this, SQLite polling remains simple.

If future versions need multiple workers, the architecture should be revisited and probably move to:

- Redis + RQ/Dramatiq
- Or PostgreSQL with safer row locking

## 14.5 Startup Recovery

On startup, the worker calls:

```text
reset_processing_jobs_to_pending()
```

This resets jobs stuck in `processing` after a crash.

## 14.6 Graceful Shutdown

The worker handles shutdown signals using best effort:

- If idle, stop
- If processing, try to finish current job
- If force-killed, startup recovery handles stuck processing jobs

Mechanism: register handlers for `SIGTERM` and `SIGINT` that set a `shutdown_requested` flag. The polling loop checks this flag between poll iterations and before claiming the next job. There is no timeout applied to an in-flight job — the current `process_job()` call is allowed to run to completion. `SIGKILL` bypasses the handler entirely; the next worker startup's recovery step (§14.5) resets any job left stuck in `processing`.

---

## 15. Settings Architecture

## 15.1 Settings Library

The application uses **Pydantic Settings**.

Expected location:

```text
app/settings.py
```

## 15.2 Settings Naming

Environment variables use uppercase names.

Pydantic fields use lowercase names.

Example:

```env
DATABASE_URL=sqlite:///./data/app.db
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE_MB=25
```

```python
database_url: str = 'sqlite:///./data/app.db'
upload_dir: str = './data/uploads'
max_upload_size_mb: int = 25
```

## 15.3 Cached Settings

Use a central cached settings function:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = 'sqlite:///./data/app.db'
    upload_dir: str = './data/uploads'
    max_upload_size_mb: int = 25


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Tests may clear the cache when overriding environment variables.

## 15.4 Expected Settings

```python
class Settings(BaseSettings):
    database_url: str = 'sqlite:///./data/app.db'
    upload_dir: str = './data/uploads'
    max_upload_size_mb: int = 25
    worker_poll_interval_seconds: int = 3

    faster_whisper_model_size: str = 'small'
    faster_whisper_device: str = 'cpu'
    faster_whisper_compute_type: str = 'int8'

    api_host: str = '0.0.0.0'
    api_port: int = 8000
```

---

## 16. Time Architecture

## 16.1 UTC Helper

Use UTC-aware datetimes.

Expected helper:

```text
app/utils/time.py
```

```python
from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)
```

Use this helper consistently for:

- `created_at`
- `updated_at`
- `started_at`
- `finished_at`

## 16.2 Serialization

API responses may rely on Pydantic’s default datetime serialization.

The exact output may be:

```text
2026-06-23T14:30:00Z
```

or:

```text
2026-06-23T14:30:00+00:00
```

Both are acceptable if they represent UTC.

---

## 17. Validation Architecture

## 17.1 Upload Validation

Upload validation should live primarily in the service layer or a small helper used by the service.

The API route should remain thin.

Validation rules:

- Required `audio` field
- Allowed extensions: `mp3`, `wav`, `m4a`, `ogg`, `webm`
- Max size: 25 MB
- Empty file rejected
- Optional language format

## 17.2 Language Validation

Language validation pattern:

```regex
^[a-z]{2,5}$
```

Invalid language values should be rejected before creating a job.

## 17.4 Pagination and Filter Validation

`limit`, `offset`, and `status` on the list endpoint are validated declaratively via FastAPI query parameter types, not custom service-layer code:

```python
limit: int = Query(default=20, ge=1, le=100)
offset: int = Query(default=0, ge=0)
status: TranscriptionJobStatus | None = Query(default=None)
```

Out-of-range values or an invalid `status` value produce FastAPI's standard `422` response automatically, the same mechanism already used for invalid UUID path parameters.

## 17.3 Error Responses

FastAPI’s default error response format is used.

Known application errors may raise `HTTPException` from the API layer after the service reports an error, or the service may raise application exceptions mapped by the route.

For v1, avoid a complex custom exception hierarchy.

---

## 18. Logging Architecture

## 18.1 Logging Style

Use basic Python logging.

No structured JSON logging in v1.

Logs should be readable as plain text.

## 18.2 Log Locations

Logging helpers may live in:

```text
app/utils/logging.py
```

or be configured directly in entrypoints for v1.

## 18.3 Required Job Context

Any log related to a transcription job should include:

```text
job_id=...
```

Worker logs should cover:

- Startup
- Model loading
- Polling
- Job claiming
- Transcription start
- Transcription completion
- Transcription failure
- File deletion
- Shutdown

---

## 19. Health Check Architecture

The health check route lives in:

```text
app/api/routes/health.py
```

It checks:

- API process is responding
- SQLite database can execute a simple query
- Upload directory exists and is writable

Expected implementation checks:

Database:

```sql
SELECT 1
```

Upload directory:

- Ensure directory exists
- Check write access

Successful response:

```json
{
  "status": "ok",
  "database": "ok",
  "upload_dir": "ok"
}
```

Failure response:

```http
503 Service Unavailable
```

The failure body is structured, not a generic `detail` message, so the client can see which dependency failed:

```json
{
  "status": "error",
  "database": "error",
  "upload_dir": "ok"
}
```

Top-level `status` is `error` if any individual check fails. This means the route builds the response body manually (e.g. via `JSONResponse`) rather than raising a plain `HTTPException`, since the failure shape must carry the same `database`/`upload_dir` keys as the success shape.

---

## 20. Docker Architecture

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

---

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

---

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

---

## 23. Dependency Architecture

## 23.1 Package Manager

Use **UV**.

## 23.2 Dependency Groups

Use:

- Runtime dependencies
- Dev dependencies

Runtime dependencies:

- `fastapi`
- `uvicorn`
- `sqlalchemy`
- `alembic`
- `pydantic-settings`
- `python-multipart`
- `faster-whisper`

Dev dependencies:

- `pytest`
- `pytest-asyncio`
- `httpx`
- `ruff`
- `pytest-cov`

No mypy or pyright required in v1.

---

## 24. Code Quality Architecture

## 24.1 Ruff

Use Ruff for linting and formatting.

Commands:

```bash
uv run ruff check .
uv run ruff format .
```

The Ruff formatter should prefer single quotes where possible.

Python code should use:

```python
status = 'pending'
message = 'Unsupported audio format.'
```

instead of:

```python
status = "pending"
message = "Unsupported audio format."
```

## 24.2 Type Hints

Use type hints throughout the codebase.

Do not enforce mypy or pyright in v1.

## 24.3 No Makefile

No Makefile, Taskfile, or Justfile in v1.

The README documents direct commands.

---

## 25. Testing Architecture

## 25.1 Test Framework

Use pytest.

Default test command:

```bash
uv run pytest
```

Coverage command:

```bash
uv run pytest --cov=app
```

No coverage gate in v1.

## 25.2 Test Categories

Tests are organized into:

```text
tests/unit/
tests/api/
tests/worker/
tests/integration/
```

## 25.3 Fake Transcriber

Default tests must not require Faster Whisper.

Use a fake transcriber in unit/API/worker tests.

Expected fake behavior:

```python
class FakeTranscriber:
    def transcribe(self, audio_path: str, language: str | None = None):
        return TranscriptionResult(
            text='Fake transcription.',
            language=language or 'en',
        )
```

Failure tests can use a fake transcriber that raises an exception.

## 25.4 Test Database

Use:

- In-memory SQLite for simple unit/API tests
- Temporary file-backed SQLite for worker/integration-style tests

Tests must not use the real development database.

## 25.5 Test Upload Storage

Use temporary directories per test.

For pytest, use:

```text
tmp_path
```

Tests must not use the real development upload directory.

## 25.6 API Tests

Use FastAPI test client or HTTPX.

Expected API test coverage:

- Create job success
- Unsupported extension
- Empty file
- Oversized file
- Invalid language
- Get job success
- Get job not found
- List jobs with pagination
- List jobs with status filter
- Health check success

## 25.7 Worker Tests

Worker tests should verify:

- Pending job is claimed
- Oldest pending job is selected
- Processing job is reset to pending on startup
- Successful transcription marks completed
- Failed transcription marks failed
- Missing audio file marks failed
- Audio file is deleted after success
- Audio file is deleted after failure

## 25.8 Optional Integration Test

A real Faster Whisper test may exist but must be marked as integration.

Run explicitly:

```bash
uv run pytest -m integration
```

It should not run in the default test command.

---

## 26. CI Architecture

Use GitHub Actions.

Workflow location:

```text
.github/workflows/ci.yml
```

Triggers:

```yaml
on:
  push:
    branches:
      - main
      - dev
  pull_request:
    branches:
      - main
      - dev
```

Required CI commands:

```bash
uv run ruff check .
uv run pytest
```

Optional coverage command:

```bash
uv run pytest --cov=app
```

No minimum coverage gate in v1.

---

## 27. Branching Architecture

The project uses a basic `main` / `dev` workflow.

```text
dev
- active development branch

main
- stable branch
```

CI runs on push and pull request events for both branches.

---

## 28. Local Development Architecture

## 28.1 Docker Compose Path

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

## 28.2 Direct UV Path

Commands:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run python -m app.worker.main
```

## 28.3 Worker Restart During Development

API uses Uvicorn reload in Docker.

Worker does not auto-reload.

When worker code changes:

```bash
docker compose restart worker
```

---

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

---

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

---

## 31. Error Handling Architecture

## 31.1 API Errors

API errors use FastAPI’s default format.

Example:

```json
{
  "detail": "Unsupported audio format. Allowed formats: mp3, wav, m4a, ogg, webm."
}
```

## 31.2 Job Errors

Failed jobs store a clean client-facing `error_message`.

No `error_code` field in v1.

Full exception details are logged by the worker.

The API must not expose stack traces.

## 31.3 Missing Audio File

If a job’s audio file is missing, the worker marks the job as failed.

Stored message:

```text
Audio file is no longer available.
```

---

## 32. Security Architecture

Version 1 has no authentication because it is internal-only.

Security assumptions:

- Service runs only in trusted private environments
- Service is not exposed publicly
- Clients are trusted backend services or local scripts

The architecture must not imply this API is safe for public exposure.

Before public exposure, the system would need:

- Authentication
- Authorization
- Request limits
- Stricter upload validation
- Possibly API keys
- Deployment hardening

---

## 33. Out-of-Scope Architecture

The v1 architecture intentionally excludes:

- Redis
- Celery
- RQ
- Dramatiq
- PostgreSQL
- S3/object storage
- Multiple workers
- Worker concurrency
- Webhooks
- Authentication
- User accounts
- Metrics endpoint
- Prometheus
- OpenTelemetry
- Worker heartbeat
- Worker HTTP server
- Full hexagonal architecture
- Generic repository interfaces
- Generic storage interfaces
- Generic transcriber interfaces

These can be introduced later if the project grows.

---

## 34. Architectural Risks and Constraints

## 34.1 SQLite as Queue

SQLite polling is simple and appropriate for v1, but it has limits.

This architecture is suitable for:

- Internal usage
- Low to moderate job volume
- One worker process
- One job at a time

It is not suitable for:

- Many workers
- High throughput
- Distributed processing
- Strong queue guarantees

If those needs appear, migrate to Redis-backed queue or PostgreSQL with locking.

## 34.2 Local Filesystem Storage

Local filesystem storage is simple but requires API and worker to share the same filesystem.

This is handled in Docker Compose with:

```yaml
- ./data:/app/data
```

If API and worker run on different machines later, object storage will be needed.

## 34.3 Faster Whisper Startup Cost

The worker loads Faster Whisper at startup.

This may make worker startup slower.

The benefit is that individual jobs avoid repeated model loading cost.

## 34.4 Python 3.13 Compatibility

The Docker image uses Python 3.13.

If Faster Whisper or related dependencies fail under Python 3.13, the fallback is Python 3.12 slim.

---

## 35. Acceptance Criteria for Architecture

The architecture is acceptable when:

1. API and worker are separate runtime processes.
2. API and worker share the same application service, repository, settings, database, and storage code.
3. The API route layer remains thin.
4. The service layer owns application workflows and database transactions.
5. The repository layer isolates SQLAlchemy access.
6. The storage class isolates filesystem operations.
7. The transcriber class isolates Faster Whisper integration.
8. SQLite is used for persistence and pending job discovery.
9. The worker polls SQLite and processes one job at a time.
10. Docker Compose can start migration, API, and worker services.
11. API and worker share the same `./data` bind mount.
12. Alembic migrations run before API and worker start in Docker Compose.
13. Tests can run without a real Faster Whisper model.
14. CI runs Ruff and pytest on `main`/`dev` push and pull requests.
15. The design remains simple and avoids unnecessary v1 abstractions.

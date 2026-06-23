# Vertical Slices Implementation Plan — Audio Transcription API

## 1. Purpose

This document defines the implementation plan for the **Audio Transcription API** using vertical slices.

A vertical slice is a small end-to-end increment that cuts through the necessary layers of the system:

```text
API / worker entrypoint
→ application service
→ repository / storage / transcriber
→ database / filesystem
→ tests / documentation
```

The goal is to avoid building isolated layers that cannot run. Each slice should produce a working, testable improvement.

---

## 2. Implementation Principles

The implementation should follow these principles:

- Build in small vertical increments.
- Keep the system runnable after each slice.
- Add tests with each slice.
- Avoid implementing unused abstractions.
- Prefer simple concrete classes.
- Keep API routes thin.
- Keep transaction ownership in the service layer.
- Use single quotes in Python code by default.
- Use Ruff for formatting and linting.
- Use pytest for tests.

---

## 3. Target Stack

The project uses:

- Python 3.13
- UV
- FastAPI
- SQLite
- SQLAlchemy 2.0
- Alembic
- Pydantic Settings
- Faster Whisper
- Local filesystem storage
- Docker Compose
- Pytest
- Ruff
- GitHub Actions

Fallback if Python 3.13 causes Faster Whisper dependency issues:

- Python 3.12

---

## 4. Slice Overview

Recommended implementation order:

1. Project skeleton and development tooling
2. Settings, database foundation, and migrations
3. Job model, repository, and basic service
4. Create transcription job endpoint
5. Fetch and list transcription jobs
6. Health check
7. Worker polling loop without real transcription
8. Job processing with fake transcriber
9. Faster Whisper integration
10. Docker Compose local runtime
11. Testing hardening and coverage reporting
12. CI workflow
13. README and usage documentation
14. Final cleanup and acceptance pass

Each slice includes:

- Goal
- Scope
- Tasks
- Tests
- Acceptance criteria

---

# Slice 1 — Project Skeleton and Development Tooling

## Goal

Create the initial project structure and make the repository installable and testable with UV.

## Scope

This slice does not implement the API behavior yet. It establishes the base project, dependency management, formatting, linting, and test framework.

## Tasks

Create the project structure:

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
      schemas/
        __init__.py

    application/
      __init__.py
      services/
        __init__.py

    domain/
      __init__.py
      enums.py

    infrastructure/
      __init__.py
      database/
        __init__.py
      repositories/
        __init__.py
      storage/
        __init__.py
      transcriber/
        __init__.py

    worker/
      __init__.py
      main.py

    utils/
      __init__.py

  tests/
    unit/
    api/
    worker/
    integration/
```

Initialize UV project:

```bash
uv init
```

Add runtime dependencies:

- `fastapi`
- `uvicorn`
- `sqlalchemy`
- `alembic`
- `pydantic-settings`
- `python-multipart`
- `faster-whisper`

Add dev dependencies:

- `pytest`
- `pytest-asyncio`
- `httpx`
- `ruff`
- `pytest-cov`

Configure Ruff in `pyproject.toml`.

Ruff should format strings with single quotes where possible.

Add a minimal FastAPI app in `app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(
    title='Audio Transcription API',
    version='0.1.0',
    description='Internal REST API for asynchronous audio transcription using Faster Whisper.',
)
```

Add an initial smoke test that imports the app.

## Tests

Add:

```text
tests/api/test_app.py
```

Expected tests:

- App can be imported.
- FastAPI app metadata exists.

Run:

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

## Acceptance Criteria

This slice is complete when:

1. The project installs with UV.
2. The app package imports successfully.
3. pytest runs successfully.
4. Ruff check passes.
5. Ruff format runs successfully.
6. Python code uses single quotes by default.

---

# Slice 2 — Settings, Database Foundation, and Migrations

## Goal

Add configuration, SQLAlchemy database setup, and Alembic migrations.

## Scope

This slice prepares persistence but does not yet implement transcription jobs.

## Tasks

Implement `app/settings.py`.

Expected settings:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(env_file='.env')


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Implement database base:

```text
app/infrastructure/database/base.py
```

Implement database session setup:

```text
app/infrastructure/database/session.py
```

Responsibilities:

- Create engine from `settings.database_url`.
- Create `SessionLocal`.
- Expose session dependency/helper.

Add Alembic:

```bash
uv run alembic init alembic
```

Configure Alembic to use the application metadata.

Add `.env.example`.

Active Docker defaults:

```env
DATABASE_URL=sqlite:////app/data/app.db
UPLOAD_DIR=/app/data/uploads

MAX_UPLOAD_SIZE_MB=25
WORKER_POLL_INTERVAL_SECONDS=3

FASTER_WHISPER_MODEL_SIZE=small
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8

API_HOST=0.0.0.0
API_PORT=8000
```

Commented direct UV alternatives:

```env
# DATABASE_URL=sqlite:///./data/app.db
# UPLOAD_DIR=./data/uploads
```

Add `app/utils/time.py`:

```python
from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)
```

## Tests

Add tests for settings:

```text
tests/unit/test_settings.py
```

Test:

- Default `database_url` is `sqlite:///./data/app.db`.
- Default `upload_dir` is `./data/uploads`.
- Environment variables override defaults.

Add tests for UTC helper:

```text
tests/unit/test_time.py
```

Test:

- `utc_now()` returns timezone-aware UTC datetime.

## Acceptance Criteria

This slice is complete when:

1. Settings load from defaults and environment variables.
2. SQLAlchemy session setup exists.
3. Alembic is initialized.
4. `utc_now()` helper exists.
5. Tests pass.
6. Ruff passes.

---

# Slice 3 — Job Model, Repository, and Basic Service

## Goal

Create the transcription job persistence model and the basic repository/service foundation.

## Scope

This slice introduces the job table and core data operations without HTTP endpoints.

## Tasks

Create status enum:

```text
app/domain/enums.py
```

```python
from enum import StrEnum


class TranscriptionJobStatus(StrEnum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
```

Create SQLAlchemy model:

```text
app/infrastructure/database/models.py
```

Table:

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

Use UUID strings:

```python
id: Mapped[str] = mapped_column(String(36), primary_key=True)
```

Column types (see architecture spec §10.4.1 for the full list):

- `status`: `String(20)`
- `original_filename`: `String(255)`
- `stored_audio_path`: `String(512)`
- `content_type`: `String(255)`, nullable
- `file_size_bytes`: `Integer`, not nullable
- `language`: `String(10)`, nullable
- `text`: `Text`, nullable
- `error_message`: `String(500)`, nullable
- all timestamps: `DateTime(timezone=True)`

Add indexes:

- `status`
- `created_at`
- `status + created_at`

Create initial Alembic migration.

Create repository:

```text
app/infrastructure/repositories/transcription_job_repository.py
```

Methods:

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

Create service skeleton:

```text
app/application/services/transcription_service.py
```

Initial methods:

```python
class TranscriptionService:
    def get_transcription_job(self, job_id):
        ...

    def list_transcription_jobs(self, *, status, limit, offset):
        ...
```

## Tests

Use temporary SQLite database.

Add repository tests:

```text
tests/unit/test_transcription_job_repository.py
```

Test:

- Add job.
- Get job by ID.
- List newest first.
- Filter by status.
- Count with and without status.
- Get oldest pending job.

Add service tests:

```text
tests/unit/test_transcription_service_basic.py
```

Test:

- Get existing job.
- Handle missing job consistently.
- List jobs with pagination.

## Acceptance Criteria

This slice is complete when:

1. The `transcription_jobs` table exists through Alembic migration.
2. Repository can create, fetch, list, count, and find pending jobs.
3. Service can fetch and list jobs.
4. Tests pass against temporary SQLite.
5. Ruff passes.

---

# Slice 4 — Create Transcription Job Endpoint

## Goal

Implement:

```http
POST /api/v1/transcriptions
```

## Scope

This slice creates jobs from uploaded audio files and stores files locally. It does not yet process jobs.

## Tasks

Create storage class:

```text
app/infrastructure/storage/local_audio_storage.py
```

Methods:

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

Implement upload validation:

- Allowed extensions: `mp3`, `wav`, `m4a`, `ogg`, `webm`
- Max size: 25 MB
- Reject empty file
- Optional language pattern: `^[a-z]{2,5}$`

Create Pydantic response schemas:

```text
app/api/schemas/transcription.py
```

Schemas:

- `TranscriptionJobResponse`
- `TranscriptionJobListItem`
- `TranscriptionJobListResponse`

Implement service method:

```python
def create_transcription_job(
    self,
    *,
    audio_file,
    language: str | None,
) -> TranscriptionJob:
    ...
```

Behavior:

1. Validate extension.
2. Validate size.
3. Validate empty file.
4. Validate language.
5. Generate UUID.
6. Save upload as `{job_id}.{extension}`.
7. Create DB job with status `pending`.
8. Commit.
9. If DB creation fails, delete saved file.

Create route:

```text
app/api/routes/transcriptions.py
```

Endpoint:

```http
POST /api/v1/transcriptions
```

Register router in `app/main.py`.

## Tests

Add API tests:

```text
tests/api/test_create_transcription_job.py
```

Test:

- Upload valid `mp3` creates pending job.
- Response includes full job representation.
- `original_filename` is stored.
- `content_type` is stored if provided.
- `text` is `null`.
- `error_message` is `null`.
- `started_at` is `null`.
- `finished_at` is `null`.
- File is saved with UUID filename.

Validation tests:

- Unsupported extension returns 400.
- Empty file returns 400.
- Oversized file returns 413.
- Invalid language returns validation error.

Use temporary upload directory.

## Acceptance Criteria

This slice is complete when:

1. `POST /api/v1/transcriptions` works.
2. Uploaded files are saved locally.
3. Pending job records are created.
4. Upload validation works.
5. API tests pass.
6. Ruff passes.

---

# Slice 5 — Fetch and List Transcription Jobs

## Goal

Implement job retrieval and listing endpoints.

## Scope

This slice completes the read side of the API.

## Tasks

Implement route:

```http
GET /api/v1/transcriptions/{job_id}
```

Behavior:

- Validate UUID using path parameter type.
- Return full job representation.
- Return 404 if not found.

Implement route:

```http
GET /api/v1/transcriptions
```

Query parameters:

- `limit`, default `20`, max `100`, min `1` (declared via `Query(ge=1, le=100)`)
- `offset`, default `0`, min `0` (declared via `Query(ge=0)`)
- `status`, optional, typed as `TranscriptionJobStatus` enum so an invalid value is a `422`

Behavior:

- Newest first.
- Optional status filter.
- Return summary items without `text`.
- Include `total`.

Ensure list item schema excludes `text`.

## Tests

Add API tests:

```text
tests/api/test_get_transcription_job.py
tests/api/test_list_transcription_jobs.py
```

Test `GET /api/v1/transcriptions/{job_id}`:

- Existing job returns full job.
- Missing job returns 404.
- Invalid UUID returns 422.

Test `GET /api/v1/transcriptions`:

- Returns `items`, `limit`, `offset`, `total`.
- Default limit is 20.
- Max limit is 100.
- Rejects limit above 100.
- Rejects limit below 1.
- Rejects negative offset.
- Rejects invalid status filter value with 422.
- Supports status filter.
- Orders newest first.
- Does not include `text` in list items.

## Acceptance Criteria

This slice is complete when:

1. Single job retrieval works.
2. Job listing works.
3. Pagination works.
4. Status filtering works.
5. List response excludes `text`.
6. Tests pass.
7. Ruff passes.

---

# Slice 6 — Health Check

## Goal

Implement:

```http
GET /health
```

## Scope

This slice adds operational visibility for API, SQLite, and upload directory readiness.

## Tasks

Create route:

```text
app/api/routes/health.py
```

Endpoint:

```http
GET /health
```

Checks:

- Database can execute `SELECT 1`.
- Upload directory exists or can be created.
- Upload directory is writable.

Successful response:

```json
{
  "status": "ok",
  "database": "ok",
  "upload_dir": "ok"
}
```

Failure (503), with a structured body showing which check failed rather than a generic `detail` message:

```json
{
  "status": "error",
  "database": "error",
  "upload_dir": "ok"
}
```

Build this response manually (e.g. `JSONResponse`) instead of raising a plain `HTTPException`, since the failure body must carry the same `database`/`upload_dir` keys as the success body.

Register health router in `app/main.py`.

Add API startup validation:

- Validate database connectivity.
- Ensure upload directory exists.
- Validate upload directory writability.

## Tests

Add:

```text
tests/api/test_health.py
```

Test:

- Health returns `ok` when DB and upload dir are valid.
- Health returns 503 with structured per-check body when upload dir is not writable, if practical to test.

Add startup validation tests if feasible.

## Acceptance Criteria

This slice is complete when:

1. `GET /health` works.
2. Health checks database.
3. Health checks upload directory.
4. API startup validates required resources.
5. Tests pass.
6. Ruff passes.

---

# Slice 7 — Worker Polling Loop Without Real Transcription

## Goal

Create the worker process and polling loop without running Faster Whisper yet.

## Scope

This slice makes the worker executable and able to claim jobs.

It does not process jobs fully yet.

## Tasks

Implement worker entrypoint:

```text
app/worker/main.py
```

Startup sequence:

1. Load settings.
2. Configure logging.
3. Validate database connectivity.
4. Ensure upload directory exists/writable.
5. Reset processing jobs to pending.
6. Enter polling loop.

At this slice, use a placeholder processing behavior or stop after claiming in tests.

Implement service methods:

```python
def claim_next_pending_job(self):
    ...

def reset_processing_jobs_to_pending(self):
    ...
```

Claim behavior:

- Select oldest pending job.
- Mark `processing`.
- Set `started_at`.
- Set `updated_at`.
- Commit.

Reset behavior:

- Find `processing` jobs.
- Set status to `pending`.
- Clear `started_at`.
- Set `updated_at`.

Implement graceful shutdown: register `SIGTERM`/`SIGINT` handlers that set a `shutdown_requested` flag, checked between poll iterations and before claiming the next job. No timeout is applied to an in-flight job. `SIGKILL` bypasses this; startup recovery (already implemented above) handles any job left stuck in `processing`.

Add worker logging.

## Tests

Add:

```text
tests/worker/test_worker_claiming.py
```

Test:

- Worker claims oldest pending job.
- Claimed job becomes `processing`.
- `started_at` is set.
- `updated_at` is set.
- `processing` jobs reset to `pending` on startup.
- Reset jobs have `started_at` cleared.

Avoid infinite loops in tests by testing service methods, not the full endless worker loop.

## Acceptance Criteria

This slice is complete when:

1. Worker entrypoint exists.
2. Worker can be started.
3. Worker startup recovery exists.
4. Pending job claiming works.
5. Tests pass.
6. Ruff passes.

---

# Slice 8 — Job Processing with Fake Transcriber

## Goal

Implement the full job processing flow using a fake transcriber.

## Scope

This slice completes worker behavior without Faster Whisper.

The worker can process jobs end-to-end with a fake transcriber in tests.

## Tasks

Create transcriber result dataclass:

```text
app/infrastructure/transcriber/faster_whisper_transcriber.py
```

or a shared local module if preferred.

```python
from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    text: str
    language: str | None
```

Create test fake transcribers:

```text
tests/fakes.py
```

Example:

```python
class FakeTranscriber:
    def transcribe(self, audio_path: str, language: str | None = None):
        return TranscriptionResult(
            text='Fake transcription.',
            language=language or 'en',
        )
```

Implement service method:

```python
def process_job(self, job_id: str, transcriber) -> None:
    ...
```

Behavior:

1. Fetch job.
2. Check stored audio path exists.
3. If missing, mark failed.
4. Call `transcriber.transcribe(path, language=job.language)`.
5. Store text.
6. If `job.language` was null, store transcriber result language.
7. Mark completed.
8. Set `finished_at`.
9. Set `updated_at`.
10. Delete uploaded audio file.

Failure behavior:

1. Log full exception.
2. Store clean `error_message`.
3. Mark failed.
4. Set `finished_at`.
5. Set `updated_at`.
6. Delete uploaded audio if it exists.

Clean transcription error message:

```text
Could not transcribe the audio file.
```

Missing audio error message:

```text
Audio file is no longer available.
```

Empty transcription text:

- Mark completed.
- Store `text = ''`.

## Tests

Add:

```text
tests/worker/test_process_job.py
```

Test success:

- Processing job becomes completed.
- Text is stored.
- Language remains provided language if originally set.
- Language is stored from result if originally null.
- `finished_at` is set.
- Audio file is deleted.

Test failure:

- Transcriber exception marks failed.
- Clean `error_message` is stored.
- `text` remains null.
- `finished_at` is set.
- Audio file is deleted.

Test missing audio:

- Missing file marks failed.
- `error_message` is `Audio file is no longer available.`
- No infinite retry.

Test empty result:

- Empty text marks completed.
- `text` is `''`.

## Acceptance Criteria

This slice is complete when:

1. `process_job` works with fake transcriber.
2. Successful jobs become `completed`.
3. Failed jobs become `failed`.
4. Missing audio is handled.
5. Audio cleanup happens after success and failure.
6. Tests pass.
7. Ruff passes.

---

# Slice 9 — Faster Whisper Integration

## Goal

Implement the real `FasterWhisperTranscriber`.

## Scope

This slice connects the worker to Faster Whisper, but default tests still use fake transcribers.

## Tasks

Implement:

```text
app/infrastructure/transcriber/faster_whisper_transcriber.py
```

Class:

```python
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

Behavior:

- Load model at initialization.
- Call `model.transcribe(audio_path, language=language)`.
- Collect `segment.text` values.
- Normalize whitespace.
- Return text and language.

Text normalization:

- Join segment texts.
- Strip.
- Collapse repeated whitespace.

Update worker startup:

- Create `FasterWhisperTranscriber` using settings.
- Exit if model loading fails.
- Pass transcriber to processing loop.

Add optional manual integration test marker:

```python
@pytest.mark.integration
```

Configure pytest markers in `pyproject.toml`.

Optional integration test should require a tiny audio fixture.

Do not run integration test by default.

## Tests

Default tests:

- Unit test text normalization with fake segment values.
- Verify worker can receive transcriber dependency.

Optional integration test:

```bash
uv run pytest -m integration
```

Test:

- Tiny audio file can be transcribed by real Faster Whisper.

## Acceptance Criteria

This slice is complete when:

1. `FasterWhisperTranscriber` loads model from configured settings.
2. Worker uses `FasterWhisperTranscriber` in real runtime.
3. Default tests do not require model download.
4. Optional integration marker exists.
5. Tests pass.
6. Ruff passes.

---

# Slice 10 — Docker Compose Local Runtime

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

---

# Slice 11 — Testing Hardening and Coverage Reporting

## Goal

Improve the default test suite and add coverage reporting.

## Scope

This slice ensures the implementation is well-covered without enforcing a coverage gate.

## Tasks

Add or review tests for all functional requirements.

Test categories:

```text
tests/unit/
tests/api/
tests/worker/
tests/integration/
```

Ensure tests use:

- Temporary SQLite databases
- Temporary upload directories
- Fake transcriber by default

Add `pytest-cov`.

Add command documentation:

```bash
uv run pytest
uv run pytest --cov=app
```

Ensure integration tests are excluded by default.

Configure marker:

```toml
[tool.pytest.ini_options]
markers = [
    'integration: tests that require external runtime dependencies or real Faster Whisper',
]
```

Depending on desired behavior, default test command can ignore integration tests:

```toml
addopts = '-m "not integration"'
```

## Tests

Run:

```bash
uv run pytest
uv run pytest --cov=app
```

## Acceptance Criteria

This slice is complete when:

1. Default pytest run excludes real Faster Whisper integration.
2. Coverage report can be generated.
3. Tests do not use real `data/app.db`.
4. Tests do not use real `data/uploads`.
5. Worker behavior is tested with fake transcriber.
6. Ruff passes.

---

# Slice 12 — CI Workflow

## Goal

Add GitHub Actions CI for `main` and `dev`.

## Scope

This slice adds automated test and lint checks.

## Tasks

Create:

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

Workflow steps:

- Checkout repository
- Install Python 3.13
- Install UV
- Run `uv sync`
- Run Ruff
- Run pytest

Commands:

```bash
uv run ruff check .
uv run pytest
```

Optionally:

```bash
uv run pytest --cov=app
```

No coverage gate.

## Tests

Push branch or run workflow locally if using a local GitHub Actions runner.

## Acceptance Criteria

This slice is complete when:

1. CI runs on push to `main` and `dev`.
2. CI runs on PRs targeting `main` and `dev`.
3. CI executes Ruff.
4. CI executes pytest.
5. CI passes.

---

# Slice 13 — README and Usage Documentation

## Goal

Document how to run, use, test, and understand the project.

## Scope

This slice creates practical documentation for local/internal development and usage.

## Tasks

Create or complete `README.md`.

Sections:

- Project overview
- Features
- Requirements
- Environment configuration
- Docker Compose startup
- Direct UV startup
- API endpoints
- curl examples
- Worker behavior
- Database migrations
- Testing
- Linting and formatting
- Optional Faster Whisper integration test
- Troubleshooting
- Architecture overview

Document first-time Docker startup:

```bash
cp .env.example .env
docker compose up --build
```

Document regular Docker startup:

```bash
docker compose up --build
```

Document direct UV startup:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run python -m app.worker.main
```

Document testing:

```bash
uv run pytest
uv run pytest --cov=app
uv run pytest -m integration
```

Document linting:

```bash
uv run ruff check .
uv run ruff format .
```

Document API examples.

Create job:

```bash
curl -X POST http://localhost:8000/api/v1/transcriptions \
  -F 'audio=@sample.mp3' \
  -F 'language=pt'
```

Fetch job:

```bash
curl http://localhost:8000/api/v1/transcriptions/{job_id}
```

List jobs:

```bash
curl 'http://localhost:8000/api/v1/transcriptions?limit=20&offset=0'
```

Filter failed jobs:

```bash
curl 'http://localhost:8000/api/v1/transcriptions?status=failed'
```

Health:

```bash
curl http://localhost:8000/health
```

Document OpenAPI docs:

```text
/docs
/openapi.json
```

## Tests

Manual documentation review.

Verify commands are accurate.

## Acceptance Criteria

This slice is complete when:

1. README explains setup clearly.
2. Docker and direct UV commands are documented.
3. API examples are documented.
4. Test and Ruff commands are documented.
5. Worker behavior is explained.
6. Known limitations are documented.

---

# Slice 14 — Final Cleanup and Acceptance Pass

## Goal

Verify the full v1 implementation against the approved functional and architecture specifications.

## Scope

This slice is for polish, consistency, bug fixing, and final readiness.

## Tasks

Review functional acceptance criteria.

Confirm:

- `POST /api/v1/transcriptions` works.
- `GET /api/v1/transcriptions/{job_id}` works.
- `GET /api/v1/transcriptions` works.
- `GET /health` works.
- Worker processes jobs.
- Uploaded audio is deleted after processing.
- Failed jobs are represented correctly.
- Docker Compose starts all services.
- Direct UV mode works.
- CI passes.

Review architecture consistency:

- Routes are thin.
- Service owns transactions.
- Repository does not commit.
- Storage handles filesystem concerns.
- Transcriber handles Faster Whisper concerns.
- No unnecessary interfaces were introduced.
- No Redis, Celery, RQ, or Dramatiq added.

Review code style:

- Single quotes where possible.
- Ruff formatting applied.
- Type hints present.
- No unused code.
- No dead abstractions.

Review ignored files:

- `.env` not committed.
- `data/` not committed.
- `.dockerignore` excludes `data` and `.env`.
- `.gitignore` generated using `ignr`.

Run final commands:

```bash
uv run ruff format .
uv run ruff check .
uv run pytest
uv run pytest --cov=app
docker compose up --build
```

Manual end-to-end check:

1. Start Docker Compose.
2. Check `/health`.
3. Upload sample audio.
4. Confirm job is `pending`.
5. Wait for worker.
6. Fetch job.
7. Confirm status is `completed` or `failed` with clean error.
8. Confirm uploaded audio was deleted.
9. Confirm list endpoint shows the job.

## Acceptance Criteria

This slice is complete when:

1. All tests pass.
2. Ruff passes.
3. Docker Compose startup works.
4. Direct UV startup works.
5. API endpoints behave as specified.
6. Worker behavior matches specification.
7. README is accurate.
8. CI passes.
9. The implementation matches the functional and architecture specs.

---

# 5. Suggested Implementation Sequence by Commits

A practical commit sequence could be:

1. `chore: initialize uv project and base structure`
2. `chore: add settings, database session, and alembic`
3. `feat: add transcription job model and repository`
4. `feat: add local audio storage and create job endpoint`
5. `feat: add job retrieval and listing endpoints`
6. `feat: add health check and startup validation`
7. `feat: add worker polling and job claiming`
8. `feat: add job processing flow with fake transcriber support`
9. `feat: integrate faster whisper transcriber`
10. `chore: add dockerfile and docker compose`
11. `test: harden API service and worker tests`
12. `ci: add github actions workflow`
13. `docs: add README usage documentation`
14. `chore: final cleanup and acceptance pass`

---

# 6. Implementation Notes and Defaults

## 6.1 Error Field

Use only:

```text
error_message
```

Do not add `error_code` in v1.

## 6.2 No Retry Endpoint

Do not implement a retry endpoint in v1.

## 6.3 No Delete Endpoint

Do not implement a delete endpoint in v1.

## 6.4 No Cancel Endpoint

Do not implement cancellation in v1.

## 6.5 Do Not Expose Stored Audio Path in API if Avoidable

Although `stored_audio_path` exists in the database, the API does not need to expose it to clients.

Recommended API response behavior:

- Keep `stored_audio_path` internal.
- Do not include it in `TranscriptionJobResponse`.
- Do not include it in `TranscriptionJobListItem`.

Rationale:

- It is an internal filesystem detail.
- The audio is deleted after processing.
- Clients do not need this path.

The database still keeps it for worker processing and historical debugging.

## 6.6 Keep List Endpoint Lightweight

Do not include `text` in list items.

Use the detail endpoint for full transcription text.

## 6.7 Keep Worker Single-Process

Do not implement multi-worker safety in v1.

The system is explicitly designed for one worker process.

---

# 7. Definition of Done for v1

The v1 implementation is done when:

1. The project can be installed with UV.
2. The project can be run with Docker Compose using:

```bash
cp .env.example .env
docker compose up --build
```

3. The project can also be run directly with UV.
4. Alembic creates the SQLite schema.
5. The API exposes:

```http
POST /api/v1/transcriptions
GET /api/v1/transcriptions/{job_id}
GET /api/v1/transcriptions
GET /health
```

6. The API validates:

- Allowed audio extensions
- Max file size
- Empty files
- Optional language format

7. The worker:

- Loads Faster Whisper
- Resets stuck processing jobs
- Polls pending jobs
- Processes oldest pending job first
- Stores results
- Marks failures
- Deletes uploaded audio

8. Tests cover:

- Unit logic
- API behavior
- Worker behavior

9. Real Faster Whisper test is optional and marked `integration`.
10. Ruff linting and formatting are configured.
11. CI runs pytest and Ruff on `main`/`dev` push and pull requests.
12. README documents setup, usage, testing, and limitations.

---

# 8. Next Step After This Plan

After this implementation plan is approved, the next practical step is to start generating the actual project files in the order of the slices.

The first implementation task would be:

```text
Slice 1 — Project skeleton and development tooling
```

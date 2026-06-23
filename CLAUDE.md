# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This repository currently contains only planning documents under `ai/docs/`. No application code exists yet. The three specs there are the source of truth for everything that gets built — read them before writing code, and keep implementation consistent with them rather than improvising new conventions.

- `ai/docs/functional-specification.md` — what the system must do (endpoints, validation rules, job lifecycle, error responses, exact JSON shapes).
- `ai/docs/architecture-specification.md` — how it must be built (layering, project structure, class responsibilities, settings, Docker, testing strategy).
- `ai/docs/vertical-slice-implementation-plan.md` — the prescribed build order, broken into 14 vertical slices, each touching API/worker → service → repository/storage/transcriber → DB/filesystem → tests in one pass. Follow this order when implementing from scratch; don't build isolated layers that can't run end-to-end.

## What this project is

An internal REST API for asynchronous audio transcription: **FastAPI** + **SQLite** + local filesystem + a single **Faster Whisper** worker process, deliberately kept simple (no Redis/Celery/Postgres/object storage/auth in v1). Two runtime processes — API and worker — communicate only through SQLite; neither calls the other directly.

```
Client → FastAPI API → SQLite (jobs table, also acts as the queue) → polling Worker → Faster Whisper → SQLite updated with result
```

## Commands (once the project is scaffolded)

```bash
# install
uv sync

# migrations
uv run alembic upgrade head

# run API (direct)
uv run uvicorn app.main:app --reload

# run worker (direct)
uv run python -m app.worker.main

# docker compose (runs migrate, api, worker)
cp .env.example .env   # first time only
docker compose up --build

# lint / format
uv run ruff check .
uv run ruff format .

# tests
uv run pytest                    # default suite, excludes real-Faster-Whisper integration tests
uv run pytest --cov=app
uv run pytest -m integration     # explicit opt-in, requires real Faster Whisper
```

There is no Makefile/Taskfile/Justfile — use these commands directly (per architecture spec §24.3).

## Architecture (target shape, per the specs)

Layered, not hexagonal — concrete classes only, no generic interfaces for repository/storage/transcriber in v1:

```
API layer (FastAPI routes, schemas)        Worker entrypoint
        ↓                                          ↓
        Application service layer (TranscriptionService) — owns DB transactions
                        ↓
        Repository / Storage / Transcriber layer
                        ↓
        SQLite / filesystem / Faster Whisper
```

- **API layer** (`app/api/`): thin routes, request parsing, response schemas, HTTP status codes. No business logic.
- **Application service** (`app/application/services/transcription_service.py`): a single `TranscriptionService` class owns all use cases (create/get/list/claim/process job, reset stuck jobs) and owns commit/rollback. Repositories never commit; routes and worker entrypoints never contain transaction logic beyond opening/closing a session.
- **Repository** (`app/infrastructure/repositories/transcription_job_repository.py`): plain SQLAlchemy 2.0 ORM queries (`Mapped`, `mapped_column`, `select`). Receives an active session; never creates one, never commits, never touches files or the transcriber.
- **Storage** (`app/infrastructure/storage/local_audio_storage.py`): `LocalAudioStorage` — local filesystem only, files named `{job_id}.{extension}`. Deletion must be safe to call on missing files (no crash on cleanup after failure).
- **Transcriber** (`app/infrastructure/transcriber/faster_whisper_transcriber.py`): `FasterWhisperTranscriber`, model loaded once at worker startup and reused. If model loading fails, the worker exits without entering the polling loop — it does not mark jobs failed for this.
- **Domain** (`app/domain/enums.py`): only domain concept is `TranscriptionJobStatus` (`pending`/`processing`/`completed`/`failed`, `StrEnum`). No separate domain dataclasses — the SQLAlchemy model is the internal job representation; Pydantic schemas shape API output.

API and worker are separate processes sharing the same codebase, settings, database, and `./data` filesystem mount — they do not call each other.

### Job lifecycle

`pending → processing → completed|failed`, plus `processing → pending` only as worker-startup crash recovery. No retry/cancel/delete endpoints, no automatic retries.

### Key invariants to preserve when implementing

- Generate the job UUID **before** saving the file; filename is `{job_id}.{ext}`. If DB job creation fails after the file was saved, delete the saved file. If file save fails, no job is created.
- Worker claims the **oldest pending** job (`created_at ASC`); the list endpoint orders **newest first** (`created_at DESC`) — these are intentionally different.
- List endpoint returns summary items (`TranscriptionJobListItem`) and never includes `text` or `stored_audio_path`; only the single-job endpoint (`TranscriptionJobResponse`) includes `text`. `stored_audio_path` is never exposed via the API.
- Worker deletes the uploaded audio file after processing regardless of success or failure; deletion errors are logged, not raised.
- Missing audio file at processing time → job marked `failed` with the exact client-facing message `Audio file is no longer available.` (no retry).
- Transcription exceptions → job marked `failed` with the exact message `Could not transcribe the audio file.`; full exception/stack trace goes to worker logs only, never to the API response.
- Successful transcription with empty output text is still `completed` (with `text = ''`), not a failure.
- Transcription text is normalized: join segment texts, strip, collapse repeated whitespace.
- Language: if the client supplied `language`, keep it as-is; if null, store whatever Faster Whisper detects. Validate with `^[a-z]{2,5}$` at upload time.
- Upload validation (extensions `mp3`/`wav`/`m4a`/`ogg`/`webm`, 25 MB max, reject empty) lives in the service layer / a small helper, not scattered in the route.
- Single-worker, single-job-at-a-time is an explicit v1 assumption — do not add concurrency or multi-worker safety.
- All timestamps via `app/utils/time.py`'s `utc_now()` (UTC-aware), never naive datetimes.

### Testing conventions

- Default `uv run pytest` must never require a real Faster Whisper model — use the `FakeTranscriber` pattern from the architecture spec (§25.3) in unit/API/worker tests.
- Use in-memory SQLite for unit/API tests, temp file-backed SQLite for worker/integration tests; use `tmp_path` for upload directories. Never touch the real `./data` dev database or upload dir from tests.
- Real-Faster-Whisper tests must be marked `@pytest.mark.integration` and excluded from the default run (`-m "not integration"`).
- Test layout: `tests/unit/`, `tests/api/`, `tests/worker/`, `tests/integration/`.

### Style

- Ruff for lint + format; prefer single quotes in Python strings. No mypy/pyright required in v1. Type hints throughout, but unenforced.

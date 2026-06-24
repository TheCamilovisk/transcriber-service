# Audio Transcription API

An internal REST API for asynchronous audio transcription using
[Faster Whisper](https://github.com/SYSTRAN/faster-whisper). Designed for
local/internal development — deliberately simple, with no external
dependencies beyond SQLite and the filesystem.

```
Client → FastAPI API → SQLite (jobs table) → polling Worker → Faster Whisper → result
```

## Features

- **POST** upload audio files for transcription (mp3, wav, m4a, ogg, webm;
  up to 25 MB).
- **GET** fetch a single transcription job (includes transcript text).
- **GET** list transcription jobs with optional status filter, pagination.
- **GET** health check endpoint.
- **Worker** polls SQLite for pending jobs, transcribes with Faster Whisper,
  and stores results.
- **Graceful shutdown** on SIGTERM/SIGINT.
- **Crash recovery** — jobs stuck in `processing` on worker restart are
  reset to `pending`.
- **OpenAPI docs** at `/docs`.

## Requirements

- **Docker** (Docker Compose v2) — recommended for easiest setup.
- **Or** Python 3.13+ with `uv` for direct execution.
- **Optional: NVIDIA GPU** for faster inference — see [GPU Host Setup](#gpu-host-setup-optional) below. Falls back to CPU if not configured.

The **Faster Whisper model** (~1 GB for the default `small` model) is
downloaded automatically on first worker start.

### GPU Host Setup (optional)

The worker can use an NVIDIA GPU for much faster transcription. This
requires host-level setup outside this repo — Docker Compose can request a
GPU, but it can't install drivers for you.

1. **Install the NVIDIA GPU driver** on the host (not in a container).
   Verify with `nvidia-smi` on the host before continuing.
2. **Install the NVIDIA Container Toolkit** so Docker containers can see
   the GPU. Full instructions:
   https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

   Short version (apt-based hosts):

   ```bash
   curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
   curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
     sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
     sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
   sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

3. **Verify Docker can see the GPU** before relying on this repo's compose
   file:

   ```bash
   docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
   ```

   If this doesn't print the GPU, fix the host/toolkit setup first — the
   `worker` service's GPU reservation in `docker-compose.yml` won't help
   otherwise.

Once the host is ready, `.env.example` already defaults to
`FASTER_WHISPER_DEVICE=cuda` / `FASTER_WHISPER_COMPUTE_TYPE=float16`. On a
machine without a GPU, uncomment the CPU fallback lines in `.env` instead.

## Quick Start

### 1. Clone and configure

```bash
git clone <repository-url>
cd transcriber-service
cp .env.example .env
```

The default `.env` works out of the box with Docker Compose. For direct UV
startup, uncomment the local-development database paths in `.env`.

### 2. Start with Docker Compose

```bash
docker compose up --build
```

This starts three services:

1. **migrate** — runs database migrations, then exits.
2. **api** — FastAPI server on port 8000.
3. **worker** — polling loop that processes transcription jobs.

The worker will download the Faster Whisper model on first run (may take a
minute). The API becomes available immediately.

### 3. Direct UV startup (no Docker)

```bash
uv sync
uv run alembic upgrade head
```

Then in two separate terminals:

```bash
# Terminal 1 — API server
uv run uvicorn app.main:app --reload
```

```bash
# Terminal 2 — Worker
uv run python -m app.worker.main
```

## Environment Configuration

Configuration is loaded from `.env` (see `.env.example` for all options).

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/app.db` | SQLite database path |
| `UPLOAD_DIR` | `./data/uploads` | Audio file upload directory |
| `MAX_UPLOAD_SIZE_MB` | `25` | Maximum upload file size |
| `WORKER_POLL_INTERVAL_SECONDS` | `3` | Seconds between worker poll cycles |
| `FASTER_WHISPER_MODEL_SIZE` | `small` | Model size (tiny, small, medium, large-v3) |
| `FASTER_WHISPER_DEVICE` | `cuda` | Device (`cuda` for GPU, `cpu` otherwise — see [GPU Host Setup](#gpu-host-setup-optional)) |
| `FASTER_WHISPER_COMPUTE_TYPE` | `float16` | Compute type (float16/float32 for GPU, int8 for CPU) |

Docker defaults use `/app/data/...` paths. For local (non-Docker) development,
uncomment the local paths in `.env.example`.

## API Endpoints

### POST `/api/v1/transcriptions`

Create a new transcription job. Accepts multipart form data.

**Parameters:**

| Field | Type | Required | Description |
|---|---|---|---|
| `audio` | file | yes | Audio file (mp3, wav, m4a, ogg, webm) |
| `language` | string | no | Language code (e.g. `pt`, `en`). Must match `^[a-z]{2,5}$`. |

**Response** `201 Created`:

```json
{
  "id": "uuid-string",
  "status": "pending",
  "original_filename": "recording.mp3",
  "content_type": "audio/mpeg",
  "file_size_bytes": 123456,
  "language": "pt",
  "error_message": null,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z",
  "started_at": null,
  "finished_at": null,
  "text": null
}
```

**Errors:**

| Status | Detail |
|---|---|
| 400 | Unsupported file extension or empty file |
| 413 | Uploaded audio file exceeds the 25 MB limit |
| 422 | Missing audio field, invalid multipart format, or invalid language value |

### GET `/api/v1/transcriptions/{job_id}`

Fetch a single transcription job. Includes transcript text.

**Response** `200 OK`:

```json
{
  "id": "uuid-string",
  "status": "completed",
  "original_filename": "recording.mp3",
  "content_type": "audio/mpeg",
  "file_size_bytes": 123456,
  "language": "pt",
  "error_message": null,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:02Z",
  "started_at": "2025-01-01T00:00:01Z",
  "finished_at": "2025-01-01T00:00:02Z",
  "text": "Transcribed text content here."
}
```

**Errors:**

| Status | Detail |
|---|---|
| 404 | Transcription job not found |

### GET `/api/v1/transcriptions`

List transcription jobs (newest first). Supports optional status filter and
pagination. Never returns transcript text.

**Query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 20 | Max items (1–100) |
| `offset` | integer | 0 | Pagination offset |
| `status` | string | — | Filter: `pending`, `processing`, `completed`, `failed` |

**Response** `200 OK`:

```json
{
  "items": [
    {
      "id": "uuid-string",
      "status": "completed",
      "original_filename": "recording.mp3",
      "content_type": "audio/mpeg",
      "file_size_bytes": 123456,
      "language": "pt",
      "error_message": null,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:02Z",
      "started_at": "2025-01-01T00:00:01Z",
      "finished_at": "2025-01-01T00:00:02Z"
    }
  ],
  "limit": 20,
  "offset": 0,
  "total": 1
}
```

### GET `/health`

Health check endpoint. Reports database and upload directory status.

**Response** `200 OK`:

```json
{
  "status": "ok",
  "database": "ok",
  "upload_dir": "ok"
}
```

If either dependency is unhealthy: `503` and `"status": "error"`.

## curl Examples

### Create a transcription job

```bash
curl -X POST http://localhost:8000/api/v1/transcriptions \
  -F 'audio=@sample.mp3' \
  -F 'language=pt'
```

### Create a job (auto-detect language)

```bash
curl -X POST http://localhost:8000/api/v1/transcriptions \
  -F 'audio=@sample.mp3'
```

### Fetch a job by ID

```bash
curl http://localhost:8000/api/v1/transcriptions/{job_id}
```

### List jobs (default: newest first, 20 per page)

```bash
curl 'http://localhost:8000/api/v1/transcriptions?limit=20&offset=0'
```

### Filter failed jobs

```bash
curl 'http://localhost:8000/api/v1/transcriptions?status=failed'
```

### Health check

```bash
curl http://localhost:8000/health
```

### OpenAPI docs

```text
http://localhost:8000/docs
http://localhost:8000/openapi.json
```

## Worker Behavior

The worker is a separate process that runs a polling loop:

1. On startup, it validates database connectivity and upload directory
   writability. It resets any jobs stuck in `processing` back to `pending`
   (crash recovery).
2. It loads the Faster Whisper model once. If loading fails, the worker
   exits without entering the polling loop.
3. It polls SQLite every `WORKER_POLL_INTERVAL_SECONDS` for the oldest
   pending job.
4. When a job is claimed:
   - The uploaded audio file is transcribed.
   - The result is stored in the database.
   - The audio file is deleted from disk (regardless of success or failure).
5. On SIGTERM/SIGINT, the worker finishes its current job and stops
   gracefully.

**Error handling:**

| Scenario | Result |
|---|---|
| Audio file missing at processing time | Job marked `failed` with `"Audio file is no longer available."` |
| Transcription exception | Job marked `failed` with `"Could not transcribe the audio file."` (full traceback in worker logs only) |
| Empty transcription text | Job marked `completed` with `"text": ""` (not a failure) |

## Database Migrations

Migrations use Alembic. The migration history lives in `alembic/versions/`.

```bash
# Run pending migrations
uv run alembic upgrade head

# Create a new migration (auto-detect changes)
uv run alembic revision --autogenerate -m "description"

# View migration history
uv run alembic history
```

With Docker Compose, migrations run automatically via the `migrate` service
before the API and worker start.

## Testing

### Default test suite (excludes real Faster Whisper)

```bash
uv run pytest
```

### Test with coverage

```bash
uv run pytest --cov=app
```

### Integration tests (requires real Faster Whisper model)

```bash
uv run pytest -m integration
```

Tests are organized by concern, not mirrored source paths:

- `tests/unit/` — unit tests for services, repositories, transcriber, settings
- `tests/api/` — HTTP-level tests via `httpx` async client
- `tests/worker/` — worker claiming and job processing tests
- `tests/integration/` — real Faster Whisper integration tests (opt-in)

## Linting and Formatting

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .
```

The CI workflow runs both on every push to `dev` and on pull requests.

## Troubleshooting

### Worker fails to start

Ensure the Faster Whisper model can be downloaded — the worker needs
internet access on first run. Check worker logs for model download errors.

### "Database connectivity check failed"

Make sure migrations have been run (`uv run alembic upgrade head`). With
Docker Compose, the `migrate` service handles this automatically.

### Port 8000 already in use

Change the port mapping in `docker-compose.yml` or set `API_PORT` in `.env`.

### Audio upload fails

Check that `UPLOAD_DIR` exists and is writable. The API validates file
extension (mp3, wav, m4a, ogg, webm), file size (max 25 MB), and rejects
empty files.

### GPU not detected / falls back to CPU

If the worker logs show `device=cuda` but transcription is slow or the
worker fails to load the model, check, in order:

1. `nvidia-smi` works on the **host** (not in a container).
2. `docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi`
   works — if not, the NVIDIA Container Toolkit isn't installed/configured;
   see [GPU Host Setup](#gpu-host-setup-optional).
3. `docker exec <worker_container> nvidia-smi` shows the GPU inside the
   running worker container.

If the host has no GPU at all, set `FASTER_WHISPER_DEVICE=cpu` and
`FASTER_WHISPER_COMPUTE_TYPE=int8` in `.env` instead.

## Architecture Overview

```
┌─────────────┐     HTTP      ┌──────────────┐     SQL     ┌──────────┐
│   Client    │ ────────────> │  FastAPI API  │ ──────────> │  SQLite  │
│  (curl,     │ <──────────── │  (port 8000)  │ <────────── │ jobs.db  │
│   app, etc) │               └──────────────┘             └──────────┘
                                              ▲                 │
                                              │                 │ poll
                                              │                 ▼
                                              │          ┌──────────────┐
                                              │          │   Worker     │
                                              │          │  (polling)   │
                                              │          │  ┌─────────┐ │
                                              │          │  │Faster   │ │
                                              │          │  │Whisper  │ │
                                              │          │  └─────────┘ │
                                              └──────────└──────────────┘
```

Layered architecture — no Redis, Celery, Postgres, or authentication in v1.

| Layer | Directory | Responsibility |
|---|---|---|
| **API** | `app/api/` | Thin routes, request parsing, response schemas |
| **Application** | `app/application/services/` | `TranscriptionService` owns all use cases and transactions |
| **Infrastructure** | `app/infrastructure/repositories/` | SQLAlchemy ORM queries |
| | `app/infrastructure/storage/` | Local filesystem audio storage |
| | `app/infrastructure/transcriber/` | Faster Whisper integration |
| **Domain** | `app/domain/` | Enums (no separate domain objects in v1) |

The API and worker are separate processes sharing the same codebase,
database, and filesystem. They communicate only through SQLite — neither
calls the other directly.

## Known Limitations

- **Single worker, single job at a time.** No concurrent processing or
  multi-worker safety.
- **No retry or cancel endpoints.** Failed jobs must be re-uploaded.
- **No authentication.** Intended for internal/local use only.
- **No object storage.** Audio files are stored on the local filesystem.
- **SQLite only.** Not suitable for multi-worker horizontal scaling.

# Functional Specification — Audio Transcription API

## 1. Purpose

The **Audio Transcription API** is an internal REST API for asynchronous transcription of audio files using **Faster Whisper**.

The API receives an audio file from a trusted backend service or local/internal script, creates a transcription job, and returns the job information immediately. A separate worker process later processes the job and stores the transcription result. Clients fetch the job status and result by polling the API.

This specification defines the functional behavior of the application.

---

## 2. Product Scope

### 2.1 Intended Clients

The API is intended for:

- Other backend services
- Internal/local scripts

It is not primarily designed for a browser frontend, mobile app, or public external consumers.

### 2.2 Exposure Model

The API is **internal-only** in version 1.

It is assumed to run in a trusted private environment, such as:

- Local machine
- Private development environment
- Internal network
- Private service-to-service setup

The API must not be exposed publicly without adding authentication and other hardening measures.

### 2.3 Authentication

Version 1 has **no authentication**.

This is acceptable only because the service is internal-only.

Future versions may add API key authentication if the service becomes remotely accessible or exposed to additional trusted services.

---

## 3. Core User Flow

The transcription flow is always asynchronous.

1. Client uploads an audio file to the API.
2. API validates the file.
3. API stores the uploaded audio temporarily.
4. API creates a transcription job with status `pending`.
5. API returns the created job immediately.
6. Worker polls for pending jobs.
7. Worker claims the oldest pending job.
8. Worker transcribes the audio using Faster Whisper.
9. Worker stores the transcription result in the database.
10. Worker deletes the original uploaded audio file.
11. Client polls the API to fetch job status and result.

The API does not support synchronous transcription in v1.

The API does not support webhooks or callbacks in v1.

Clients are expected to poll the job endpoint.

---

## 4. Functional Requirements

## 4.1 Create Transcription Job

The system must provide an endpoint for creating a transcription job by uploading an audio file.

```http
POST /api/v1/transcriptions
```

Request format:

```http
Content-Type: multipart/form-data
```

Accepted form fields:

| Field      | Required | Type   | Description                     |
| ---------- | -------: | ------ | ------------------------------- |
| `audio`    |      Yes | File   | Audio file to transcribe        |
| `language` |       No | String | Optional ISO-like language code |

Example:

```bash
curl -X POST http://localhost:8000/api/v1/transcriptions \
  -F 'audio=@sample.mp3' \
  -F 'language=pt'
```

### 4.1.1 Upload Behavior

When a valid request is received, the API must:

1. Validate the uploaded file.
2. Validate the optional language value.
3. Generate a UUID for the job.
4. Save the uploaded audio file using the job UUID as filename.
5. Create a database job record with status `pending`.
6. Return the full created job representation.

The upload flow must generate the job UUID before saving the file.

The stored filename must use the job UUID and preserve the original extension.

Example:

```text
Original filename:
meeting-audio.mp3

Job ID:
8f4b2d6e-91b5-4d3a-a36f-78f2f3c1c9a1

Stored path:
uploads/8f4b2d6e-91b5-4d3a-a36f-78f2f3c1c9a1.mp3
```

If file saving fails, no job should be created.

If database job creation fails after the file was saved, the saved file should be deleted.

### 4.1.2 Upload Response

The upload endpoint must return the full created job representation.

Initial values:

| Field           | Initial Value |
| --------------- | ------------- |
| `status`        | `pending`     |
| `text`          | `null`        |
| `error_message` | `null`        |
| `started_at`    | `null`        |
| `finished_at`   | `null`        |

Example response:

```json
{
  "id": "8f4b2d6e-91b5-4d3a-a36f-78f2f3c1c9a1",
  "status": "pending",
  "original_filename": "meeting-audio.mp3",
  "content_type": "audio/mpeg",
  "file_size_bytes": 1234567,
  "language": "pt",
  "text": null,
  "error_message": null,
  "created_at": "2026-06-23T14:30:00+00:00",
  "updated_at": "2026-06-23T14:30:00+00:00",
  "started_at": null,
  "finished_at": null
}
```

---

## 4.2 Fetch Transcription Job

The system must provide an endpoint for fetching a single transcription job.

```http
GET /api/v1/transcriptions/{job_id}
```

The `job_id` must be a valid UUID.

If the job exists, the API must return the full job representation.

The response shape must be stable across all statuses.

- `text` is `null` until the job is completed.
- `error_message` is `null` unless the job failed.

Example pending response:

```json
{
  "id": "8f4b2d6e-91b5-4d3a-a36f-78f2f3c1c9a1",
  "status": "pending",
  "original_filename": "meeting-audio.mp3",
  "content_type": "audio/mpeg",
  "file_size_bytes": 1234567,
  "language": "pt",
  "text": null,
  "error_message": null,
  "created_at": "2026-06-23T14:30:00+00:00",
  "updated_at": "2026-06-23T14:30:00+00:00",
  "started_at": null,
  "finished_at": null
}
```

Example completed response:

```json
{
  "id": "8f4b2d6e-91b5-4d3a-a36f-78f2f3c1c9a1",
  "status": "completed",
  "original_filename": "meeting-audio.mp3",
  "content_type": "audio/mpeg",
  "file_size_bytes": 1234567,
  "language": "pt",
  "text": "Hello, this is the transcribed audio text.",
  "error_message": null,
  "created_at": "2026-06-23T14:30:00+00:00",
  "updated_at": "2026-06-23T14:31:20+00:00",
  "started_at": "2026-06-23T14:30:05+00:00",
  "finished_at": "2026-06-23T14:31:20+00:00"
}
```

Example failed response:

```json
{
  "id": "8f4b2d6e-91b5-4d3a-a36f-78f2f3c1c9a1",
  "status": "failed",
  "original_filename": "meeting-audio.mp3",
  "content_type": "audio/mpeg",
  "file_size_bytes": 1234567,
  "language": "pt",
  "text": null,
  "error_message": "Could not transcribe the audio file.",
  "created_at": "2026-06-23T14:30:00+00:00",
  "updated_at": "2026-06-23T14:30:18+00:00",
  "started_at": "2026-06-23T14:30:05+00:00",
  "finished_at": "2026-06-23T14:30:18+00:00"
}
```

### 4.2.1 Not Found Behavior

If the job does not exist, the API must return:

```http
404 Not Found
```

Response:

```json
{
  "detail": "Transcription job not found."
}
```

### 4.2.2 Invalid UUID Behavior

If the job ID is not a valid UUID, FastAPI/Pydantic validation should return:

```http
422 Unprocessable Entity
```

---

## 4.3 List Transcription Jobs

The system must provide an endpoint for listing transcription jobs.

```http
GET /api/v1/transcriptions
```

The list endpoint must support pagination.

Query parameters:

| Parameter | Required | Default | Maximum | Description               |
| --------- | -------: | ------: | ------: | ------------------------- |
| `limit`   |       No |    `20` |   `100` | Number of items to return |
| `offset`  |       No |     `0` |     N/A | Number of items to skip   |
| `status`  |       No |     N/A |     N/A | Optional status filter    |

Allowed status filter values:

- `pending`
- `processing`
- `completed`
- `failed`

Example:

```http
GET /api/v1/transcriptions?status=failed&limit=20&offset=0
```

### 4.3.0 Pagination and Filter Validation

`limit` must be between `1` and `100` inclusive. `offset` must be `0` or greater. `status`, when provided, must be one of the four allowed status values.

Any of the following must return `422 Unprocessable Entity` via standard FastAPI/Pydantic query parameter validation, the same mechanism used for invalid UUID path parameters:

- `limit` less than `1` or greater than `100`
- `offset` less than `0`
- `status` not one of `pending`, `processing`, `completed`, `failed`

No custom validation code is required for these cases; declaring the query parameters with the appropriate constraints (`Query(ge=1, le=100)`, `Query(ge=0)`, and an enum type for `status`) is sufficient.

### 4.3.1 Ordering

The list endpoint must return newest jobs first.

```text
created_at DESC
```

This differs from worker processing order, which uses oldest pending jobs first.

### 4.3.2 List Response Shape

The list endpoint must return summary items only.

It must not include the full transcription text.

Example response:

```json
{
  "items": [
    {
      "id": "8f4b2d6e-91b5-4d3a-a36f-78f2f3c1c9a1",
      "status": "completed",
      "original_filename": "meeting-audio.mp3",
      "content_type": "audio/mpeg",
      "file_size_bytes": 1234567,
      "language": "pt",
      "error_message": null,
      "created_at": "2026-06-23T14:30:00+00:00",
      "updated_at": "2026-06-23T14:31:20+00:00",
      "started_at": "2026-06-23T14:30:05+00:00",
      "finished_at": "2026-06-23T14:31:20+00:00"
    }
  ],
  "limit": 20,
  "offset": 0,
  "total": 135
}
```

The client must use the single-job endpoint to retrieve the transcription text.

---

## 4.4 Health Check

The system must provide a health check endpoint.

```http
GET /health
```

The health check must verify:

- API process is running
- SQLite database is reachable
- Upload directory exists and is writable

Example successful response:

```json
{
  "status": "ok",
  "database": "ok",
  "upload_dir": "ok"
}
```

If a required dependency is unavailable, the endpoint must return `503 Service Unavailable` with a structured body showing the per-check status, not a generic `detail` message. Each check reports `ok` or `error` independently:

```json
{
  "status": "error",
  "database": "error",
  "upload_dir": "ok"
}
```

```json
{
  "status": "error",
  "database": "ok",
  "upload_dir": "error"
}
```

The top-level `status` is `error` if any individual check fails.

---

# 5. Audio Upload Requirements

## 5.1 Accepted Formats

Version 1 must accept the following file extensions:

- `mp3`
- `wav`
- `m4a`
- `ogg`
- `webm`

The API performs light validation based on:

- File extension
- File size
- Empty file check

The worker/transcriber performs deeper validation during decoding/transcription.

## 5.2 Maximum File Size

The maximum upload size is:

```text
25 MB
```

If the uploaded file exceeds this limit, the API must return:

```http
413 Payload Too Large
```

Example response:

```json
{
  "detail": "Uploaded audio file exceeds the 25 MB limit."
}
```

## 5.3 Empty File

If the uploaded file is empty, the API must return:

```http
400 Bad Request
```

Example response:

```json
{
  "detail": "Uploaded audio file is empty."
}
```

`file_size_bytes` and the empty-file check are both based on the number of bytes actually written to disk during `save_upload`, never on a client-supplied `Content-Length` header. This keeps both checks consistent and not spoofable via headers.

## 5.4 Unsupported Format

If the file extension is unsupported, the API must return:

```http
400 Bad Request
```

Example response:

```json
{
  "detail": "Unsupported audio format. Allowed formats: mp3, wav, m4a, ogg, webm."
}
```

### 5.4.1 Extension Extraction Rule

The extension is extracted as the last suffix of the original filename, compared case-insensitively against the allowed list:

- `meeting.MP3` → extension `mp3` (lowercased) → accepted.
- `meeting` (no extension) → unsupported format → rejected.
- `meeting.mp3.exe` → extension `exe` (last suffix only) → rejected.

The stored filename (`{job_id}.{extension}`) always uses the lowercased extension, regardless of the case the client sent.

## 5.5 Content Type

The API should store the uploaded file content type when provided by the client.

The API must not require content type.

The API must not validate content type against a strict allowlist in v1.

A job may have:

```json
{
  "content_type": "audio/mpeg"
}
```

or:

```json
{
  "content_type": null
}
```

## 5.6 Duration Limit

Version 1 has no explicit audio duration limit.

Only the 25 MB file size limit is enforced.

---

# 6. Language Handling

The upload endpoint accepts an optional `language` field.

Example:

```bash
curl -X POST http://localhost:8000/api/v1/transcriptions \
  -F 'audio=@sample.mp3' \
  -F 'language=pt'
```

## 6.1 Language Validation

The `language` value must be a simple ISO-like lowercase language code.

Accepted pattern:

```regex
^[a-z]{2,5}$
```

Examples:

- `pt`
- `en`
- `es`
- `fr`

The API does not maintain a full allowlist of supported languages in v1.

Invalid language values should be rejected at upload time.

## 6.2 Language Storage Behavior

The job uses a single `language` field.

If the client provides a language, the job stores that value.

If the client does not provide a language, the job initially stores `null`.

When Faster Whisper auto-detects the language, the worker stores the detected language in the same field.

Examples:

```text
Client sends language=pt
→ job.language starts as pt
→ worker keeps language as pt

Client omits language
→ job.language starts as null
→ worker stores detected language, for example pt
```

---

# 7. Job Lifecycle

## 7.1 Supported Statuses

Version 1 supports exactly these statuses:

- `pending`
- `processing`
- `completed`
- `failed`

Meaning:

| Status       | Meaning                                          |
| ------------ | ------------------------------------------------ |
| `pending`    | Job was created and is waiting for the worker    |
| `processing` | Worker claimed the job and started transcription |
| `completed`  | Transcription finished successfully              |
| `failed`     | Transcription failed                             |

Version 1 does not support:

- `cancelled`
- `retrying`
- `expired`

## 7.2 Status Transitions

Expected normal transition:

```text
pending → processing → completed
```

Expected failure transition:

```text
pending → processing → failed
```

A job may also return from `processing` to `pending` during worker startup recovery if the worker previously crashed.

```text
processing → pending
```

This is allowed only as a recovery behavior.

## 7.3 Retry Behavior

Version 1 has no automatic retry mechanism.

If transcription fails during normal processing, the job becomes `failed`.

The system does not expose retry endpoints in v1.

A worker crash is handled separately by startup recovery, where stuck `processing` jobs are reset to `pending`.

## 7.4 Cancellation

Version 1 does not support job cancellation.

There is no cancel endpoint.

## 7.5 Deletion

Version 1 does not support deleting job records through the API.

There is no delete endpoint.

---

# 8. Worker Functional Behavior

The worker is a separate process from the API.

The worker uses SQLite as a simple job queue by polling for pending jobs.

There is no Redis, Celery, RQ, or Dramatiq in v1.

## 8.1 Worker Polling

The worker must poll the database for pending jobs.

The polling interval must be configurable.

Default:

```env
WORKER_POLL_INTERVAL_SECONDS=3
```

When idle, the worker waits for the configured interval before checking again.

## 8.2 Worker Concurrency

Version 1 supports:

- One worker process
- One job processed at a time

No configurable concurrency is required in v1.

Multiple worker processes are not officially supported in v1.

## 8.3 Job Claiming Order

The worker must process the oldest pending job first.

Ordering:

```text
created_at ASC
```

Conceptual query:

```sql
SELECT *
FROM transcription_jobs
WHERE status = 'pending'
ORDER BY created_at ASC
LIMIT 1;
```

After claiming a job, the worker must:

1. Mark the job as `processing`.
2. Set `started_at`.
3. Set `updated_at`.
4. Commit the change.
5. Run transcription.

## 8.4 Worker Startup Recovery

When the worker starts, it must reset jobs stuck in `processing` back to `pending`.

This handles cases where the worker crashed while processing a job.

If a reset job’s audio file no longer exists when processing is attempted, the worker must mark the job as failed.

Error message:

```text
Audio file is no longer available.
```

## 8.5 Missing Audio File

If the worker tries to process a job but the stored audio file does not exist, it must:

- Mark the job as failed
- Set `finished_at`
- Set `updated_at`
- Store a clean `error_message`
- Not delete the job record
- Not retry forever

Example:

```json
{
  "status": "failed",
  "text": null,
  "error_message": "Audio file is no longer available."
}
```

## 8.6 Worker Shutdown

Worker shutdown should be best-effort.

If idle:

- Stop immediately.

If processing:

- Try to finish the current job before stopping.

If force-killed:

- Startup recovery resets stuck `processing` jobs to `pending`.

Mechanism: the worker registers handlers for `SIGTERM` and `SIGINT` that set a `shutdown_requested` flag. The flag is checked between poll iterations and before claiming the next job. There is no timeout on an in-flight job — the worker lets the current job finish naturally before exiting. A force-kill (`SIGKILL`) bypasses this entirely and relies on startup recovery on the next launch.

## 8.7 Worker Logs

The worker should log important lifecycle events:

- Worker starting
- Loading Faster Whisper model
- Faster Whisper model loaded
- Reset stuck processing jobs to pending
- Waiting for jobs
- Claimed job `job_id=...`
- Started transcription `job_id=...`
- Completed job `job_id=...`
- Failed job `job_id=...`
- Worker shutdown requested

Logs related to a job must include `job_id`.

---

# 9. Transcription Behavior

## 9.1 Engine

Version 1 uses **Faster Whisper**.

The worker runs transcription locally.

No external transcription API is used.

## 9.2 Model Loading

The worker must load the Faster Whisper model once at startup.

The model must be reused for all jobs processed by that worker.

If the model cannot be loaded, the worker must exit with an error and must not enter the polling loop.

The worker must not mark jobs as failed due to model startup/configuration failure.

## 9.3 Model Configuration

The following settings must be configurable:

- `FASTER_WHISPER_MODEL_SIZE`
- `FASTER_WHISPER_DEVICE`
- `FASTER_WHISPER_COMPUTE_TYPE`

Defaults (Docker, GPU host with NVIDIA Container Toolkit configured):

```env
FASTER_WHISPER_MODEL_SIZE=small
FASTER_WHISPER_DEVICE=cuda
FASTER_WHISPER_COMPUTE_TYPE=float16
```

CPU fallback (no GPU available):

```env
FASTER_WHISPER_MODEL_SIZE=small
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8
```

Other supported model sizes:

```env
FASTER_WHISPER_MODEL_SIZE=base
FASTER_WHISPER_MODEL_SIZE=medium
```

## 9.4 Transcription Result

The completed job must contain:

- Plain transcription text
- Basic metadata

Version 1 does not expose:

- Segment-level timestamps
- Word-level timestamps
- Speaker diarization
- Translation

## 9.5 Text Assembly

Faster Whisper returns segments internally.

Version 1 must assemble the final text as one normalized plain-text result.

The system must:

- Join segment texts
- Strip leading/trailing whitespace
- Collapse repeated whitespace
- Store the normalized text in the job record

Example:

```text
Raw segments:
- " Hello,"
- "   this is a test."
- " Thank you."

Stored text:
"Hello, this is a test. Thank you."
```

## 9.6 Empty Transcription Result

If Faster Whisper completes successfully but produces no text, the job must still be marked as `completed`.

The `text` field should be an empty string.

Example:

```json
{
  "status": "completed",
  "text": "",
  "error_message": null
}
```

Silent or unintelligible audio is not treated as a system failure.

## 9.7 Transcription Failure

If Faster Whisper fails while processing a job, the worker must:

- Mark the job as failed
- Set a clean client-facing `error_message`
- Set `finished_at`
- Set `updated_at`
- Log the full exception and stack trace
- Delete the uploaded audio file after failure handling

The API must not expose internal stack traces.

Client-facing error example:

```json
{
  "status": "failed",
  "text": null,
  "error_message": "Could not transcribe the audio file."
}
```

---

# 10. Storage and Retention

## 10.1 Uploaded Audio Storage

Uploaded audio files are stored on the local filesystem.

The API and worker must share the same filesystem path or mounted volume.

The upload directory must be configurable.

Default direct local path:

```env
UPLOAD_DIR=./data/uploads
```

Default Docker path:

```env
UPLOAD_DIR=/app/data/uploads
```

## 10.2 Upload Directory Behavior

On startup, the API and worker should create the upload directory automatically if it does not exist.

Startup should fail only if the directory:

- Cannot be created
- Is not writable

## 10.3 Original Audio Retention

Uploaded audio is temporary.

The worker must delete the original audio file after processing finishes.

This applies to both:

- Completed jobs
- Failed jobs

The job metadata and transcription result remain stored.

## 10.4 Job Retention

Job records and transcription results are kept indefinitely in v1.

There is no automatic deletion of job records.

## 10.5 Duplicate Uploads

Version 1 does not perform duplicate detection.

Every uploaded audio file creates a new transcription job, even if the same audio was uploaded before.

---

# 11. Job Data Model

A transcription job must store the following fields:

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

Field meanings:

| Field               | Meaning                                                 |
| ------------------- | ------------------------------------------------------- |
| `id`                | UUID job identifier                                     |
| `status`            | `pending`, `processing`, `completed`, or `failed`       |
| `original_filename` | Original filename sent by the client                    |
| `stored_audio_path` | Temporary local path used by the worker before deletion |
| `content_type`      | Uploaded file MIME/content type, when provided          |
| `file_size_bytes`   | Uploaded file size                                      |
| `language`          | Requested language or detected language                 |
| `text`              | Final transcription text when completed                 |
| `error_message`     | Clean failure message when failed                       |
| `created_at`        | When the job was created                                |
| `updated_at`        | When the job was last updated                           |
| `started_at`        | When the worker started processing                      |
| `finished_at`       | When the job reached `completed` or `failed`            |

After processing finishes, the original audio file is deleted. The `stored_audio_path` may remain as historical metadata, but the file itself should no longer exist.

---

# 12. Timestamp Requirements

All timestamps must be generated as UTC-aware datetimes.

The API must return timestamps as UTC ISO 8601 values.

The implementation may use default Pydantic datetime serialization.

Both forms are acceptable:

```text
2026-06-23T14:30:00Z
2026-06-23T14:30:00+00:00
```

Documentation examples may use `Z`, but the implementation does not need custom serialization only to force the `Z` suffix.

---

# 13. API Error Handling

Version 1 uses FastAPI’s default error format.

Known application errors should return simple `detail` messages.

Example:

```json
{
  "detail": "Unsupported audio format."
}
```

## 13.1 Error Behavior Summary

| Case                            |     Status |
| ------------------------------- | ---------: |
| Invalid UUID path parameter     |        422 |
| Job not found                   |        404 |
| Unsupported audio extension     |        400 |
| Empty uploaded file             |        400 |
| Uploaded file exceeds 25 MB     |        413 |
| Invalid language value          | 422 or 400 |
| Invalid `limit`/`offset`        |        422 |
| Invalid `status` filter value   |        422 |
| Health check dependency failure |        503 |

---

# 14. API Schema Conventions

## 14.1 JSON Field Naming

API JSON fields must use `snake_case`.

Example:

```json
{
  "original_filename": "meeting.mp3",
  "file_size_bytes": 1234567,
  "error_message": null,
  "created_at": "2026-06-23T14:30:00+00:00"
}
```

No `camelCase` aliases are required in v1.

## 14.2 Response Schemas

The API should use separate response schemas for different response shapes.

Expected schemas:

### `TranscriptionJobResponse`

Full job representation.

Used by:

- `POST /api/v1/transcriptions`
- `GET /api/v1/transcriptions/{job_id}`

Includes `text`.

### `TranscriptionJobListItem`

Summary representation.

Used inside:

- `GET /api/v1/transcriptions`

Does not include `text`.

### `TranscriptionJobListResponse`

Contains:

- `items`
- `limit`
- `offset`
- `total`

---

# 15. Configuration Requirements

The application must use environment-based configuration.

Settings are loaded through Pydantic Settings.

The repository must include:

```text
.env.example
```

The repository must not commit:

```text
.env
```

## 15.1 Required/default Settings

Expected settings:

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
FASTER_WHISPER_DEVICE=cuda
FASTER_WHISPER_COMPUTE_TYPE=float16

# CPU fallback (host without an NVIDIA GPU / Container Toolkit):
# FASTER_WHISPER_DEVICE=cpu
# FASTER_WHISPER_COMPUTE_TYPE=int8

API_HOST=0.0.0.0
API_PORT=8000
```

The application should default to the local data directory if `DATABASE_URL` is not explicitly provided:

```python
database_url: str = 'sqlite:///./data/app.db'
```

The upload directory should default to:

```python
upload_dir: str = './data/uploads'
```

---

# 16. Local Execution Requirements

The project must support two local execution modes.

## 16.1 Docker Compose Mode

Docker Compose is the preferred easy startup path.

First-time setup:

```bash
cp .env.example .env
docker compose up --build
```

Regular startup after `.env` exists:

```bash
docker compose up --build
```

Docker Compose must run:

- Migration service
- API service
- Worker service

The migration service must run Alembic migrations before API and worker start.

```bash
uv run alembic upgrade head
```

Migrations should run every time Docker Compose starts. Alembic is expected to be idempotent when the schema is already up to date.

## 16.2 Direct UV Mode

The project must also support direct local development with UV.

Expected commands:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run python -m app.worker.main
```

---

# 17. Documentation Requirements

Version 1 must include a `README.md`.

The README should include:

- Project overview
- Requirements
- Docker Compose startup
- Direct UV startup
- Environment variables
- Database migration instructions
- API usage examples with curl
- Testing commands
- Linting commands
- Basic architecture overview

FastAPI-generated OpenAPI documentation must be available.

Expected docs endpoint:

```http
/docs
```

Expected OpenAPI JSON endpoint:

```http
/openapi.json
```

OpenAPI metadata:

```text
title: Audio Transcription API
version: 0.1.0
description: Internal REST API for asynchronous audio transcription using Faster Whisper.
```

---

# 18. Testing Requirements

Version 1 must include:

- Unit tests
- API tests
- Worker tests

The default test suite must mock or fake the transcriber.

Real Faster Whisper transcription is not required in the default test suite.

## 18.1 Expected Test Coverage Areas

Unit tests:

- Job creation service
- Job listing service
- Job retrieval service
- Job processing service
- Validation rules

API tests:

- `POST /api/v1/transcriptions`
- `GET /api/v1/transcriptions/{job_id}`
- `GET /api/v1/transcriptions`
- `GET /health`
- Invalid upload cases

Worker tests:

- Pending job is claimed
- Job becomes processing
- Successful transcription saves text and completes job
- Failed transcription stores error and marks job failed
- Uploaded audio is deleted after processing
- Stuck processing jobs are reset on startup
- Missing audio file marks job as failed

## 18.2 Real Transcription Integration Test

A real Faster Whisper test may exist as an optional/manual integration test.

It must not run as part of the default test command.

Default:

```bash
uv run pytest
```

Optional integration test:

```bash
uv run pytest -m integration
```

## 18.3 Test Database

Tests must not use the real development database.

Use:

- In-memory SQLite for simple unit/API tests
- Temporary file-backed SQLite for worker/integration-style tests

## 18.4 Test Storage

Tests must not use the real development upload directory.

Tests should use temporary directories, such as pytest’s `tmp_path`.

---

# 19. Quality Requirements

## 19.1 Package Manager

The project must use **UV** as the Python package manager.

## 19.2 Python Version

The Docker image should use:

```text
python:3.13-slim
```

If Python 3.13 causes dependency compatibility issues with Faster Whisper or related dependencies, the fallback is:

```text
python:3.12-slim
```

## 19.3 Formatting and Linting

The project must use Ruff for linting and formatting.

Commands:

```bash
uv run ruff check .
uv run ruff format .
```

Python strings should prefer single quotes by default.

Example:

```python
status = 'pending'
message = 'Unsupported audio format.'
```

## 19.4 Type Checking

The codebase should use type hints.

Version 1 does not require mypy or pyright.

## 19.5 Coverage

Version 1 should include coverage reporting but no strict coverage gate.

Commands:

```bash
uv run pytest
uv run pytest --cov=app
```

---

# 20. CI Requirements

The project must include a basic GitHub Actions CI workflow.

The workflow must run on:

- Push to `main`
- Push to `dev`
- Pull requests targeting `main`
- Pull requests targeting `dev`

The CI must run:

```bash
uv run ruff check .
uv run pytest
```

Coverage reporting may also run:

```bash
uv run pytest --cov=app
```

No minimum coverage gate is required in v1.

---

# 21. Branching Expectations

The project uses a basic `main` / `dev` workflow.

```text
dev
- active development branch

main
- stable branch
```

CI must run on both branches for push and pull request events.

---

# 22. Out of Scope for v1

The following features are explicitly out of scope for v1:

- Public API exposure
- Authentication
- User accounts
- Authorization
- OAuth
- API keys
- Synchronous transcription
- Webhooks
- Callbacks
- Cancellation endpoint
- Retry endpoint
- Delete endpoint
- Duplicate upload detection
- Object storage
- Redis queue
- Celery/RQ/Dramatiq
- Multiple workers
- Configurable worker concurrency
- Segment-level timestamps
- Word-level timestamps
- Speaker diarization
- Translation
- Metrics endpoint
- Prometheus
- OpenTelemetry
- Worker health endpoint
- Worker heartbeat table

---

# 23. Functional Acceptance Criteria

The v1 system is functionally complete when:

1. A client can upload a valid audio file through `POST /api/v1/transcriptions`.
2. The API validates extension, size, empty file, and optional language.
3. The API stores the audio file temporarily and creates a pending job.
4. The API returns the full created job representation.
5. A client can fetch a job by ID.
6. A client can list jobs with `limit`/`offset` pagination.
7. A client can filter listed jobs by status.
8. The worker starts, loads Faster Whisper, and polls for pending jobs.
9. The worker processes the oldest pending job first.
10. The worker marks jobs as `processing`, then `completed` or `failed`.
11. Completed jobs contain normalized plain transcription text.
12. Failed jobs contain a clean `error_message`.
13. The worker deletes uploaded audio after both success and failure.
14. The health endpoint checks API, database, and upload directory readiness.
15. Docker Compose can start the migration service, API, and worker.
16. Direct UV startup also works.
17. Tests cover API, service, and worker behavior using a fake transcriber.
18. Ruff linting and pytest run successfully locally and in CI.

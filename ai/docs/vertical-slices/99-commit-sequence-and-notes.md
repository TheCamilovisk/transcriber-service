# Vertical Slices — Commit Sequence, Implementation Notes, and Definition of Done

> Source: `vertical-slice-implementation-plan.md` §5–8

## 5. Suggested Implementation Sequence by Commits

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

## 6. Implementation Notes and Defaults

### 6.1 Error Field

Use only:

```text
error_message
```

Do not add `error_code` in v1.

### 6.2 No Retry Endpoint

Do not implement a retry endpoint in v1.

### 6.3 No Delete Endpoint

Do not implement a delete endpoint in v1.

### 6.4 No Cancel Endpoint

Do not implement cancellation in v1.

### 6.5 Do Not Expose Stored Audio Path in API if Avoidable

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

### 6.6 Keep List Endpoint Lightweight

Do not include `text` in list items.

Use the detail endpoint for full transcription text.

### 6.7 Keep Worker Single-Process

Do not implement multi-worker safety in v1.

The system is explicitly designed for one worker process.

## 7. Definition of Done for v1

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

## 8. Next Step After This Plan

After this implementation plan is approved, the next practical step is to start generating the actual project files in the order of the slices.

The first implementation task would be:

```text
Slice 1 — Project skeleton and development tooling
```

See [Slice 1 — Project Skeleton and Development Tooling](slice-01-project-skeleton.md).

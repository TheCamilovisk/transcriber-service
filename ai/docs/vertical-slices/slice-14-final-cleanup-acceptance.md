# Slice 14 — Final Cleanup and Acceptance Pass

> Source: `vertical-slice-implementation-plan.md` Slice 14

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

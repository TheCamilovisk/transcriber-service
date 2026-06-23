# Functional — Out of Scope and Acceptance Criteria

> Source: `functional-specification.md` §22–23

## 22. Out of Scope for v1

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

## 23. Functional Acceptance Criteria

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

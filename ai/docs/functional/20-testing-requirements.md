# Functional — Testing Requirements

> Source: `functional-specification.md` §18

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

Tests should use temporary directories, such as pytest's `tmp_path`.

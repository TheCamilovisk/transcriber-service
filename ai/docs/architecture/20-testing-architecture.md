# Architecture — Testing Architecture

> Source: `architecture-specification.md` §25

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

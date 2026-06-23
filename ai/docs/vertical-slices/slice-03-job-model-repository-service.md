# Slice 3 — Job Model, Repository, and Basic Service

> Source: `vertical-slice-implementation-plan.md` Slice 3

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

Column types (see [architecture §10.4.1](../architecture/08-database-architecture.md) for the full list):

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

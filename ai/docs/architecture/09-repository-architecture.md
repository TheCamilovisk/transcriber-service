# Architecture — Repository Architecture

> Source: `architecture-specification.md` §11

## 11.1 Repository Class

The repository is a concrete class:

```text
TranscriptionJobRepository
```

Expected location:

```text
app/infrastructure/repositories/transcription_job_repository.py
```

No repository interface/protocol is required in v1.

## 11.2 Repository Responsibilities

Expected repository methods:

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

Repository methods should:

- Query SQLAlchemy models
- Update SQLAlchemy model fields
- Return ORM objects

Repository methods should not:

- Commit transactions
- Own session lifecycle
- Perform file operations
- Call Faster Whisper

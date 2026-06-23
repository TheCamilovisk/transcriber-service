# Architecture — Application Service Architecture

> Source: `architecture-specification.md` §8

## 8.1 Main Service

The application uses a single service class in v1:

```text
TranscriptionService
```

Expected location:

```text
app/application/services/transcription_service.py
```

## 8.2 Service Responsibilities

The service should expose methods similar to:

```python
class TranscriptionService:
    def create_transcription_job(...):
        ...

    def get_transcription_job(...):
        ...

    def list_transcription_jobs(...):
        ...

    def claim_next_pending_job(...):
        ...

    def reset_processing_jobs_to_pending(...):
        ...

    def process_job(...):
        ...
```

## 8.3 Transaction Ownership

The service layer owns database transactions.

Repositories do not call `commit()`.

Routes do not contain transaction logic.

Worker entrypoints do not contain transaction logic beyond opening and closing sessions.

Expected pattern:

```text
Route or worker opens session
  ↓
Service performs use case
  ↓
Repository mutates/query objects
  ↓
Service commits or rolls back
```

## 8.4 File and Database Consistency

For job creation:

1. Generate UUID.
2. Save file.
3. Create database row.
4. Commit transaction.
5. If database creation fails, delete saved file.

This avoids creating a pending job without a corresponding audio file.

For job processing:

1. Mark job processing.
2. Commit.
3. Transcribe.
4. Mark completed or failed.
5. Delete audio file.
6. Commit final state.

The exact implementation may split commits around status transitions to make job state visible to clients.

`process_job()` uses a single session for the whole call, but commits at each phase boundary rather than once at the end: commit immediately after marking `processing`, then commit again after marking the final `completed`/`failed` state. This makes the `processing` transition durably visible to API readers as soon as it happens, without needing to open and close a separate session per phase.

# Slice 4 — Create Transcription Job Endpoint

> Source: `vertical-slice-implementation-plan.md` Slice 4

## Goal

Implement:

```http
POST /api/v1/transcriptions
```

## Scope

This slice creates jobs from uploaded audio files and stores files locally. It does not yet process jobs.

## Tasks

Create storage class:

```text
app/infrastructure/storage/local_audio_storage.py
```

Methods:

```python
class LocalAudioStorage:
    def ensure_upload_dir_exists(self) -> None:
        ...

    def validate_writable(self) -> None:
        ...

    def save_upload(...):
        ...

    def exists(self, path: str) -> bool:
        ...

    def delete(self, path: str) -> None:
        ...
```

Implement upload validation:

- Allowed extensions: `mp3`, `wav`, `m4a`, `ogg`, `webm`
- Max size: 25 MB
- Reject empty file
- Optional language pattern: `^[a-z]{2,5}$`

Create Pydantic response schemas:

```text
app/api/schemas/transcription.py
```

Schemas:

- `TranscriptionJobResponse`
- `TranscriptionJobListItem`
- `TranscriptionJobListResponse`

Implement service method:

```python
def create_transcription_job(
    self,
    *,
    audio_file,
    language: str | None,
) -> TranscriptionJob:
    ...
```

Behavior:

1. Validate extension.
2. Validate size.
3. Validate empty file.
4. Validate language.
5. Generate UUID.
6. Save upload as `{job_id}.{extension}`.
7. Create DB job with status `pending`.
8. Commit.
9. If DB creation fails, delete saved file.

Create route:

```text
app/api/routes/transcriptions.py
```

Endpoint:

```http
POST /api/v1/transcriptions
```

Register router in `app/main.py`.

## Tests

Add API tests:

```text
tests/api/test_create_transcription_job.py
```

Test:

- Upload valid `mp3` creates pending job.
- Response includes full job representation.
- `original_filename` is stored.
- `content_type` is stored if provided.
- `text` is `null`.
- `error_message` is `null`.
- `started_at` is `null`.
- `finished_at` is `null`.
- File is saved with UUID filename.

Validation tests:

- Unsupported extension returns 400.
- Empty file returns 400.
- Oversized file returns 413.
- Invalid language returns validation error.

Use temporary upload directory.

## Acceptance Criteria

This slice is complete when:

1. `POST /api/v1/transcriptions` works.
2. Uploaded files are saved locally.
3. Pending job records are created.
4. Upload validation works.
5. API tests pass.
6. Ruff passes.

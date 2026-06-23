# Functional — Fetch Transcription Job

> Source: `functional-specification.md` §4.2

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

## 4.2.1 Not Found Behavior

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

## 4.2.2 Invalid UUID Behavior

If the job ID is not a valid UUID, FastAPI/Pydantic validation should return:

```http
422 Unprocessable Entity
```

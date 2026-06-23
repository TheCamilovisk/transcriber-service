# Functional — Create Transcription Job

> Source: `functional-specification.md` §4.1

The system must provide an endpoint for creating a transcription job by uploading an audio file.

```http
POST /api/v1/transcriptions
```

Request format:

```http
Content-Type: multipart/form-data
```

Accepted form fields:

| Field      | Required | Type   | Description                     |
| ---------- | -------: | ------ | -------------------------------- |
| `audio`    |      Yes | File   | Audio file to transcribe        |
| `language` |       No | String | Optional ISO-like language code |

Example:

```bash
curl -X POST http://localhost:8000/api/v1/transcriptions \
  -F 'audio=@sample.mp3' \
  -F 'language=pt'
```

## 4.1.1 Upload Behavior

When a valid request is received, the API must:

1. Validate the uploaded file.
2. Validate the optional language value.
3. Generate a UUID for the job.
4. Save the uploaded audio file using the job UUID as filename.
5. Create a database job record with status `pending`.
6. Return the full created job representation.

The upload flow must generate the job UUID before saving the file.

The stored filename must use the job UUID and preserve the original extension.

Example:

```text
Original filename:
meeting-audio.mp3

Job ID:
8f4b2d6e-91b5-4d3a-a36f-78f2f3c1c9a1

Stored path:
uploads/8f4b2d6e-91b5-4d3a-a36f-78f2f3c1c9a1.mp3
```

If file saving fails, no job should be created.

If database job creation fails after the file was saved, the saved file should be deleted.

## 4.1.2 Upload Response

The upload endpoint must return the full created job representation.

Initial values:

| Field           | Initial Value |
| --------------- | ------------- |
| `status`        | `pending`     |
| `text`          | `null`        |
| `error_message` | `null`        |
| `started_at`    | `null`        |
| `finished_at`   | `null`        |

Example response:

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

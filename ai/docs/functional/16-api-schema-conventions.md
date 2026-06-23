# Functional — API Schema Conventions

> Source: `functional-specification.md` §14

## 14.1 JSON Field Naming

API JSON fields must use `snake_case`.

Example:

```json
{
  "original_filename": "meeting.mp3",
  "file_size_bytes": 1234567,
  "error_message": null,
  "created_at": "2026-06-23T14:30:00+00:00"
}
```

No `camelCase` aliases are required in v1.

## 14.2 Response Schemas

The API should use separate response schemas for different response shapes.

Expected schemas:

### `TranscriptionJobResponse`

Full job representation.

Used by:

- `POST /api/v1/transcriptions`
- `GET /api/v1/transcriptions/{job_id}`

Includes `text`.

### `TranscriptionJobListItem`

Summary representation.

Used inside:

- `GET /api/v1/transcriptions`

Does not include `text`.

### `TranscriptionJobListResponse`

Contains:

- `items`
- `limit`
- `offset`
- `total`

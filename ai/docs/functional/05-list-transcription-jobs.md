# Functional — List Transcription Jobs

> Source: `functional-specification.md` §4.3

The system must provide an endpoint for listing transcription jobs.

```http
GET /api/v1/transcriptions
```

The list endpoint must support pagination.

Query parameters:

| Parameter | Required | Default | Maximum | Description               |
| --------- | -------: | ------: | ------: | -------------------------- |
| `limit`   |       No |    `20` |   `100` | Number of items to return |
| `offset`  |       No |     `0` |     N/A | Number of items to skip   |
| `status`  |       No |     N/A |     N/A | Optional status filter    |

Allowed status filter values:

- `pending`
- `processing`
- `completed`
- `failed`

Example:

```http
GET /api/v1/transcriptions?status=failed&limit=20&offset=0
```

## 4.3.0 Pagination and Filter Validation

`limit` must be between `1` and `100` inclusive. `offset` must be `0` or greater. `status`, when provided, must be one of the four allowed status values.

Any of the following must return `422 Unprocessable Entity` via standard FastAPI/Pydantic query parameter validation, the same mechanism used for invalid UUID path parameters:

- `limit` less than `1` or greater than `100`
- `offset` less than `0`
- `status` not one of `pending`, `processing`, `completed`, `failed`

No custom validation code is required for these cases; declaring the query parameters with the appropriate constraints (`Query(ge=1, le=100)`, `Query(ge=0)`, and an enum type for `status`) is sufficient.

## 4.3.1 Ordering

The list endpoint must return newest jobs first.

```text
created_at DESC
```

This differs from worker processing order, which uses oldest pending jobs first.

## 4.3.2 List Response Shape

The list endpoint must return summary items only.

It must not include the full transcription text.

Example response:

```json
{
  "items": [
    {
      "id": "8f4b2d6e-91b5-4d3a-a36f-78f2f3c1c9a1",
      "status": "completed",
      "original_filename": "meeting-audio.mp3",
      "content_type": "audio/mpeg",
      "file_size_bytes": 1234567,
      "language": "pt",
      "error_message": null,
      "created_at": "2026-06-23T14:30:00+00:00",
      "updated_at": "2026-06-23T14:31:20+00:00",
      "started_at": "2026-06-23T14:30:05+00:00",
      "finished_at": "2026-06-23T14:31:20+00:00"
    }
  ],
  "limit": 20,
  "offset": 0,
  "total": 135
}
```

The client must use the single-job endpoint to retrieve the transcription text.

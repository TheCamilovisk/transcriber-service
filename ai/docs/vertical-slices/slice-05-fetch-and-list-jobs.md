# Slice 5 — Fetch and List Transcription Jobs

> Source: `vertical-slice-implementation-plan.md` Slice 5

## Goal

Implement job retrieval and listing endpoints.

## Scope

This slice completes the read side of the API.

## Tasks

Implement route:

```http
GET /api/v1/transcriptions/{job_id}
```

Behavior:

- Validate UUID using path parameter type.
- Return full job representation.
- Return 404 if not found.

Implement route:

```http
GET /api/v1/transcriptions
```

Query parameters:

- `limit`, default `20`, max `100`, min `1` (declared via `Query(ge=1, le=100)`)
- `offset`, default `0`, min `0` (declared via `Query(ge=0)`)
- `status`, optional, typed as `TranscriptionJobStatus` enum so an invalid value is a `422`

Behavior:

- Newest first.
- Optional status filter.
- Return summary items without `text`.
- Include `total`.

Ensure list item schema excludes `text`.

## Tests

Add API tests:

```text
tests/api/test_get_transcription_job.py
tests/api/test_list_transcription_jobs.py
```

Test `GET /api/v1/transcriptions/{job_id}`:

- Existing job returns full job.
- Missing job returns 404.
- Invalid UUID returns 422.

Test `GET /api/v1/transcriptions`:

- Returns `items`, `limit`, `offset`, `total`.
- Default limit is 20.
- Max limit is 100.
- Rejects limit above 100.
- Rejects limit below 1.
- Rejects negative offset.
- Rejects invalid status filter value with 422.
- Supports status filter.
- Orders newest first.
- Does not include `text` in list items.

## Acceptance Criteria

This slice is complete when:

1. Single job retrieval works.
2. Job listing works.
3. Pagination works.
4. Status filtering works.
5. List response excludes `text`.
6. Tests pass.
7. Ruff passes.

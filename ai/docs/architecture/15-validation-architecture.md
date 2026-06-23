# Architecture — Validation Architecture

> Source: `architecture-specification.md` §17

## 17.1 Upload Validation

Upload validation should live primarily in the service layer or a small helper used by the service.

The API route should remain thin.

Validation rules:

- Required `audio` field
- Allowed extensions: `mp3`, `wav`, `m4a`, `ogg`, `webm`
- Max size: 25 MB
- Empty file rejected
- Optional language format

## 17.2 Language Validation

Language validation pattern:

```regex
^[a-z]{2,5}$
```

Invalid language values should be rejected before creating a job.

## 17.3 Error Responses

FastAPI's default error response format is used.

Known application errors may raise `HTTPException` from the API layer after the service reports an error, or the service may raise application exceptions mapped by the route.

For v1, avoid a complex custom exception hierarchy.

## 17.4 Pagination and Filter Validation

`limit`, `offset`, and `status` on the list endpoint are validated declaratively via FastAPI query parameter types, not custom service-layer code:

```python
limit: int = Query(default=20, ge=1, le=100)
offset: int = Query(default=0, ge=0)
status: TranscriptionJobStatus | None = Query(default=None)
```

Out-of-range values or an invalid `status` value produce FastAPI's standard `422` response automatically, the same mechanism already used for invalid UUID path parameters.

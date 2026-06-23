# Slice 6 — Health Check

> Source: `vertical-slice-implementation-plan.md` Slice 6

## Goal

Implement:

```http
GET /health
```

## Scope

This slice adds operational visibility for API, SQLite, and upload directory readiness.

## Tasks

Create route:

```text
app/api/routes/health.py
```

Endpoint:

```http
GET /health
```

Checks:

- Database can execute `SELECT 1`.
- Upload directory exists or can be created.
- Upload directory is writable.

Successful response:

```json
{
  "status": "ok",
  "database": "ok",
  "upload_dir": "ok"
}
```

Failure (503), with a structured body showing which check failed rather than a generic `detail` message:

```json
{
  "status": "error",
  "database": "error",
  "upload_dir": "ok"
}
```

Build this response manually (e.g. `JSONResponse`) instead of raising a plain `HTTPException`, since the failure body must carry the same `database`/`upload_dir` keys as the success body.

Register health router in `app/main.py`.

Add API startup validation:

- Validate database connectivity.
- Ensure upload directory exists.
- Validate upload directory writability.

## Tests

Add:

```text
tests/api/test_health.py
```

Test:

- Health returns `ok` when DB and upload dir are valid.
- Health returns 503 with structured per-check body when upload dir is not writable, if practical to test.

Add startup validation tests if feasible.

## Acceptance Criteria

This slice is complete when:

1. `GET /health` works.
2. Health checks database.
3. Health checks upload directory.
4. API startup validates required resources.
5. Tests pass.
6. Ruff passes.

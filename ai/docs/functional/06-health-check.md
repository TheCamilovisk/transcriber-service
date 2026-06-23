# Functional — Health Check

> Source: `functional-specification.md` §4.4

The system must provide a health check endpoint.

```http
GET /health
```

The health check must verify:

- API process is running
- SQLite database is reachable
- Upload directory exists and is writable

Example successful response:

```json
{
  "status": "ok",
  "database": "ok",
  "upload_dir": "ok"
}
```

If a required dependency is unavailable, the endpoint must return `503 Service Unavailable` with a structured body showing the per-check status, not a generic `detail` message. Each check reports `ok` or `error` independently:

```json
{
  "status": "error",
  "database": "error",
  "upload_dir": "ok"
}
```

```json
{
  "status": "error",
  "database": "ok",
  "upload_dir": "error"
}
```

The top-level `status` is `error` if any individual check fails.

# Architecture — Health Check Architecture

> Source: `architecture-specification.md` §19

The health check route lives in:

```text
app/api/routes/health.py
```

It checks:

- API process is responding
- SQLite database can execute a simple query
- Upload directory exists and is writable

Expected implementation checks:

Database:

```sql
SELECT 1
```

Upload directory:

- Ensure directory exists
- Check write access

Successful response:

```json
{
  "status": "ok",
  "database": "ok",
  "upload_dir": "ok"
}
```

Failure response:

```http
503 Service Unavailable
```

The failure body is structured, not a generic `detail` message, so the client can see which dependency failed:

```json
{
  "status": "error",
  "database": "error",
  "upload_dir": "ok"
}
```

Top-level `status` is `error` if any individual check fails. This means the route builds the response body manually (e.g. via `JSONResponse`) rather than raising a plain `HTTPException`, since the failure shape must carry the same `database`/`upload_dir` keys as the success shape.

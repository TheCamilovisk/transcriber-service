# Functional — API Error Handling

> Source: `functional-specification.md` §13

Version 1 uses FastAPI's default error format.

Known application errors should return simple `detail` messages.

Example:

```json
{
  "detail": "Unsupported audio format."
}
```

## 13.1 Error Behavior Summary

| Case                            |     Status |
| -------------------------------- | ---------: |
| Invalid UUID path parameter     |        422 |
| Job not found                   |        404 |
| Unsupported audio extension     |        400 |
| Empty uploaded file             |        400 |
| Uploaded file exceeds 25 MB     |        413 |
| Invalid language value          | 422 or 400 |
| Invalid `limit`/`offset`        |        422 |
| Invalid `status` filter value   |        422 |
| Health check dependency failure |        503 |

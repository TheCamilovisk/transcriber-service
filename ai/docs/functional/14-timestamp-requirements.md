# Functional — Timestamp Requirements

> Source: `functional-specification.md` §12

All timestamps must be generated as UTC-aware datetimes.

The API must return timestamps as UTC ISO 8601 values.

The implementation may use default Pydantic datetime serialization.

Both forms are acceptable:

```text
2026-06-23T14:30:00Z
2026-06-23T14:30:00+00:00
```

Documentation examples may use `Z`, but the implementation does not need custom serialization only to force the `Z` suffix.

# Architecture — Time Architecture

> Source: `architecture-specification.md` §16

## 16.1 UTC Helper

Use UTC-aware datetimes.

Expected helper:

```text
app/utils/time.py
```

```python
from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)
```

Use this helper consistently for:

- `created_at`
- `updated_at`
- `started_at`
- `finished_at`

## 16.2 Serialization

API responses may rely on Pydantic's default datetime serialization.

The exact output may be:

```text
2026-06-23T14:30:00Z
```

or:

```text
2026-06-23T14:30:00+00:00
```

Both are acceptable if they represent UTC.

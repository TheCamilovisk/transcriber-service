# Slice 2 — Settings, Database Foundation, and Migrations

> Source: `vertical-slice-implementation-plan.md` Slice 2

## Goal

Add configuration, SQLAlchemy database setup, and Alembic migrations.

## Scope

This slice prepares persistence but does not yet implement transcription jobs.

## Tasks

Implement `app/settings.py`.

Expected settings:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = 'sqlite:///./data/app.db'
    upload_dir: str = './data/uploads'
    max_upload_size_mb: int = 25
    worker_poll_interval_seconds: int = 3

    faster_whisper_model_size: str = 'small'
    faster_whisper_device: str = 'cpu'
    faster_whisper_compute_type: str = 'int8'

    api_host: str = '0.0.0.0'
    api_port: int = 8000

    model_config = SettingsConfigDict(env_file='.env')


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Implement database base:

```text
app/infrastructure/database/base.py
```

Implement database session setup:

```text
app/infrastructure/database/session.py
```

Responsibilities:

- Create engine from `settings.database_url`.
- Create `SessionLocal`.
- Expose session dependency/helper.

Add Alembic:

```bash
uv run alembic init alembic
```

Configure Alembic to use the application metadata.

Add `.env.example`.

Active Docker defaults:

```env
DATABASE_URL=sqlite:////app/data/app.db
UPLOAD_DIR=/app/data/uploads

MAX_UPLOAD_SIZE_MB=25
WORKER_POLL_INTERVAL_SECONDS=3

FASTER_WHISPER_MODEL_SIZE=small
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8

API_HOST=0.0.0.0
API_PORT=8000
```

Commented direct UV alternatives:

```env
# DATABASE_URL=sqlite:///./data/app.db
# UPLOAD_DIR=./data/uploads
```

Add `app/utils/time.py`:

```python
from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)
```

## Tests

Add tests for settings:

```text
tests/unit/test_settings.py
```

Test:

- Default `database_url` is `sqlite:///./data/app.db`.
- Default `upload_dir` is `./data/uploads`.
- Environment variables override defaults.

Add tests for UTC helper:

```text
tests/unit/test_time.py
```

Test:

- `utc_now()` returns timezone-aware UTC datetime.

## Acceptance Criteria

This slice is complete when:

1. Settings load from defaults and environment variables.
2. SQLAlchemy session setup exists.
3. Alembic is initialized.
4. `utc_now()` helper exists.
5. Tests pass.
6. Ruff passes.

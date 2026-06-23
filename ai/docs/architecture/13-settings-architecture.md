# Architecture — Settings Architecture

> Source: `architecture-specification.md` §15

## 15.1 Settings Library

The application uses **Pydantic Settings**.

Expected location:

```text
app/settings.py
```

## 15.2 Settings Naming

Environment variables use uppercase names.

Pydantic fields use lowercase names.

Example:

```env
DATABASE_URL=sqlite:///./data/app.db
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE_MB=25
```

```python
database_url: str = 'sqlite:///./data/app.db'
upload_dir: str = './data/uploads'
max_upload_size_mb: int = 25
```

## 15.3 Cached Settings

Use a central cached settings function:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = 'sqlite:///./data/app.db'
    upload_dir: str = './data/uploads'
    max_upload_size_mb: int = 25


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Tests may clear the cache when overriding environment variables.

## 15.4 Expected Settings

```python
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
```

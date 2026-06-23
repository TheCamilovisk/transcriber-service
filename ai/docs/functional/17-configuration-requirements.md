# Functional — Configuration Requirements

> Source: `functional-specification.md` §15

The application must use environment-based configuration.

Settings are loaded through Pydantic Settings.

The repository must include:

```text
.env.example
```

The repository must not commit:

```text
.env
```

## 15.1 Required/Default Settings

Expected settings:

```env
# Docker Compose defaults
DATABASE_URL=sqlite:////app/data/app.db
UPLOAD_DIR=/app/data/uploads

# Direct UV local defaults
# DATABASE_URL=sqlite:///./data/app.db
# UPLOAD_DIR=./data/uploads

MAX_UPLOAD_SIZE_MB=25
WORKER_POLL_INTERVAL_SECONDS=3

FASTER_WHISPER_MODEL_SIZE=small
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8

API_HOST=0.0.0.0
API_PORT=8000
```

The application should default to the local data directory if `DATABASE_URL` is not explicitly provided:

```python
database_url: str = 'sqlite:///./data/app.db'
```

The upload directory should default to:

```python
upload_dir: str = './data/uploads'
```

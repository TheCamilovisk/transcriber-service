# Slice 1 — Project Skeleton and Development Tooling

> Source: `vertical-slice-implementation-plan.md` Slice 1

## Goal

Create the initial project structure and make the repository installable and testable with UV.

## Scope

This slice does not implement the API behavior yet. It establishes the base project, dependency management, formatting, linting, and test framework.

## Tasks

Create the project structure:

```text
transcription-api/
  app/
    __init__.py
    main.py
    settings.py

    api/
      __init__.py
      dependencies.py
      routes/
        __init__.py
      schemas/
        __init__.py

    application/
      __init__.py
      services/
        __init__.py

    domain/
      __init__.py
      enums.py

    infrastructure/
      __init__.py
      database/
        __init__.py
      repositories/
        __init__.py
      storage/
        __init__.py
      transcriber/
        __init__.py

    worker/
      __init__.py
      main.py

    utils/
      __init__.py

  tests/
    unit/
    api/
    worker/
    integration/
```

Initialize UV project:

```bash
uv init
```

Add runtime dependencies:

- `fastapi`
- `uvicorn`
- `sqlalchemy`
- `alembic`
- `pydantic-settings`
- `python-multipart`
- `faster-whisper`

Add dev dependencies:

- `pytest`
- `pytest-asyncio`
- `httpx`
- `ruff`
- `pytest-cov`

Configure Ruff in `pyproject.toml`.

Ruff should format strings with single quotes where possible.

Add a minimal FastAPI app in `app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(
    title='Audio Transcription API',
    version='0.1.0',
    description='Internal REST API for asynchronous audio transcription using Faster Whisper.',
)
```

Add an initial smoke test that imports the app.

## Tests

Add:

```text
tests/api/test_app.py
```

Expected tests:

- App can be imported.
- FastAPI app metadata exists.

Run:

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

## Acceptance Criteria

This slice is complete when:

1. The project installs with UV.
2. The app package imports successfully.
3. pytest runs successfully.
4. Ruff check passes.
5. Ruff format runs successfully.
6. Python code uses single quotes by default.

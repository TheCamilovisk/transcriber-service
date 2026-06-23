# Architecture — Dependency and Code Quality Architecture

> Source: `architecture-specification.md` §23–24

## 23.1 Package Manager

Use **UV**.

## 23.2 Dependency Groups

Use:

- Runtime dependencies
- Dev dependencies

Runtime dependencies:

- `fastapi`
- `uvicorn`
- `sqlalchemy`
- `alembic`
- `pydantic-settings`
- `python-multipart`
- `faster-whisper`

Dev dependencies:

- `pytest`
- `pytest-asyncio`
- `httpx`
- `ruff`
- `pytest-cov`

No mypy or pyright required in v1.

## 24.1 Ruff

Use Ruff for linting and formatting.

Commands:

```bash
uv run ruff check .
uv run ruff format .
```

The Ruff formatter should prefer single quotes where possible.

Python code should use:

```python
status = 'pending'
message = 'Unsupported audio format.'
```

instead of:

```python
status = "pending"
message = "Unsupported audio format."
```

## 24.2 Type Hints

Use type hints throughout the codebase.

Do not enforce mypy or pyright in v1.

## 24.3 No Makefile

No Makefile, Taskfile, or Justfile in v1.

The README documents direct commands.

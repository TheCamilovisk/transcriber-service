# Functional — Quality Requirements

> Source: `functional-specification.md` §19

## 19.1 Package Manager

The project must use **UV** as the Python package manager.

## 19.2 Python Version

The Docker image should use:

```text
python:3.13-slim
```

If Python 3.13 causes dependency compatibility issues with Faster Whisper or related dependencies, the fallback is:

```text
python:3.12-slim
```

## 19.3 Formatting and Linting

The project must use Ruff for linting and formatting.

Commands:

```bash
uv run ruff check .
uv run ruff format .
```

Python strings should prefer single quotes by default.

Example:

```python
status = 'pending'
message = 'Unsupported audio format.'
```

## 19.4 Type Checking

The codebase should use type hints.

Version 1 does not require mypy or pyright.

## 19.5 Coverage

Version 1 should include coverage reporting but no strict coverage gate.

Commands:

```bash
uv run pytest
uv run pytest --cov=app
```

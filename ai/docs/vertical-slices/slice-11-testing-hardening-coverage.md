# Slice 11 — Testing Hardening and Coverage Reporting

> Source: `vertical-slice-implementation-plan.md` Slice 11

## Goal

Improve the default test suite and add coverage reporting.

## Scope

This slice ensures the implementation is well-covered without enforcing a coverage gate.

## Tasks

Add or review tests for all functional requirements.

Test categories:

```text
tests/unit/
tests/api/
tests/worker/
tests/integration/
```

Ensure tests use:

- Temporary SQLite databases
- Temporary upload directories
- Fake transcriber by default

Add `pytest-cov`.

Add command documentation:

```bash
uv run pytest
uv run pytest --cov=app
```

Ensure integration tests are excluded by default.

Configure marker:

```toml
[tool.pytest.ini_options]
markers = [
    'integration: tests that require external runtime dependencies or real Faster Whisper',
]
```

Depending on desired behavior, default test command can ignore integration tests:

```toml
addopts = '-m "not integration"'
```

## Tests

Run:

```bash
uv run pytest
uv run pytest --cov=app
```

## Acceptance Criteria

This slice is complete when:

1. Default pytest run excludes real Faster Whisper integration.
2. Coverage report can be generated.
3. Tests do not use real `data/app.db`.
4. Tests do not use real `data/uploads`.
5. Worker behavior is tested with fake transcriber.
6. Ruff passes.

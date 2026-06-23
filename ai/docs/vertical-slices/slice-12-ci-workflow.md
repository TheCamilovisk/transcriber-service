# Slice 12 — CI Workflow

> Source: `vertical-slice-implementation-plan.md` Slice 12

## Goal

Add GitHub Actions CI for `main` and `dev`.

## Scope

This slice adds automated test and lint checks.

## Tasks

Create:

```text
.github/workflows/ci.yml
```

Triggers:

```yaml
on:
  push:
    branches:
      - main
      - dev
  pull_request:
    branches:
      - main
      - dev
```

Workflow steps:

- Checkout repository
- Install Python 3.13
- Install UV
- Run `uv sync`
- Run Ruff
- Run pytest

Commands:

```bash
uv run ruff check .
uv run pytest
```

Optionally:

```bash
uv run pytest --cov=app
```

No coverage gate.

## Tests

Push branch or run workflow locally if using a local GitHub Actions runner.

## Acceptance Criteria

This slice is complete when:

1. CI runs on push to `main` and `dev`.
2. CI runs on PRs targeting `main` and `dev`.
3. CI executes Ruff.
4. CI executes pytest.
5. CI passes.

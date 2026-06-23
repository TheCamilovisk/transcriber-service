# Architecture — CI and Branching Architecture

> Source: `architecture-specification.md` §26–27

## 26. CI Architecture

Use GitHub Actions.

Workflow location:

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

Required CI commands:

```bash
uv run ruff check .
uv run pytest
```

Optional coverage command:

```bash
uv run pytest --cov=app
```

No minimum coverage gate in v1.

## 27. Branching Architecture

The project uses a basic `main` / `dev` workflow.

```text
dev
- active development branch

main
- stable branch
```

CI runs on push and pull request events for both branches.

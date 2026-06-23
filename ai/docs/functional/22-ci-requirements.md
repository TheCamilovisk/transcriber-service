# Functional — CI and Branching Requirements

> Source: `functional-specification.md` §20–21

## 20. CI Requirements

The project must include a basic GitHub Actions CI workflow.

The workflow must run on:

- Push to `main`
- Push to `dev`
- Pull requests targeting `main`
- Pull requests targeting `dev`

The CI must run:

```bash
uv run ruff check .
uv run pytest
```

Coverage reporting may also run:

```bash
uv run pytest --cov=app
```

No minimum coverage gate is required in v1.

## 21. Branching Expectations

The project uses a basic `main` / `dev` workflow.

```text
dev
- active development branch

main
- stable branch
```

CI must run on both branches for push and pull request events.

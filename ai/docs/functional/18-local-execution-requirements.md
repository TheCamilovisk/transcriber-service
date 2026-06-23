# Functional — Local Execution Requirements

> Source: `functional-specification.md` §16

The project must support two local execution modes.

## 16.1 Docker Compose Mode

Docker Compose is the preferred easy startup path.

First-time setup:

```bash
cp .env.example .env
docker compose up --build
```

Regular startup after `.env` exists:

```bash
docker compose up --build
```

Docker Compose must run:

- Migration service
- API service
- Worker service

The migration service must run Alembic migrations before API and worker start.

```bash
uv run alembic upgrade head
```

Migrations should run every time Docker Compose starts. Alembic is expected to be idempotent when the schema is already up to date.

## 16.2 Direct UV Mode

The project must also support direct local development with UV.

Expected commands:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run python -m app.worker.main
```

# Slice 13 — README and Usage Documentation

> Source: `vertical-slice-implementation-plan.md` Slice 13

## Goal

Document how to run, use, test, and understand the project.

## Scope

This slice creates practical documentation for local/internal development and usage.

## Tasks

Create or complete `README.md`.

Sections:

- Project overview
- Features
- Requirements
- Environment configuration
- Docker Compose startup
- Direct UV startup
- API endpoints
- curl examples
- Worker behavior
- Database migrations
- Testing
- Linting and formatting
- Optional Faster Whisper integration test
- Troubleshooting
- Architecture overview

Document first-time Docker startup:

```bash
cp .env.example .env
docker compose up --build
```

Document regular Docker startup:

```bash
docker compose up --build
```

Document direct UV startup:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run python -m app.worker.main
```

Document testing:

```bash
uv run pytest
uv run pytest --cov=app
uv run pytest -m integration
```

Document linting:

```bash
uv run ruff check .
uv run ruff format .
```

Document API examples.

Create job:

```bash
curl -X POST http://localhost:8000/api/v1/transcriptions \
  -F 'audio=@sample.mp3' \
  -F 'language=pt'
```

Fetch job:

```bash
curl http://localhost:8000/api/v1/transcriptions/{job_id}
```

List jobs:

```bash
curl 'http://localhost:8000/api/v1/transcriptions?limit=20&offset=0'
```

Filter failed jobs:

```bash
curl 'http://localhost:8000/api/v1/transcriptions?status=failed'
```

Health:

```bash
curl http://localhost:8000/health
```

Document OpenAPI docs:

```text
/docs
/openapi.json
```

## Tests

Manual documentation review.

Verify commands are accurate.

## Acceptance Criteria

This slice is complete when:

1. README explains setup clearly.
2. Docker and direct UV commands are documented.
3. API examples are documented.
4. Test and Ruff commands are documented.
5. Worker behavior is explained.
6. Known limitations are documented.

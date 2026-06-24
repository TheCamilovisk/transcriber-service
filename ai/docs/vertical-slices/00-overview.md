# Vertical Slices — Overview

> Source: `vertical-slice-implementation-plan.md` §1–4

## 1. Purpose

This document defines the implementation plan for the **Audio Transcription API** using vertical slices.

A vertical slice is a small end-to-end increment that cuts through the necessary layers of the system:

```text
API / worker entrypoint
→ application service
→ repository / storage / transcriber
→ database / filesystem
→ tests / documentation
```

The goal is to avoid building isolated layers that cannot run. Each slice should produce a working, testable improvement.

## 2. Implementation Principles

The implementation should follow these principles:

- Build in small vertical increments.
- Keep the system runnable after each slice.
- Add tests with each slice.
- Avoid implementing unused abstractions.
- Prefer simple concrete classes.
- Keep API routes thin.
- Keep transaction ownership in the service layer.
- Use single quotes in Python code by default.
- Use Ruff for formatting and linting.
- Use pytest for tests.

## 3. Target Stack

The project uses:

- Python 3.13
- UV
- FastAPI
- SQLite
- SQLAlchemy 2.0
- Alembic
- Pydantic Settings
- Faster Whisper
- Local filesystem storage
- Docker Compose
- Pytest
- Ruff
- GitHub Actions

Fallback if Python 3.13 causes Faster Whisper dependency issues:

- Python 3.12

## 4. Slice Overview

Recommended implementation order:

1. [Project skeleton and development tooling](slice-01-project-skeleton.md)
2. [Settings, database foundation, and migrations](slice-02-settings-database-migrations.md)
3. [Job model, repository, and basic service](slice-03-job-model-repository-service.md)
4. [Create transcription job endpoint](slice-04-create-transcription-job-endpoint.md)
5. [Fetch and list transcription jobs](slice-05-fetch-and-list-jobs.md)
6. [Health check](slice-06-health-check.md)
7. [Worker polling loop without real transcription](slice-07-worker-polling-loop.md)
8. [Job processing with fake transcriber](slice-08-job-processing-fake-transcriber.md)
9. [Faster Whisper integration](slice-09-faster-whisper-integration.md)
10. [Docker Compose local runtime](slice-10-docker-compose-runtime.md)
11. [Testing hardening and coverage reporting](slice-11-testing-hardening-coverage.md)
12. [CI workflow](slice-12-ci-workflow.md)
13. [README and usage documentation](slice-13-readme-documentation.md)
14. [Final cleanup and acceptance pass](slice-14-final-cleanup-acceptance.md)
15. [GPU-enabled Faster Whisper inference](slice-15-gpu-inference.md)

Each slice includes:

- Goal
- Scope
- Tasks
- Tests
- Acceptance criteria

See also [Commit sequence and implementation notes](99-commit-sequence-and-notes.md).

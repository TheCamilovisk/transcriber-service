# Architecture — API Architecture

> Source: `architecture-specification.md` §7

## 7.1 API Framework

The API uses **FastAPI**.

OpenAPI metadata:

```text
title: Audio Transcription API
version: 0.1.0
description: Internal REST API for asynchronous audio transcription using Faster Whisper.
```

## 7.2 API Routes

Application endpoints use the `/api/v1` prefix.

Health endpoint remains unversioned.

```http
POST /api/v1/transcriptions
GET /api/v1/transcriptions/{job_id}
GET /api/v1/transcriptions
GET /health
```

## 7.3 Route Modules

Expected route modules:

```text
app/api/routes/transcriptions.py
app/api/routes/health.py
```

`transcriptions.py` contains:

- Create transcription job endpoint
- Get transcription job endpoint
- List transcription jobs endpoint

`health.py` contains:

- Health check endpoint

## 7.4 API Schemas

Schemas live in:

```text
app/api/schemas/transcription.py
```

Expected schemas:

- `TranscriptionJobResponse`
- `TranscriptionJobListItem`
- `TranscriptionJobListResponse`

The API should not return raw SQLAlchemy models directly.

The API uses `snake_case` JSON fields.

## 7.5 Dependency Injection

API dependencies live in:

```text
app/api/dependencies.py
```

Expected dependencies:

- `get_db_session()`
- `get_transcription_service()`

The route layer receives dependencies and delegates use cases to `TranscriptionService`.

# Functional — Documentation Requirements

> Source: `functional-specification.md` §17

Version 1 must include a `README.md`.

The README should include:

- Project overview
- Requirements
- Docker Compose startup
- Direct UV startup
- Environment variables
- Database migration instructions
- API usage examples with curl
- Testing commands
- Linting commands
- Basic architecture overview

FastAPI-generated OpenAPI documentation must be available.

Expected docs endpoint:

```http
/docs
```

Expected OpenAPI JSON endpoint:

```http
/openapi.json
```

OpenAPI metadata:

```text
title: Audio Transcription API
version: 0.1.0
description: Internal REST API for asynchronous audio transcription using Faster Whisper.
```

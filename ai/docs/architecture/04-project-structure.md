# Architecture — Proposed Project Structure

> Source: `architecture-specification.md` §6

```text
transcription-api/
  app/
    __init__.py

    main.py
    settings.py

    api/
      __init__.py
      dependencies.py
      routes/
        __init__.py
        health.py
        transcriptions.py
      schemas/
        __init__.py
        transcription.py

    application/
      __init__.py
      services/
        __init__.py
        transcription_service.py

    domain/
      __init__.py
      enums.py

    infrastructure/
      __init__.py

      database/
        __init__.py
        base.py
        session.py
        models.py

      repositories/
        __init__.py
        transcription_job_repository.py

      storage/
        __init__.py
        local_audio_storage.py

      transcriber/
        __init__.py
        faster_whisper_transcriber.py

    worker/
      __init__.py
      main.py

    utils/
      __init__.py
      time.py
      logging.py

  alembic/
    versions/

  tests/
    unit/
    api/
    worker/
    integration/

  .github/
    workflows/
      ci.yml

  .env.example
  .dockerignore
  docker-compose.yml
  Dockerfile
  alembic.ini
  pyproject.toml
  uv.lock
  README.md
```

## 6.1 Notes on Structure

The API and worker live in the same repository and share the same codebase.

The API entrypoint is:

```text
app/main.py
```

The worker entrypoint is:

```text
app/worker/main.py
```

The database model is kept under infrastructure because it is a persistence concern.

The only domain-level concept needed in v1 is the job status enum.

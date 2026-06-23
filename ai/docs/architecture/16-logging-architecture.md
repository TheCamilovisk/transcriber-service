# Architecture — Logging Architecture

> Source: `architecture-specification.md` §18

## 18.1 Logging Style

Use basic Python logging.

No structured JSON logging in v1.

Logs should be readable as plain text.

## 18.2 Log Locations

Logging helpers may live in:

```text
app/utils/logging.py
```

or be configured directly in entrypoints for v1.

## 18.3 Required Job Context

Any log related to a transcription job should include:

```text
job_id=...
```

Worker logs should cover:

- Startup
- Model loading
- Polling
- Job claiming
- Transcription start
- Transcription completion
- Transcription failure
- File deletion
- Shutdown

# Architecture — Worker Architecture

> Source: `architecture-specification.md` §14

## 14.1 Worker Entrypoint

Worker entrypoint:

```text
app/worker/main.py
```

Run directly:

```bash
uv run python -m app.worker.main
```

Docker Compose command:

```bash
uv run python -m app.worker.main
```

## 14.2 Worker Lifecycle

Worker startup sequence:

1. Load settings.
2. Configure logging.
3. Create/validate upload directory.
4. Validate database connectivity.
5. Load Faster Whisper model.
6. Reset processing jobs to pending.
7. Enter polling loop.

## 14.3 Polling Loop

Conceptual loop:

```python
while not shutdown_requested:
    job = service.claim_next_pending_job()

    if job is None:
        sleep(settings.worker_poll_interval_seconds)
        continue

    service.process_job(job.id)
```

## 14.4 Single-Worker Assumption

The worker design assumes:

- One worker process
- One job at a time

Because of this, SQLite polling remains simple.

If future versions need multiple workers, the architecture should be revisited and probably move to:

- Redis + RQ/Dramatiq
- Or PostgreSQL with safer row locking

## 14.5 Startup Recovery

On startup, the worker calls:

```text
reset_processing_jobs_to_pending()
```

This resets jobs stuck in `processing` after a crash.

## 14.6 Graceful Shutdown

The worker handles shutdown signals using best effort:

- If idle, stop
- If processing, try to finish current job
- If force-killed, startup recovery handles stuck processing jobs

Mechanism: register handlers for `SIGTERM` and `SIGINT` that set a `shutdown_requested` flag. The polling loop checks this flag between poll iterations and before claiming the next job. There is no timeout applied to an in-flight job — the current `process_job()` call is allowed to run to completion. `SIGKILL` bypasses the handler entirely; the next worker startup's recovery step (§14.5) resets any job left stuck in `processing`.

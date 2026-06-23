# Slice 7 — Worker Polling Loop Without Real Transcription

> Source: `vertical-slice-implementation-plan.md` Slice 7

## Goal

Create the worker process and polling loop without running Faster Whisper yet.

## Scope

This slice makes the worker executable and able to claim jobs.

It does not process jobs fully yet.

## Tasks

Implement worker entrypoint:

```text
app/worker/main.py
```

Startup sequence:

1. Load settings.
2. Configure logging.
3. Validate database connectivity.
4. Ensure upload directory exists/writable.
5. Reset processing jobs to pending.
6. Enter polling loop.

At this slice, use a placeholder processing behavior or stop after claiming in tests.

Implement service methods:

```python
def claim_next_pending_job(self):
    ...

def reset_processing_jobs_to_pending(self):
    ...
```

Claim behavior:

- Select oldest pending job.
- Mark `processing`.
- Set `started_at`.
- Set `updated_at`.
- Commit.

Reset behavior:

- Find `processing` jobs.
- Set status to `pending`.
- Clear `started_at`.
- Set `updated_at`.

Implement graceful shutdown: register `SIGTERM`/`SIGINT` handlers that set a `shutdown_requested` flag, checked between poll iterations and before claiming the next job. No timeout is applied to an in-flight job. `SIGKILL` bypasses this; startup recovery (already implemented above) handles any job left stuck in `processing`.

Add worker logging.

## Tests

Add:

```text
tests/worker/test_worker_claiming.py
```

Test:

- Worker claims oldest pending job.
- Claimed job becomes `processing`.
- `started_at` is set.
- `updated_at` is set.
- `processing` jobs reset to `pending` on startup.
- Reset jobs have `started_at` cleared.

Avoid infinite loops in tests by testing service methods, not the full endless worker loop.

## Acceptance Criteria

This slice is complete when:

1. Worker entrypoint exists.
2. Worker can be started.
3. Worker startup recovery exists.
4. Pending job claiming works.
5. Tests pass.
6. Ruff passes.

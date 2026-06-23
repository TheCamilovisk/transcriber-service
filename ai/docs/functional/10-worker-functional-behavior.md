# Functional — Worker Functional Behavior

> Source: `functional-specification.md` §8

The worker is a separate process from the API.

The worker uses SQLite as a simple job queue by polling for pending jobs.

There is no Redis, Celery, RQ, or Dramatiq in v1.

## 8.1 Worker Polling

The worker must poll the database for pending jobs.

The polling interval must be configurable.

Default:

```env
WORKER_POLL_INTERVAL_SECONDS=3
```

When idle, the worker waits for the configured interval before checking again.

## 8.2 Worker Concurrency

Version 1 supports:

- One worker process
- One job processed at a time

No configurable concurrency is required in v1.

Multiple worker processes are not officially supported in v1.

## 8.3 Job Claiming Order

The worker must process the oldest pending job first.

Ordering:

```text
created_at ASC
```

Conceptual query:

```sql
SELECT *
FROM transcription_jobs
WHERE status = 'pending'
ORDER BY created_at ASC
LIMIT 1;
```

After claiming a job, the worker must:

1. Mark the job as `processing`.
2. Set `started_at`.
3. Set `updated_at`.
4. Commit the change.
5. Run transcription.

## 8.4 Worker Startup Recovery

When the worker starts, it must reset jobs stuck in `processing` back to `pending`.

This handles cases where the worker crashed while processing a job.

If a reset job's audio file no longer exists when processing is attempted, the worker must mark the job as failed.

Error message:

```text
Audio file is no longer available.
```

## 8.5 Missing Audio File

If the worker tries to process a job but the stored audio file does not exist, it must:

- Mark the job as failed
- Set `finished_at`
- Set `updated_at`
- Store a clean `error_message`
- Not delete the job record
- Not retry forever

Example:

```json
{
  "status": "failed",
  "text": null,
  "error_message": "Audio file is no longer available."
}
```

## 8.6 Worker Shutdown

Worker shutdown should be best-effort.

If idle:

- Stop immediately.

If processing:

- Try to finish the current job before stopping.

If force-killed:

- Startup recovery resets stuck `processing` jobs to `pending`.

Mechanism: the worker registers handlers for `SIGTERM` and `SIGINT` that set a `shutdown_requested` flag. The flag is checked between poll iterations and before claiming the next job. There is no timeout on an in-flight job — the worker lets the current job finish naturally before exiting. A force-kill (`SIGKILL`) bypasses this entirely and relies on startup recovery on the next launch.

## 8.7 Worker Logs

The worker should log important lifecycle events:

- Worker starting
- Loading Faster Whisper model
- Faster Whisper model loaded
- Reset stuck processing jobs to pending
- Waiting for jobs
- Claimed job `job_id=...`
- Started transcription `job_id=...`
- Completed job `job_id=...`
- Failed job `job_id=...`
- Worker shutdown requested

Logs related to a job must include `job_id`.

# Functional — Job Lifecycle

> Source: `functional-specification.md` §7

## 7.1 Supported Statuses

Version 1 supports exactly these statuses:

- `pending`
- `processing`
- `completed`
- `failed`

Meaning:

| Status       | Meaning                                          |
| ------------ | ------------------------------------------------ |
| `pending`    | Job was created and is waiting for the worker    |
| `processing` | Worker claimed the job and started transcription |
| `completed`  | Transcription finished successfully              |
| `failed`     | Transcription failed                             |

Version 1 does not support:

- `cancelled`
- `retrying`
- `expired`

## 7.2 Status Transitions

Expected normal transition:

```text
pending → processing → completed
```

Expected failure transition:

```text
pending → processing → failed
```

A job may also return from `processing` to `pending` during worker startup recovery if the worker previously crashed.

```text
processing → pending
```

This is allowed only as a recovery behavior.

## 7.3 Retry Behavior

Version 1 has no automatic retry mechanism.

If transcription fails during normal processing, the job becomes `failed`.

The system does not expose retry endpoints in v1.

A worker crash is handled separately by startup recovery, where stuck `processing` jobs are reset to `pending`.

## 7.4 Cancellation

Version 1 does not support job cancellation.

There is no cancel endpoint.

## 7.5 Deletion

Version 1 does not support deleting job records through the API.

There is no delete endpoint.

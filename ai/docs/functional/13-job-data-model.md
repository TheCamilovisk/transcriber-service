# Functional — Job Data Model

> Source: `functional-specification.md` §11

A transcription job must store the following fields:

- `id`
- `status`
- `original_filename`
- `stored_audio_path`
- `content_type`
- `file_size_bytes`
- `language`
- `text`
- `error_message`
- `created_at`
- `updated_at`
- `started_at`
- `finished_at`

Field meanings:

| Field               | Meaning                                                  |
| ------------------- | --------------------------------------------------------- |
| `id`                | UUID job identifier                                       |
| `status`            | `pending`, `processing`, `completed`, or `failed`        |
| `original_filename` | Original filename sent by the client                     |
| `stored_audio_path` | Temporary local path used by the worker before deletion  |
| `content_type`      | Uploaded file MIME/content type, when provided           |
| `file_size_bytes`   | Uploaded file size                                        |
| `language`          | Requested language or detected language                  |
| `text`              | Final transcription text when completed                  |
| `error_message`     | Clean failure message when failed                         |
| `created_at`        | When the job was created                                  |
| `updated_at`        | When the job was last updated                             |
| `started_at`        | When the worker started processing                        |
| `finished_at`       | When the job reached `completed` or `failed`              |

After processing finishes, the original audio file is deleted. The `stored_audio_path` may remain as historical metadata, but the file itself should no longer exist.

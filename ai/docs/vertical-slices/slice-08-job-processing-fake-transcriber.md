# Slice 8 — Job Processing with Fake Transcriber

> Source: `vertical-slice-implementation-plan.md` Slice 8

## Goal

Implement the full job processing flow using a fake transcriber.

## Scope

This slice completes worker behavior without Faster Whisper.

The worker can process jobs end-to-end with a fake transcriber in tests.

## Tasks

Create transcriber result dataclass:

```text
app/infrastructure/transcriber/faster_whisper_transcriber.py
```

or a shared local module if preferred.

```python
from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    text: str
    language: str | None
```

Create test fake transcribers:

```text
tests/fakes.py
```

Example:

```python
class FakeTranscriber:
    def transcribe(self, audio_path: str, language: str | None = None):
        return TranscriptionResult(
            text='Fake transcription.',
            language=language or 'en',
        )
```

Implement service method:

```python
def process_job(self, job_id: str, transcriber) -> None:
    ...
```

Behavior:

1. Fetch job.
2. Check stored audio path exists.
3. If missing, mark failed.
4. Call `transcriber.transcribe(path, language=job.language)`.
5. Store text.
6. If `job.language` was null, store transcriber result language.
7. Mark completed.
8. Set `finished_at`.
9. Set `updated_at`.
10. Delete uploaded audio file.

Failure behavior:

1. Log full exception.
2. Store clean `error_message`.
3. Mark failed.
4. Set `finished_at`.
5. Set `updated_at`.
6. Delete uploaded audio if it exists.

Clean transcription error message:

```text
Could not transcribe the audio file.
```

Missing audio error message:

```text
Audio file is no longer available.
```

Empty transcription text:

- Mark completed.
- Store `text = ''`.

## Tests

Add:

```text
tests/worker/test_process_job.py
```

Test success:

- Processing job becomes completed.
- Text is stored.
- Language remains provided language if originally set.
- Language is stored from result if originally null.
- `finished_at` is set.
- Audio file is deleted.

Test failure:

- Transcriber exception marks failed.
- Clean `error_message` is stored.
- `text` remains null.
- `finished_at` is set.
- Audio file is deleted.

Test missing audio:

- Missing file marks failed.
- `error_message` is `Audio file is no longer available.`
- No infinite retry.

Test empty result:

- Empty text marks completed.
- `text` is `''`.

## Acceptance Criteria

This slice is complete when:

1. `process_job` works with fake transcriber.
2. Successful jobs become `completed`.
3. Failed jobs become `failed`.
4. Missing audio is handled.
5. Audio cleanup happens after success and failure.
6. Tests pass.
7. Ruff passes.

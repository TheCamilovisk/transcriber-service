# Functional — Transcription Behavior

> Source: `functional-specification.md` §9

## 9.1 Engine

Version 1 uses **Faster Whisper**.

The worker runs transcription locally.

No external transcription API is used.

## 9.2 Model Loading

The worker must load the Faster Whisper model once at startup.

The model must be reused for all jobs processed by that worker.

If the model cannot be loaded, the worker must exit with an error and must not enter the polling loop.

The worker must not mark jobs as failed due to model startup/configuration failure.

## 9.3 Model Configuration

The following settings must be configurable:

- `FASTER_WHISPER_MODEL_SIZE`
- `FASTER_WHISPER_DEVICE`
- `FASTER_WHISPER_COMPUTE_TYPE`

Defaults (Docker, GPU host with NVIDIA Container Toolkit configured):

```env
FASTER_WHISPER_MODEL_SIZE=small
FASTER_WHISPER_DEVICE=cuda
FASTER_WHISPER_COMPUTE_TYPE=float16
```

CPU fallback (no GPU available):

```env
FASTER_WHISPER_MODEL_SIZE=small
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8
```

Other supported model sizes:

```env
FASTER_WHISPER_MODEL_SIZE=base
FASTER_WHISPER_MODEL_SIZE=medium
```

## 9.4 Transcription Result

The completed job must contain:

- Plain transcription text
- Basic metadata

Version 1 does not expose:

- Segment-level timestamps
- Word-level timestamps
- Speaker diarization
- Translation

## 9.5 Text Assembly

Faster Whisper returns segments internally.

Version 1 must assemble the final text as one normalized plain-text result.

The system must:

- Join segment texts
- Strip leading/trailing whitespace
- Collapse repeated whitespace
- Store the normalized text in the job record

Example:

```text
Raw segments:
- " Hello,"
- "   this is a test."
- " Thank you."

Stored text:
"Hello, this is a test. Thank you."
```

## 9.6 Empty Transcription Result

If Faster Whisper completes successfully but produces no text, the job must still be marked as `completed`.

The `text` field should be an empty string.

Example:

```json
{
  "status": "completed",
  "text": "",
  "error_message": null
}
```

Silent or unintelligible audio is not treated as a system failure.

## 9.7 Transcription Failure

If Faster Whisper fails while processing a job, the worker must:

- Mark the job as failed
- Set a clean client-facing `error_message`
- Set `finished_at`
- Set `updated_at`
- Log the full exception and stack trace
- Delete the uploaded audio file after failure handling

The API must not expose internal stack traces.

Client-facing error example:

```json
{
  "status": "failed",
  "text": null,
  "error_message": "Could not transcribe the audio file."
}
```

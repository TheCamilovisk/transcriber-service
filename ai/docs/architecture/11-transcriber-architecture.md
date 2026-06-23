# Architecture — Transcriber Architecture

> Source: `architecture-specification.md` §13

## 13.1 Transcriber Implementation

The transcriber is a concrete class:

```text
FasterWhisperTranscriber
```

Expected location:

```text
app/infrastructure/transcriber/faster_whisper_transcriber.py
```

No generic transcriber interface is required in v1.

## 13.2 Model Lifecycle

The worker creates one `FasterWhisperTranscriber` instance at startup.

The Faster Whisper model loads during transcriber initialization.

If loading fails:

- Worker exits with an error
- Worker does not start polling
- Jobs are not marked failed

## 13.3 Transcriber Method Shape

Expected shape:

```python
from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    text: str
    language: str | None


class FasterWhisperTranscriber:
    def __init__(
        self,
        model_size: str,
        device: str,
        compute_type: str,
    ) -> None:
        ...

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
    ) -> TranscriptionResult:
        ...
```

## 13.4 Text Normalization

The transcriber should:

- Collect segment texts
- Join them
- Strip leading/trailing whitespace
- Collapse repeated whitespace

The service stores only the normalized plain text.

## 13.5 Language Behavior

If the job already has `language`, the service passes it to the transcriber and keeps it.

If the job language is `null`, the transcriber result language is stored back into the job.

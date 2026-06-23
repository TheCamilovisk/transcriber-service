# Slice 9 — Faster Whisper Integration

> Source: `vertical-slice-implementation-plan.md` Slice 9

## Goal

Implement the real `FasterWhisperTranscriber`.

## Scope

This slice connects the worker to Faster Whisper, but default tests still use fake transcribers.

## Tasks

Implement:

```text
app/infrastructure/transcriber/faster_whisper_transcriber.py
```

Class:

```python
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

Behavior:

- Load model at initialization.
- Call `model.transcribe(audio_path, language=language)`.
- Collect `segment.text` values.
- Normalize whitespace.
- Return text and language.

Text normalization:

- Join segment texts.
- Strip.
- Collapse repeated whitespace.

Update worker startup:

- Create `FasterWhisperTranscriber` using settings.
- Exit if model loading fails.
- Pass transcriber to processing loop.

Add optional manual integration test marker:

```python
@pytest.mark.integration
```

Configure pytest markers in `pyproject.toml`.

Optional integration test should require a tiny audio fixture.

Do not run integration test by default.

## Tests

Default tests:

- Unit test text normalization with fake segment values.
- Verify worker can receive transcriber dependency.

Optional integration test:

```bash
uv run pytest -m integration
```

Test:

- Tiny audio file can be transcribed by real Faster Whisper.

## Acceptance Criteria

This slice is complete when:

1. `FasterWhisperTranscriber` loads model from configured settings.
2. Worker uses `FasterWhisperTranscriber` in real runtime.
3. Default tests do not require model download.
4. Optional integration marker exists.
5. Tests pass.
6. Ruff passes.

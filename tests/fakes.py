from __future__ import annotations

from app.infrastructure.transcriber.faster_whisper_transcriber import (
    TranscriptionResult,
)


class FakeTranscriber:
    def transcribe(
        self, audio_path: str, language: str | None = None
    ) -> TranscriptionResult:
        return TranscriptionResult(
            text='Fake transcription.',
            language=language or 'en',
        )


class FakeTranscriberAlwaysFails:
    def transcribe(
        self, audio_path: str, language: str | None = None
    ) -> TranscriptionResult:
        msg = 'Transcriber failure'
        raise RuntimeError(msg)


class FakeTranscriberEmptyResult:
    def transcribe(
        self, audio_path: str, language: str | None = None
    ) -> TranscriptionResult:
        return TranscriptionResult(text='', language=language or 'en')

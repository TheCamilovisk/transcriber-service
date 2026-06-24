from __future__ import annotations

import re
from dataclasses import dataclass

from faster_whisper import WhisperModel


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
        self._model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
    ) -> TranscriptionResult:
        segments, info = self._model.transcribe(audio_path, language=language)
        text = ''.join(segment.text for segment in segments)
        text = re.sub(r'\s+', ' ', text.strip())
        return TranscriptionResult(text=text, language=info.language)

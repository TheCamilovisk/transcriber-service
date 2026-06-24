"""Integration test for FasterWhisperTranscriber with a real model.

This test requires downloading the Faster Whisper model and is excluded
from the default test suite. Run with:

    uv run pytest -m integration
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.infrastructure.transcriber.faster_whisper_transcriber import (
    FasterWhisperTranscriber,
    TranscriptionResult,
)


@pytest.fixture(scope='module')
def tiny_audio_file(tmp_path_factory) -> Path:
    """Generate a tiny WAV file with silence using ffmpeg."""
    audio_path = tmp_path_factory.mktemp('audio') / 'silence.wav'
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'anullsrc=r=16000:cl=mono',
            '-t',
            '1',
            '-acodec',
            'pcm_s16le',
            str(audio_path),
        ],
        check=True,
        capture_output=True,
    )
    return audio_path


@pytest.mark.integration
class TestFasterWhisperTranscriberReal:
    """Integration tests that require a real Faster Whisper model download."""

    def test_transcribe_tiny_audio(self, tiny_audio_file: Path) -> None:
        """Verify that a real model can transcribe a tiny audio file."""
        transcriber = FasterWhisperTranscriber(
            model_size='tiny',
            device='cpu',
            compute_type='int8',
        )
        result = transcriber.transcribe(str(tiny_audio_file))

        assert isinstance(result, TranscriptionResult)
        assert isinstance(result.text, str)
        assert isinstance(result.language, str)
        # Even silence should produce a language detection.
        assert len(result.language) >= 2

    def test_transcribe_with_language_hint(self, tiny_audio_file: Path) -> None:
        """Verify passing an explicit language to transcribe."""
        transcriber = FasterWhisperTranscriber(
            model_size='tiny',
            device='cpu',
            compute_type='int8',
        )
        result = transcriber.transcribe(str(tiny_audio_file), language='en')

        assert isinstance(result, TranscriptionResult)
        assert result.language == 'en'

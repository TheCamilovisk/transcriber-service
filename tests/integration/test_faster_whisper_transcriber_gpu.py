"""GPU integration test for FasterWhisperTranscriber with a real model.

Requires a real Faster Whisper model download and a CUDA-capable GPU. Skipped
automatically when no GPU is available (e.g. CI, CPU-only dev machines). Run
with:

    uv run pytest -m integration
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import ctranslate2
import pytest

from app.infrastructure.transcriber.faster_whisper_transcriber import (
    FasterWhisperTranscriber,
    TranscriptionResult,
)

no_gpu = ctranslate2.get_cuda_device_count() == 0


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
@pytest.mark.skipif(no_gpu, reason='No CUDA-capable GPU available.')
class TestFasterWhisperTranscriberGpu:
    """Integration tests that require a real Faster Whisper model on GPU."""

    def test_transcribe_tiny_audio_on_gpu(self, tiny_audio_file: Path) -> None:
        """Verify that a real model can transcribe a tiny audio file on GPU."""
        transcriber = FasterWhisperTranscriber(
            model_size='tiny',
            device='cuda',
            compute_type='float16',
        )
        result = transcriber.transcribe(str(tiny_audio_file))

        assert isinstance(result, TranscriptionResult)
        assert isinstance(result.text, str)
        assert isinstance(result.language, str)
        assert len(result.language) >= 2

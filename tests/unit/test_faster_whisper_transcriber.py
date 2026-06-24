"""Tests for FasterWhisperTranscriber text normalization."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.transcriber.faster_whisper_transcriber import (
    FasterWhisperTranscriber,
    TranscriptionResult,
)


def _make_mock_segment(text: str) -> MagicMock:
    segment = MagicMock()
    segment.text = text
    return segment


def _make_mock_info(language: str = 'en') -> MagicMock:
    info = MagicMock()
    info.language = language
    return info


class TestTextNormalization:
    @pytest.mark.parametrize(
        ('segment_texts', 'language', 'expected_text', 'expected_language'),
        [
            # Basic case: single segment, already clean.
            (
                ['Hello world.'],
                'en',
                'Hello world.',
                'en',
            ),
            # Multiple segments joined.
            (
                ['Hello ', 'world.', ' How are you?'],
                'en',
                'Hello world. How are you?',
                'en',
            ),
            # Leading and trailing whitespace stripped.
            (
                ['  Hello world.  '],
                'en',
                'Hello world.',
                'en',
            ),
            # Internal repeated whitespace collapsed.
            (
                ['Hello    world.'],
                'en',
                'Hello world.',
                'en',
            ),
            # Multiple segments with mixed whitespace.
            (
                ['  Hello  ', '  world!  ', '  How are  you?  '],
                'en',
                'Hello world! How are you?',
                'en',
            ),
            # Tabs and newlines collapsed.
            (
                ['Hello\t\nworld.\n\nHow are you?'],
                'en',
                'Hello world. How are you?',
                'en',
            ),
            # Empty text.
            (
                [''],
                'en',
                '',
                'en',
            ),
            # Only whitespace.
            (
                ['   ', '\t', '\n'],
                'en',
                '',
                'en',
            ),
            # Language detection returned from info.
            (
                ['Hola mundo.'],
                'es',
                'Hola mundo.',
                'es',
            ),
        ],
    )
    def test_transcribe_normalization(
        self,
        segment_texts: list[str],
        language: str,
        expected_text: str,
        expected_language: str,
    ) -> None:
        """Verify text normalization with mock segments."""
        mock_segments = [_make_mock_segment(t) for t in segment_texts]
        mock_info = _make_mock_info(language=expected_language)

        with patch(
            'app.infrastructure.transcriber.faster_whisper_transcriber.WhisperModel'
        ) as MockWhisperModel:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = (mock_segments, mock_info)
            MockWhisperModel.return_value = mock_model

            transcriber = FasterWhisperTranscriber(
                model_size='tiny',
                device='cpu',
                compute_type='int8',
            )
            result = transcriber.transcribe('fake_path.mp3', language=language)

        assert isinstance(result, TranscriptionResult)
        assert result.text == expected_text
        assert result.language == expected_language

    def test_transcribe_japanese_language(self) -> None:
        """Verify Japanese text is handled correctly."""
        mock_segments = [_make_mock_segment('こんにちは 世界。')]
        mock_info = _make_mock_info(language='ja')

        with patch(
            'app.infrastructure.transcriber.faster_whisper_transcriber.WhisperModel'
        ) as MockWhisperModel:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = (mock_segments, mock_info)
            MockWhisperModel.return_value = mock_model

            transcriber = FasterWhisperTranscriber(
                model_size='tiny',
                device='cpu',
                compute_type='int8',
            )
            result = transcriber.transcribe('fake_path.mp3')

        assert result.text == 'こんにちは 世界。'
        assert result.language == 'ja'

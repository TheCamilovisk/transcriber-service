from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.database.models import TranscriptionJob
from app.infrastructure.repositories.transcription_job_repository import (
    TranscriptionJobRepository,
)
from app.infrastructure.storage.local_audio_storage import LocalAudioStorage
from app.infrastructure.transcriber.faster_whisper_transcriber import (
    TranscriptionResult,
)
from app.settings import get_settings
from app.utils.time import utc_now

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg', 'webm'}
LANGUAGE_PATTERN = re.compile(r'^[a-z]{2,5}$')


def _get_extension(filename: str) -> str | None:
    """Extract the last suffix, lowercased, without the dot."""
    suffix = Path(filename).suffix
    if not suffix:
        return None
    return suffix[1:].lower()


def validate_extension(filename: str) -> str:
    """Validate the file extension. Returns the lowercased extension."""
    extension = _get_extension(filename)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                'Unsupported audio format. '
                'Allowed formats: mp3, wav, m4a, ogg, webm.'
            ),
        )
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                'Unsupported audio format. '
                'Allowed formats: mp3, wav, m4a, ogg, webm.'
            ),
        )
    return extension


def validate_language(language: str | None) -> None:
    """Validate optional language code."""
    if language is not None and not LANGUAGE_PATTERN.match(language):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail='Invalid language value.',
        )


class TranscriptionService:
    def __init__(self, session: Session):
        self._session = session
        self._repository = TranscriptionJobRepository(session)
        self._storage = LocalAudioStorage()

    def create_transcription_job(
        self,
        *,
        original_filename: str,
        content: bytes,
        content_type: str | None,
        language: str | None,
    ) -> TranscriptionJob:
        # 1. Validate extension.
        extension = validate_extension(original_filename)

        # 2. Validate language.
        validate_language(language)

        # 3. Validate size and empty file using actual content bytes.
        settings = get_settings()
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail='Uploaded audio file exceeds the 25 MB limit.',
            )
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Uploaded audio file is empty.',
            )

        # 4. Generate UUID before saving the file.
        job_id = str(uuid.uuid4())
        stored_audio_path, file_size_bytes = self._storage.save_upload(
            content=content, job_id=job_id, extension=extension
        )

        # 5. Create DB job with status pending.
        now = utc_now()
        job = TranscriptionJob(
            id=job_id,
            status='pending',
            original_filename=original_filename,
            stored_audio_path=stored_audio_path,
            content_type=content_type,
            file_size_bytes=file_size_bytes,
            language=language,
            text=None,
            error_message=None,
            created_at=now,
            updated_at=now,
            started_at=None,
            finished_at=None,
        )

        try:
            self._repository.add(job)
            self._session.commit()
        except Exception:
            self._session.rollback()
            self._storage.delete(stored_audio_path)
            raise

        return job

    def get_transcription_job(self, job_id: str) -> TranscriptionJob | None:
        return self._repository.get_by_id(job_id)

    def list_transcription_jobs(
        self,
        *,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TranscriptionJob], int]:
        items = self._repository.list(status=status, limit=limit, offset=offset)
        total = self._repository.count(status=status)
        return items, total

    def claim_next_pending_job(self) -> TranscriptionJob | None:
        job = self._repository.get_oldest_pending()
        if job is None:
            return None

        now = utc_now()
        job.status = 'processing'
        job.started_at = now
        job.updated_at = now
        self._session.commit()
        return job

    def reset_processing_jobs_to_pending(self) -> list[TranscriptionJob]:
        jobs = self._repository.list_processing_jobs()
        now = utc_now()
        for job in jobs:
            job.status = 'pending'
            job.started_at = None
            job.updated_at = now
        if jobs:
            self._session.commit()
        return jobs

    def process_job(self, job_id: str, transcriber) -> None:
        """Process a transcription job using the given transcriber.

        Fetches the job, checks audio file existence, transcribes,
        stores the result, and cleans up the audio file.
        """
        job = self._repository.get_by_id(job_id)
        if job is None:
            logger.warning('Job %s not found, skipping.', job_id)
            return

        audio_path = job.stored_audio_path

        # Check if the audio file still exists.
        if not self._storage.exists(audio_path):
            logger.warning(
                'Audio file missing for job %s: %s', job_id, audio_path
            )
            job.status = 'failed'
            job.error_message = 'Audio file is no longer available.'
            job.finished_at = utc_now()
            job.updated_at = utc_now()
            self._session.commit()
            return

        # Transcribe.
        try:
            result: TranscriptionResult = transcriber.transcribe(
                audio_path, language=job.language
            )
        except Exception:
            logger.exception('Transcription failed for job %s.', job_id)
            job.status = 'failed'
            job.error_message = 'Could not transcribe the audio file.'
            job.finished_at = utc_now()
            job.updated_at = utc_now()
            self._session.commit()
            self._storage.delete(audio_path)
            return

        # Store result.
        job.text = result.text
        if job.language is None:
            job.language = result.language
        job.status = 'completed'
        job.finished_at = utc_now()
        job.updated_at = utc_now()
        self._session.commit()

        # Clean up audio file after processing.
        self._storage.delete(audio_path)

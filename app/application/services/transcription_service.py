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

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.services.transcription_service import (
    TranscriptionService,
)
from app.infrastructure.database.session import get_db


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


def get_transcription_service(
    session: Session = Depends(get_db_session),
) -> TranscriptionService:
    return TranscriptionService(session)

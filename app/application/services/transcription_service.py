from sqlalchemy.orm import Session

from app.infrastructure.database.models import TranscriptionJob
from app.infrastructure.repositories.transcription_job_repository import (
    TranscriptionJobRepository,
)


class TranscriptionService:
    def __init__(self, session: Session):
        self._session = session
        self._repository = TranscriptionJobRepository(session)

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

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import TranscriptionJob


class TranscriptionJobRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, job: TranscriptionJob) -> None:
        self._session.add(job)

    def get_by_id(self, job_id: str) -> TranscriptionJob | None:
        return self._session.get(TranscriptionJob, job_id)

    def list(
        self,
        *,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[TranscriptionJob]:
        stmt = select(TranscriptionJob).order_by(
            TranscriptionJob.created_at.desc()
        )
        if status is not None:
            stmt = stmt.where(TranscriptionJob.status == status)
        stmt = stmt.offset(offset).limit(limit)
        return list(self._session.execute(stmt).scalars().all())

    def count(self, *, status: str | None = None) -> int:
        stmt = select(func.count(TranscriptionJob.id))
        if status is not None:
            stmt = stmt.where(TranscriptionJob.status == status)
        result = self._session.execute(stmt).scalar()
        return result or 0

    def get_oldest_pending(self) -> TranscriptionJob | None:
        stmt = (
            select(TranscriptionJob)
            .where(TranscriptionJob.status == 'pending')
            .order_by(TranscriptionJob.created_at.asc())
            .limit(1)
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def list_processing_jobs(self) -> list[TranscriptionJob]:
        stmt = select(TranscriptionJob).where(
            TranscriptionJob.status == 'processing'
        )
        return list(self._session.execute(stmt).scalars().all())

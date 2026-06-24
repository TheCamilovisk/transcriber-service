"""Tests for worker claiming and startup recovery logic."""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.services.transcription_service import (
    TranscriptionService,
)
from app.infrastructure.database.base import Base
from app.infrastructure.database.models import TranscriptionJob
from app.utils.time import utc_now


@pytest.fixture
def session() -> Session:
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    sess = TestSession()
    yield sess
    sess.close()


@pytest.fixture
def service(session: Session) -> TranscriptionService:
    return TranscriptionService(session)


def make_job(
    job_id: str = 'test-id',
    status: str = 'pending',
    original_filename: str = 'test.mp3',
    created_at=utc_now(),
) -> TranscriptionJob:
    now = created_at
    return TranscriptionJob(
        id=job_id,
        status=status,
        original_filename=original_filename,
        stored_audio_path=f'data/uploads/{job_id}.mp3',
        content_type='audio/mpeg',
        file_size_bytes=1024,
        language=None,
        text=None,
        error_message=None,
        created_at=now,
        updated_at=now,
        started_at=None,
        finished_at=None,
    )


class TestClaimNextPendingJob:
    def test_claims_oldest_pending_job(self, service, session):
        older = make_job(
            job_id='job-older',
            created_at=utc_now() - timedelta(hours=3),
        )
        newer = make_job(
            job_id='job-newer',
            created_at=utc_now() - timedelta(hours=1),
        )
        session.add(older)
        session.add(newer)
        session.commit()

        claimed = service.claim_next_pending_job()
        assert claimed is not None
        assert claimed.id == 'job-older'

    def test_claimed_job_becomes_processing(self, service, session):
        session.add(make_job(job_id='job-1'))
        session.commit()

        claimed = service.claim_next_pending_job()
        assert claimed is not None
        assert claimed.status == 'processing'

        # Verify it's persisted.
        session.refresh(claimed)
        assert claimed.status == 'processing'

    def test_started_at_is_set(self, service, session):
        session.add(make_job(job_id='job-1'))
        session.commit()

        claimed = service.claim_next_pending_job()
        assert claimed is not None
        assert claimed.started_at is not None
        assert isinstance(claimed.started_at, type(utc_now()))

    def test_updated_at_is_set(self, service, session):
        old_now = utc_now()
        job = make_job(job_id='job-1', created_at=old_now)
        session.add(job)
        session.commit()

        # Small delay to ensure updated_at differs.
        claimed = service.claim_next_pending_job()
        assert claimed is not None
        assert claimed.updated_at is not None
        # updated_at should be >= started_at (both set now).
        assert claimed.updated_at >= claimed.started_at

    def test_returns_none_when_no_pending(self, service, session):
        completed = make_job(job_id='job-1', status='completed')
        processing = make_job(job_id='job-2', status='processing')
        session.add(completed)
        session.add(processing)
        session.commit()

        claimed = service.claim_next_pending_job()
        assert claimed is None


class TestResetProcessingJobsToPending:
    def test_resets_processing_to_pending(self, service, session):
        job = make_job(job_id='job-1', status='processing')
        # Set started_at like a real claim would.
        job.started_at = utc_now() - timedelta(minutes=5)
        session.add(job)
        session.commit()

        reset = service.reset_processing_jobs_to_pending()
        assert len(reset) == 1
        assert reset[0].id == 'job-1'

        session.refresh(job)
        assert job.status == 'pending'

    def test_reset_clears_started_at(self, service, session):
        job = make_job(job_id='job-1', status='processing')
        job.started_at = utc_now() - timedelta(minutes=5)
        session.add(job)
        session.commit()

        service.reset_processing_jobs_to_pending()
        session.refresh(job)
        assert job.started_at is None

    def test_reset_sets_updated_at(self, service, session):
        old_now = utc_now()
        job = make_job(job_id='job-1', status='processing')
        job.started_at = old_now
        job.updated_at = old_now
        session.add(job)
        session.commit()

        service.reset_processing_jobs_to_pending()
        session.refresh(job)
        # Compare as naive to avoid timezone-awareness issues with SQLite.
        updated_at_naive = job.updated_at.replace(tzinfo=None)
        old_now_naive = old_now.replace(tzinfo=None)
        assert updated_at_naive > old_now_naive

    def test_reset_ignores_non_processing(self, service, session):
        pending = make_job(job_id='job-1', status='pending')
        completed = make_job(job_id='job-2', status='completed')
        failed = make_job(job_id='job-3', status='failed')
        session.add(pending)
        session.add(completed)
        session.add(failed)
        session.commit()

        reset = service.reset_processing_jobs_to_pending()
        assert reset == []

        # Verify none changed.
        session.refresh(pending)
        assert pending.status == 'pending'

    def test_reset_multiple_processing_jobs(self, service, session):
        job1 = make_job(job_id='job-1', status='processing')
        job1.started_at = utc_now() - timedelta(hours=1)
        job2 = make_job(job_id='job-2', status='processing')
        job2.started_at = utc_now() - timedelta(hours=2)

        session.add(job1)
        session.add(job2)
        session.commit()

        reset = service.reset_processing_jobs_to_pending()
        assert len(reset) == 2

        session.refresh(job1)
        session.refresh(job2)
        assert job1.status == 'pending'
        assert job1.started_at is None
        assert job2.status == 'pending'
        assert job2.started_at is None

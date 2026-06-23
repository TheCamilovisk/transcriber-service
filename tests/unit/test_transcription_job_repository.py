from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.database.base import Base
from app.infrastructure.database.models import TranscriptionJob
from app.infrastructure.repositories.transcription_job_repository import (
    TranscriptionJobRepository,
)
from app.utils.time import utc_now


@pytest.fixture
def session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    sess = TestSession()
    yield sess
    sess.close()


@pytest.fixture
def repository(session: Session):
    return TranscriptionJobRepository(session)


def make_job(
    job_id: str = 'test-id',
    status: str = 'pending',
    original_filename: str = 'test.mp3',
    created_at: datetime | None = None,
) -> TranscriptionJob:
    now = created_at or utc_now()
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


class TestAddAndGetById:
    def test_add_and_get_by_id(self, repository, session):
        job = make_job()
        repository.add(job)
        session.commit()

        retrieved = repository.get_by_id('test-id')
        assert retrieved is not None
        assert retrieved.id == 'test-id'
        assert retrieved.status == 'pending'
        assert retrieved.original_filename == 'test.mp3'
        assert retrieved.file_size_bytes == 1024

    def test_get_by_id_returns_none_for_missing(self, repository):
        assert repository.get_by_id('nonexistent') is None


class TestList:
    def test_list_returns_newest_first(self, repository, session):
        older = make_job(
            job_id='job-1',
            created_at=utc_now() - timedelta(hours=2),
        )
        newer = make_job(
            job_id='job-2',
            created_at=utc_now() - timedelta(hours=1),
        )
        repository.add(older)
        repository.add(newer)
        session.commit()

        results = repository.list(limit=10, offset=0)
        assert len(results) == 2
        assert results[0].id == 'job-2'
        assert results[1].id == 'job-1'

    def test_list_filters_by_status(self, repository, session):
        pending = make_job(job_id='job-1')
        completed = make_job(job_id='job-2', status='completed')
        repository.add(pending)
        repository.add(completed)
        session.commit()

        results = repository.list(status='pending', limit=10, offset=0)
        assert len(results) == 1
        assert results[0].id == 'job-1'

    def test_list_respects_limit_and_offset(self, repository, session):
        for i in range(5):
            repository.add(make_job(job_id=f'job-{i}'))
        session.commit()

        results = repository.list(limit=2, offset=0)
        assert len(results) == 2

        # Offset 2 should skip the first 2 (newest: job-4, job-3)
        results_page2 = repository.list(limit=2, offset=2)
        assert len(results_page2) == 2

    def test_list_without_status_returns_all(self, repository, session):
        repository.add(make_job(job_id='job-1', status='pending'))
        repository.add(make_job(job_id='job-2', status='completed'))
        repository.add(make_job(job_id='job-3', status='failed'))
        session.commit()

        results = repository.list(limit=10, offset=0)
        assert len(results) == 3


class TestCount:
    def test_count_all(self, repository, session):
        repository.add(make_job(job_id='job-1'))
        repository.add(make_job(job_id='job-2'))
        session.commit()

        assert repository.count() == 2

    def test_count_with_status(self, repository, session):
        repository.add(make_job(job_id='job-1', status='pending'))
        repository.add(make_job(job_id='job-2', status='completed'))
        session.commit()

        assert repository.count(status='pending') == 1
        assert repository.count(status='completed') == 1
        assert repository.count(status='failed') == 0

    def test_count_empty(self, repository):
        assert repository.count() == 0


class TestGetOldestPending:
    def test_returns_oldest_pending(self, repository, session):
        older = make_job(
            job_id='job-1',
            created_at=utc_now() - timedelta(hours=3),
        )
        newer = make_job(
            job_id='job-2',
            created_at=utc_now() - timedelta(hours=1),
        )
        repository.add(older)
        repository.add(newer)
        session.commit()

        result = repository.get_oldest_pending()
        assert result is not None
        assert result.id == 'job-1'

    def test_ignores_non_pending_jobs(self, repository, session):
        completed = make_job(
            job_id='job-1',
            status='completed',
        )
        processing = make_job(
            job_id='job-2',
            status='processing',
        )
        repository.add(completed)
        repository.add(processing)
        session.commit()

        result = repository.get_oldest_pending()
        assert result is None

    def test_returns_none_when_no_pending(self, repository):
        assert repository.get_oldest_pending() is None


class TestListProcessingJobs:
    def test_returns_processing_jobs(self, repository, session):
        processing = make_job(job_id='job-1', status='processing')
        pending = make_job(job_id='job-2', status='pending')
        repository.add(processing)
        repository.add(pending)
        session.commit()

        results = repository.list_processing_jobs()
        assert len(results) == 1
        assert results[0].id == 'job-1'

    def test_returns_empty_when_none_processing(self, repository, session):
        pending = make_job(job_id='job-1', status='pending')
        repository.add(pending)
        session.commit()

        results = repository.list_processing_jobs()
        assert results == []

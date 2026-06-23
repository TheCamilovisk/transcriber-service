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
def session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    sess = TestSession()
    yield sess
    sess.close()


@pytest.fixture
def service(session: Session):
    return TranscriptionService(session)


def make_job(job_id: str = 'test-id') -> TranscriptionJob:
    now = utc_now()
    return TranscriptionJob(
        id=job_id,
        status='pending',
        original_filename='test.mp3',
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


class TestGetTranscriptionJob:
    def test_get_existing_job(self, service, session):
        job = make_job()
        session.add(job)
        session.commit()

        result = service.get_transcription_job('test-id')
        assert result is not None
        assert result.id == 'test-id'
        assert result.status == 'pending'

    def test_get_missing_job_returns_none(self, service):
        result = service.get_transcription_job('nonexistent')
        assert result is None


class TestListTranscriptionJobs:
    def test_list_all_jobs(self, service, session):
        session.add(make_job(job_id='job-1'))
        session.add(make_job(job_id='job-2'))
        session.commit()

        items, total = service.list_transcription_jobs()
        assert len(items) == 2
        assert total == 2

    def test_list_filters_by_status(self, service, session):
        session.add(make_job(job_id='job-1'))
        job2 = make_job(job_id='job-2')
        job2.status = 'completed'
        session.add(job2)
        session.commit()

        items, total = service.list_transcription_jobs(status='pending')
        assert len(items) == 1
        assert total == 1
        assert items[0].id == 'job-1'

    def test_list_with_pagination(self, service, session):
        for i in range(5):
            session.add(make_job(job_id=f'job-{i}'))
        session.commit()

        items, total = service.list_transcription_jobs(limit=2, offset=0)
        assert len(items) == 2
        assert total == 5

    def test_list_empty(self, service):
        items, total = service.list_transcription_jobs()
        assert items == []
        assert total == 0

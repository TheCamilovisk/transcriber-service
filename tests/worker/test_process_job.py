"""Tests for TranscriptionService.process_job with fake transcribers."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.services.transcription_service import (
    TranscriptionService,
)
from app.infrastructure.database.base import Base
from app.infrastructure.database.models import TranscriptionJob
from app.infrastructure.storage.local_audio_storage import LocalAudioStorage
from app.utils.time import utc_now
from tests.fakes import (
    FakeTranscriber,
    FakeTranscriberAlwaysFails,
    FakeTranscriberEmptyResult,
)


@pytest.fixture
def upload_dir(tmp_path) -> Path:
    d = tmp_path / 'uploads'
    d.mkdir()
    return d


@pytest.fixture
def session() -> Session:
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    sess = TestSession()
    yield sess
    sess.close()


@pytest.fixture
def service(session: Session, upload_dir: Path) -> TranscriptionService:
    svc = TranscriptionService(session)
    svc._storage = LocalAudioStorage(upload_dir=str(upload_dir))
    return svc


def create_audio_file(upload_dir: Path, job_id: str) -> Path:
    """Create a dummy audio file and return its path."""
    filepath = upload_dir / f'{job_id}.mp3'
    filepath.write_text('fake audio content')
    return filepath


def make_job(
    job_id: str = 'test-id',
    status: str = 'processing',
    stored_audio_path: str = '',
    language: str | None = None,
) -> TranscriptionJob:
    now = utc_now()
    return TranscriptionJob(
        id=job_id,
        status=status,
        original_filename='test.mp3',
        stored_audio_path=stored_audio_path,
        content_type='audio/mpeg',
        file_size_bytes=1024,
        language=language,
        text=None,
        error_message=None,
        created_at=now,
        updated_at=now,
        started_at=now,
        finished_at=None,
    )


class TestProcessJobSuccess:
    def test_job_becomes_completed(self, service, session, upload_dir):
        job_id = 'job-success-1'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriber())

        session.refresh(job)
        assert job.status == 'completed'

    def test_text_is_stored(self, service, session, upload_dir):
        job_id = 'job-success-2'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriber())

        session.refresh(job)
        assert job.text == 'Fake transcription.'

    def test_language_remains_provided_language(  # noqa: PLR0913
        self,
        service,
        session,
        upload_dir,
    ):
        job_id = 'job-success-3'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
            language='es',
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriber())

        session.refresh(job)
        assert job.language == 'es'

    def test_language_stored_from_result_when_null(
        self,
        service,
        session,
        upload_dir,
    ):
        job_id = 'job-success-4'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
            language=None,
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriber())

        session.refresh(job)
        assert job.language == 'en'

    def test_finished_at_is_set(self, service, session, upload_dir):
        job_id = 'job-success-5'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriber())

        session.refresh(job)
        assert job.finished_at is not None
        assert isinstance(job.finished_at, type(utc_now()))

    def test_audio_file_is_deleted(self, service, session, upload_dir):
        job_id = 'job-success-6'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        assert audio_path.exists()
        service.process_job(job_id, FakeTranscriber())
        assert not audio_path.exists()


class TestProcessJobFailure:
    def test_transcriber_exception_marks_failed(
        self,
        service,
        session,
        upload_dir,
    ):
        job_id = 'job-fail-1'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriberAlwaysFails())

        session.refresh(job)
        assert job.status == 'failed'

    def test_clean_error_message_is_stored(
        self,
        service,
        session,
        upload_dir,
    ):
        job_id = 'job-fail-2'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriberAlwaysFails())

        session.refresh(job)
        assert job.error_message == 'Could not transcribe the audio file.'

    def test_text_remains_null_after_failure(
        self,
        service,
        session,
        upload_dir,
    ):
        job_id = 'job-fail-3'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriberAlwaysFails())

        session.refresh(job)
        assert job.text is None

    def test_finished_at_is_set_on_failure(
        self,
        service,
        session,
        upload_dir,
    ):
        job_id = 'job-fail-4'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriberAlwaysFails())

        session.refresh(job)
        assert job.finished_at is not None

    def test_audio_file_deleted_after_failure(
        self,
        service,
        session,
        upload_dir,
    ):
        job_id = 'job-fail-5'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        assert audio_path.exists()
        service.process_job(job_id, FakeTranscriberAlwaysFails())
        assert not audio_path.exists()


class TestProcessJobMissingAudio:
    def test_missing_audio_marks_failed(self, service, session, upload_dir):
        job_id = 'job-missing-1'
        audio_path = upload_dir / f'{job_id}.mp3'
        # Intentionally do NOT create the file.
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriber())

        session.refresh(job)
        assert job.status == 'failed'

    def test_missing_audio_error_message(
        self,
        service,
        session,
        upload_dir,
    ):
        job_id = 'job-missing-2'
        audio_path = upload_dir / f'{job_id}.mp3'
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriber())

        session.refresh(job)
        assert job.error_message == 'Audio file is no longer available.'

    def test_missing_audio_no_retry(self, service, session, upload_dir):
        job_id = 'job-missing-3'
        audio_path = upload_dir / f'{job_id}.mp3'
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        # First call — should fail.
        service.process_job(job_id, FakeTranscriber())
        session.refresh(job)
        assert job.status == 'failed'

        # Second call — job is already failed, should be a no-op
        # (process_job should not re-process a failed/non-processing job).
        old_error = job.error_message
        service.process_job(job_id, FakeTranscriber())
        session.refresh(job)
        assert job.status == 'failed'
        # Error message should remain the same.
        assert job.error_message == old_error


class TestProcessJobEmptyResult:
    def test_empty_text_marks_completed(self, service, session, upload_dir):
        job_id = 'job-empty-1'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriberEmptyResult())

        session.refresh(job)
        assert job.status == 'completed'

    def test_empty_text_is_stored(self, service, session, upload_dir):
        job_id = 'job-empty-2'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriberEmptyResult())

        session.refresh(job)
        assert job.text == ''  # noqa: PLC1901

    def test_empty_text_still_sets_finished_at(
        self,
        service,
        session,
        upload_dir,
    ):
        job_id = 'job-empty-3'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        service.process_job(job_id, FakeTranscriberEmptyResult())

        session.refresh(job)
        assert job.finished_at is not None

    def test_empty_text_still_deletes_audio(
        self,
        service,
        session,
        upload_dir,
    ):
        job_id = 'job-empty-4'
        audio_path = create_audio_file(upload_dir, job_id)
        job = make_job(
            job_id=job_id,
            stored_audio_path=str(audio_path),
        )
        session.add(job)
        session.commit()

        assert audio_path.exists()
        service.process_job(job_id, FakeTranscriberEmptyResult())
        assert not audio_path.exists()

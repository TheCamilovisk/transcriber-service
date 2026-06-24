from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies import get_transcription_service
from app.application.services.transcription_service import (
    TranscriptionService,
)
from app.infrastructure.database.base import Base
from app.infrastructure.storage.local_audio_storage import LocalAudioStorage
from app.main import app


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / 'test.db')


@pytest.fixture
def db_session(db_path: str) -> Generator[Session, None, None]:
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    sess = TestSession()
    yield sess
    sess.close()


@pytest.fixture
def upload_dir(tmp_path) -> str:
    d = tmp_path / 'uploads'
    d.mkdir()
    return str(d)


@pytest.fixture
def test_client(
    db_session: Session,
    upload_dir: str,
) -> Generator[TestClient, None, None]:
    storage = LocalAudioStorage(upload_dir=upload_dir)
    service = TranscriptionService(db_session)
    service._storage = storage

    def _override_service() -> TranscriptionService:
        return service

    app.dependency_overrides[get_transcription_service] = _override_service

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()

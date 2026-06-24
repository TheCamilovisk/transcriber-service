import uuid
from pathlib import Path

from fastapi.testclient import TestClient


class TestCreateTranscriptionJob:
    ENDPOINT = '/api/v1/transcriptions'

    def test_upload_valid_mp3_creates_pending_job(
        self, test_client: TestClient, upload_dir: str
    ):
        response = test_client.post(
            self.ENDPOINT,
            files={
                'audio': ('test-audio.mp3', b'fake mp3 content', 'audio/mpeg')
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data['status'] == 'pending'
        assert data['text'] is None
        assert data['error_message'] is None
        assert data['started_at'] is None
        assert data['finished_at'] is None
        assert data['content_type'] == 'audio/mpeg'

        # Response includes full job representation.
        assert 'id' in data
        assert 'original_filename' in data
        assert 'file_size_bytes' in data
        assert 'language' in data
        assert 'created_at' in data
        assert 'updated_at' in data

        # original_filename is stored.
        assert data['original_filename'] == 'test-audio.mp3'

        # File is saved with UUID filename.
        job_id = data['id']
        # Validate it's a valid UUID.
        uuid.UUID(job_id)
        saved_path = Path(upload_dir) / f'{job_id}.mp3'
        assert saved_path.exists()
        assert saved_path.read_bytes() == b'fake mp3 content'

    def test_upload_valid_wav_creates_pending_job(
        self, test_client: TestClient
    ):
        response = test_client.post(
            self.ENDPOINT,
            files={'audio': ('recording.wav', b'wav data')},
        )
        assert response.status_code == 201
        data = response.json()
        assert data['status'] == 'pending'
        assert data['original_filename'] == 'recording.wav'

    def test_upload_with_content_type(
        self, test_client: TestClient, upload_dir: str
    ):
        response = test_client.post(
            self.ENDPOINT,
            files={
                'audio': (
                    'meeting.ogg',
                    b'ogg data',
                    'audio/ogg',
                )
            },
        )
        assert response.status_code == 201
        assert response.json()['content_type'] == 'audio/ogg'

    def test_upload_without_content_type(self, test_client: TestClient):
        # When httpx does not send an explicit Content-Type for the file,
        # it may default to a guess like 'audio/mp4' for .m4a. The API
        # should still accept the upload and store whatever content type
        # the client sends (or None if none was provided).
        response = test_client.post(
            self.ENDPOINT,
            files={'audio': ('noctype.m4a', b'some data')},
        )
        assert response.status_code == 201
        data = response.json()
        # The API stores whatever the client sent; no validation is done.
        assert 'content_type' in data

    def test_upload_with_language(self, test_client: TestClient):
        response = test_client.post(
            self.ENDPOINT,
            files={'audio': ('sample.mp3', b'data')},
            data={'language': 'pt'},
        )
        assert response.status_code == 201
        assert response.json()['language'] == 'pt'

    def test_upload_without_language(self, test_client: TestClient):
        response = test_client.post(
            self.ENDPOINT,
            files={'audio': ('sample.mp3', b'data')},
        )
        assert response.status_code == 201
        assert response.json()['language'] is None

    # --- Validation tests ---

    def test_unsupported_extension_returns_400(self, test_client: TestClient):
        response = test_client.post(
            self.ENDPOINT,
            files={'audio': ('video.avi', b'content')},
        )
        assert response.status_code == 400
        assert 'Unsupported audio format' in response.json()['detail']

    def test_no_extension_returns_400(self, test_client: TestClient):
        response = test_client.post(
            self.ENDPOINT,
            files={'audio': ('noextension', b'content')},
        )
        assert response.status_code == 400
        assert 'Unsupported audio format' in response.json()['detail']

    def test_empty_file_returns_400(self, test_client: TestClient):
        response = test_client.post(
            self.ENDPOINT,
            files={'audio': ('empty.mp3', b'')},
        )
        assert response.status_code == 400
        assert 'empty' in response.json()['detail'].lower()

    def test_oversized_file_returns_413(self, test_client: TestClient):
        # 25 MB + 1 byte
        oversized = b'x' * (25 * 1024 * 1024 + 1)
        response = test_client.post(
            self.ENDPOINT,
            files={'audio': ('large.mp3', oversized)},
        )
        assert response.status_code == 413
        assert '25 MB' in response.json()['detail']

    def test_invalid_language_returns_422(self, test_client: TestClient):
        response = test_client.post(
            self.ENDPOINT,
            files={'audio': ('sample.mp3', b'data')},
            data={'language': 'english'},
        )
        assert response.status_code == 422
        assert 'Invalid language' in response.json()['detail']

    def test_empty_language_string_treated_as_none(
        self, test_client: TestClient
    ):
        # An empty string language is treated as if language was not
        # provided (stored as null, job is created).
        response = test_client.post(
            self.ENDPOINT,
            files={'audio': ('sample.mp3', b'data')},
            data={'language': ''},
        )
        assert response.status_code == 201
        assert response.json()['language'] is None

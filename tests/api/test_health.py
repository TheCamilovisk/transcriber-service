from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.infrastructure.storage.local_audio_storage import LocalAudioStorage


class TestHealth:
    ENDPOINT = '/health'

    def test_health_returns_ok_when_all_checks_pass(
        self, test_client: TestClient
    ):
        response = test_client.get(self.ENDPOINT)
        assert response.status_code == 200
        data = response.json()

        assert data == {
            'status': 'ok',
            'database': 'ok',
            'upload_dir': 'ok',
        }

    def test_health_returns_503_when_upload_dir_not_writable(
        self, test_client: TestClient
    ):
        with patch.object(
            LocalAudioStorage,
            'validate_writable',
            side_effect=RuntimeError('Not writable'),
        ):
            response = test_client.get(self.ENDPOINT)

        assert response.status_code == 503
        data = response.json()

        assert data == {
            'status': 'error',
            'database': 'ok',
            'upload_dir': 'error',
        }

    def test_response_has_expected_structure(self, test_client: TestClient):
        response = test_client.get(self.ENDPOINT)
        assert response.status_code == 200
        data = response.json()

        assert set(data.keys()) == {'status', 'database', 'upload_dir'}
        assert data['status'] in {'ok', 'error'}
        assert data['database'] in {'ok', 'error'}
        assert data['upload_dir'] in {'ok', 'error'}

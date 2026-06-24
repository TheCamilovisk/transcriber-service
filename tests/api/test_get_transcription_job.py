from fastapi.testclient import TestClient


class TestGetTranscriptionJob:
    ENDPOINT = '/api/v1/transcriptions'

    def test_get_existing_job_returns_full_job(self, test_client: TestClient):
        # Create a job first
        create_resp = test_client.post(
            self.ENDPOINT,
            files={'audio': ('test.mp3', b'fake mp3 content', 'audio/mpeg')},
        )
        assert create_resp.status_code == 201
        job_id = create_resp.json()['id']

        # Fetch the job
        response = test_client.get(f'{self.ENDPOINT}/{job_id}')
        assert response.status_code == 200
        data = response.json()

        assert data['id'] == job_id
        assert data['status'] == 'pending'
        assert data['original_filename'] == 'test.mp3'
        assert data['text'] is None
        assert data['error_message'] is None
        assert data['started_at'] is None
        assert data['finished_at'] is None
        assert data['file_size_bytes'] == len(b'fake mp3 content')
        assert data['language'] is None

        # Verify all expected fields are present
        expected_fields = {
            'id',
            'status',
            'original_filename',
            'content_type',
            'file_size_bytes',
            'language',
            'text',
            'error_message',
            'created_at',
            'updated_at',
            'started_at',
            'finished_at',
        }
        assert set(data.keys()) == expected_fields

    def test_get_missing_job_returns_404(self, test_client: TestClient):
        response = test_client.get(
            f'{self.ENDPOINT}/00000000-0000-0000-0000-000000000000'
        )
        assert response.status_code == 404
        assert response.json()['detail'] == 'Transcription job not found.'

    def test_invalid_uuid_returns_422(self, test_client: TestClient):
        response = test_client.get(f'{self.ENDPOINT}/not-a-uuid')
        assert response.status_code == 422

from fastapi.testclient import TestClient


class TestListTranscriptionJobs:
    ENDPOINT = '/api/v1/transcriptions'

    def _create_job(
        self, test_client: TestClient, filename: str = 'test.mp3'
    ) -> str:
        resp = test_client.post(
            self.ENDPOINT,
            files={'audio': (filename, b'content')},
        )
        assert resp.status_code == 201
        return resp.json()['id']

    def test_returns_items_limit_offset_total(self, test_client: TestClient):
        self._create_job(test_client)
        self._create_job(test_client)

        response = test_client.get(self.ENDPOINT)
        assert response.status_code == 200
        data = response.json()

        assert 'items' in data
        assert 'limit' in data
        assert 'offset' in data
        assert 'total' in data
        assert len(data['items']) == 2
        assert data['total'] == 2

    def test_default_limit_is_20(self, test_client: TestClient):
        response = test_client.get(self.ENDPOINT)
        assert response.status_code == 200
        assert response.json()['limit'] == 20

    def test_max_limit_is_100(self, test_client: TestClient):
        response = test_client.get(f'{self.ENDPOINT}?limit=100')
        assert response.status_code == 200
        assert response.json()['limit'] == 100

    def test_rejects_limit_above_100(self, test_client: TestClient):
        response = test_client.get(f'{self.ENDPOINT}?limit=101')
        assert response.status_code == 422

    def test_rejects_limit_below_1(self, test_client: TestClient):
        response = test_client.get(f'{self.ENDPOINT}?limit=0')
        assert response.status_code == 422

    def test_rejects_negative_offset(self, test_client: TestClient):
        response = test_client.get(f'{self.ENDPOINT}?offset=-1')
        assert response.status_code == 422

    def test_rejects_invalid_status_filter_with_422(
        self, test_client: TestClient
    ):
        response = test_client.get(f'{self.ENDPOINT}?status=invalid_status')
        assert response.status_code == 422

    def test_supports_status_filter(self, test_client: TestClient):
        self._create_job(test_client)
        # Create a completed job by directly setting status in DB
        # Since we can't easily create a completed job through the API
        # in this slice, just verify that pending filter returns what
        # we created.
        response = test_client.get(f'{self.ENDPOINT}?status=pending')
        assert response.status_code == 200
        data = response.json()
        assert data['total'] >= 1
        for item in data['items']:
            assert item['status'] == 'pending'

    def test_orders_newest_first(self, test_client: TestClient):
        id1 = self._create_job(test_client, filename='first.mp3')
        id2 = self._create_job(test_client, filename='second.mp3')

        response = test_client.get(self.ENDPOINT)
        data = response.json()
        items = data['items']

        # Find our two jobs in the list
        job_ids = [item['id'] for item in items]
        assert id1 in job_ids
        assert id2 in job_ids

        # The second created job should appear before the first
        assert job_ids.index(id2) < job_ids.index(id1)

    def test_does_not_include_text_in_list_items(self, test_client: TestClient):
        self._create_job(test_client)

        response = test_client.get(self.ENDPOINT)
        data = response.json()
        for item in data['items']:
            assert 'text' not in item

    def test_list_item_has_expected_fields(self, test_client: TestClient):
        self._create_job(test_client)

        response = test_client.get(self.ENDPOINT)
        data = response.json()
        for item in data['items']:
            expected_fields = {
                'id',
                'status',
                'original_filename',
                'content_type',
                'file_size_bytes',
                'language',
                'error_message',
                'created_at',
                'updated_at',
                'started_at',
                'finished_at',
            }
            assert set(item.keys()) == expected_fields

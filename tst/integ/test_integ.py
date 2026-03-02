import pytest
from fastapi.testclient import TestClient
from src.service.service import app


class TestIntegration:
    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            yield client

    def test_provision_and_check_stats(self, client):
        """
        Integration Test:
        Verifies that a provision request flow works from API to Engine.
        """
        # 1. Send a provisioning request
        payload = {
            "id": "test-droplet-01",
            "cpu_required": 2,
            "ram_required": 4,
            "anti_affinity_group": "web-servers"
        }

        response = client.post("/provision", json=payload)

        # 2. Assert the API responded correctly
        assert response.status_code == 201
        data = response.json()
        assert "host_id" in data

        # 3. Verify the system state reflects the change
        # (Assuming you have a stats endpoint)
        stats_response = client.get("/stats")
        assert stats_response.status_code == 200
        # Add specific logic here to check if used_ram increased
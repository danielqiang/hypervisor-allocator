import pytest

from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from src.service import app, get_allocator


class TestService:
    """
    single provision call small vm succeeds
    multiple provision call small vm succeeds
    single provision call large vm succeeds
    single provision call impossibly large vm throws
    multiple provision calls succeeds, final provision call that exceeds capacity throws
    provision -> deprovision -> provision same id succeeds
    provision same id twice throws
    """

    @pytest.fixture
    def mock_allocator(self):
        mock = MagicMock()
        app.dependency_overrides[get_allocator] = lambda: mock

        yield mock

        app.dependency_overrides.clear()

    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            yield client

    def test_allocator_provision_succeeds_yields_201(self, client, mock_allocator):
        host_id = "host1"
        mock_allocator.provision.return_value = host_id

        response = client.post(
            "/provision", json={"id": "vm1", "ram_required": 2, "cpu_required": 2}
        )

        assert response.status_code == 201
        assert response.json()["host_id"] == host_id

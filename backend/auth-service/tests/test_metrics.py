from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.auth
@pytest.mark.metrics
class TestMetricsEndpoint:
    def test_metrics_endpoint(self):
        response = client.get("/auth/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "version" in data
        assert "requests_processed" in data
        assert "http_status_codes" in data
        assert "start_time" in data
        assert "uptime_seconds" in data

        try:
            datetime.fromisoformat(data["start_time"])
        except ValueError:
            pytest.fail("start_time is not in ISO format")

        assert isinstance(data["version"], str)
        assert isinstance(data["requests_processed"], int)
        assert isinstance(data["http_status_codes"], dict)
        assert isinstance(data["uptime_seconds"], (int, float))

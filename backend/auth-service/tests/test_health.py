import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.auth
@pytest.mark.health
@pytest.mark.smoke
def test_health_check():
    response = client.get("/auth/health")
    assert response.status_code == 200
    assert response.json()["status"] == "Auth service started"

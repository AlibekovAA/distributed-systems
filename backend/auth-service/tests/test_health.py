import pytest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.mark.auth
@pytest.mark.health
@pytest.mark.smoke
def test_health_check():
    response = client.get("/auth/health")
    assert response.status_code == 200
    assert response.json()["status"] == "Auth service started"

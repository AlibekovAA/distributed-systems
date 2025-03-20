from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)


@pytest.mark.auth
@pytest.mark.profile
@pytest.mark.security
class TestProfile:
    def test_get_profile_authorized(self, auth_token):
        response = client.get(
            "/auth/profile",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "email" in response.json()
        assert "name" in response.json()
        assert "balance" in response.json()

    def test_get_profile_unauthorized(self):
        response = client.get("/auth/profile")
        assert response.status_code == 401

    def test_get_profile_invalid_token(self):
        response = client.get(
            "/auth/profile",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

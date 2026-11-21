import pytest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.mark.auth
@pytest.mark.login
@pytest.mark.smoke
class TestAuthenticationFlow:
    def test_successful_login(self, registered_user, test_user_data):
        response = client.post(
            "/auth/login", json={"email": test_user_data["email"], "password": test_user_data["password"]}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_invalid_credentials(self, registered_user):
        response = client.post("/auth/login", json={"email": "test@example.com", "password": "wrongpassword"})
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_nonexistent_user_login(self):
        response = client.post("/auth/login", json={"email": "nonexistent@example.com", "password": "password123"})
        assert response.status_code == 401

    def test_refresh_token_cannot_access_profile(self, registered_user, test_user_data):
        login_response = client.post(
            "/auth/login", json={"email": test_user_data["email"], "password": test_user_data["password"]}
        )
        refresh_token = login_response.json()["refresh_token"]

        response = client.get("/auth/profile", headers={"Authorization": f"Bearer {refresh_token}"})

        assert response.status_code == 401

    def test_access_token_cannot_refresh(self, registered_user, test_user_data):
        login_response = client.post(
            "/auth/login", json={"email": test_user_data["email"], "password": test_user_data["password"]}
        )
        access_token = login_response.json()["access_token"]

        response = client.post("/auth/token/refresh", json={"refresh_token": access_token})

        assert response.status_code == 401

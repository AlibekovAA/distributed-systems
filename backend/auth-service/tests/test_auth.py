from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    }


@pytest.fixture
def registered_user(test_user_data):
    response = client.post("/auth/register", json=test_user_data)
    return response.json()


@pytest.fixture
def auth_token(test_user_data):
    response = client.post("/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    return response.json()["access_token"]


def test_health_check():
    response = client.get("/auth/health")
    assert response.status_code == 200
    assert response.json()["status"] == "Auth service started"


class TestRegistration:
    def test_successful_registration(self, test_user_data):
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == 200
        assert "id" in response.json()
        assert response.json()["email"] == test_user_data["email"]

    def test_duplicate_registration(self, test_user_data):
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_invalid_email_registration(self, test_user_data):
        test_user_data["email"] = "invalid-email"
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == 422

    def test_short_password_registration(self, test_user_data):
        test_user_data["password"] = "123"
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == 422


class TestAuthentication:
    def test_successful_login(self, registered_user, test_user_data):
        response = client.post("/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_invalid_credentials(self, registered_user):
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_nonexistent_user_login(self):
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })
        assert response.status_code == 401


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


class TestTokenRefresh:
    def test_successful_token_refresh(self, registered_user, test_user_data):
        login_response = client.post("/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        refresh_token = login_response.json()["refresh_token"]

        response = client.post(
            "/auth/token/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_invalid_refresh_token(self):
        response = client.post(
            "/auth/token/refresh",
            json={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401


class TestEndToEnd:
    def test_complete_auth_flow(self, test_user_data):
        register_response = client.post("/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        user_id = register_response.json()["id"]

        login_response = client.post("/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        profile_response = client.get(
            "/auth/profile",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert profile_response.status_code == 200
        assert profile_response.json()["id"] == user_id

        refresh_response = client.post(
            "/auth/token/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]

        new_profile_response = client.get(
            "/auth/profile",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert new_profile_response.status_code == 200
        assert new_profile_response.json()["id"] == user_id

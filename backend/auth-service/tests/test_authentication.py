from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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

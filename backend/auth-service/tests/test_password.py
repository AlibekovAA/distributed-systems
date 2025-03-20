import time
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.auth
@pytest.mark.password
@pytest.mark.security
class TestPasswordChange:
    def test_successful_password_change(self, auth_token, test_user_data):
        response = client.post(
            "/auth/change-password",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "old_password": test_user_data["password"],
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"

        time.sleep(1)

        login_response = client.post("/auth/login", json={
            "email": test_user_data["email"],
            "password": "newpassword123"
        })
        assert login_response.status_code == 200

    def test_wrong_old_password(self, auth_token):
        response = client.post(
            "/auth/change-password",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "old_password": "wrongpassword",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 400
        assert "Invalid old password" in response.json()["detail"]

    def test_short_new_password(self, auth_token, test_user_data):
        response = client.post(
            "/auth/change-password",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "old_password": test_user_data["password"],
                "new_password": "short"
            }
        )
        assert response.status_code == 400
        assert "Password must be at least 8 characters long" in response.json()["detail"]

    def test_unauthorized_password_change(self):
        response = client.post(
            "/auth/change-password",
            json={
                "old_password": "password123",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 401

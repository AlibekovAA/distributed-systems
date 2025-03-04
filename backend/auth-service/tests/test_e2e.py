from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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
        assert refresh_response.status_code == 422

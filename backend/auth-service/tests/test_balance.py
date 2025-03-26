import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.auth
@pytest.mark.balance
@pytest.mark.smoke
class TestBalanceOperations:
    def test_successful_balance_add(self, auth_token):
        initial_profile = client.get(
            "/auth/profile",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        initial_balance = initial_profile.json()["balance"]

        response = client.post(
            "/auth/add-balance",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"amount": 1000}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["new_balance"] == initial_balance + 1000

        profile_response = client.get(
            "/auth/profile",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert profile_response.json()["balance"] == initial_balance + 1000

    def test_negative_amount(self, auth_token):
        response = client.post(
            "/auth/add-balance",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"amount": -100}
        )
        assert response.status_code == 400
        assert "Amount must be positive" in response.json()["detail"]

    def test_zero_amount(self, auth_token):
        response = client.post(
            "/auth/add-balance",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"amount": 0}
        )
        assert response.status_code == 400
        assert "Amount must be positive" in response.json()["detail"]

    def test_unauthorized_balance_add(self):
        response = client.post(
            "/auth/add-balance",
            json={"amount": 1000}
        )
        assert response.status_code == 401

    def test_multiple_balance_updates(self, auth_token):
        initial_profile = client.get(
            "/auth/profile",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        initial_balance = initial_profile.json()["balance"]

        first_response = client.post(
            "/auth/add-balance",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"amount": 1000}
        )
        assert first_response.status_code == 200
        assert first_response.json()["new_balance"] == initial_balance + 1000

        second_response = client.post(
            "/auth/add-balance",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"amount": 500}
        )
        assert second_response.status_code == 200
        assert second_response.json()["new_balance"] == initial_balance + 1500

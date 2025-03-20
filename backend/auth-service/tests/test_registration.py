from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.core.database import get_db
from models.user_model import User as UserModel

client = TestClient(app)


@pytest.mark.auth
@pytest.mark.registration
@pytest.mark.smoke
class TestRegistration:
    def test_successful_registration(self, test_user_data):
        with get_db() as db:
            db.query(UserModel).delete()
            db.commit()

        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == 200
        assert "id" in response.json()
        assert response.json()["email"] == test_user_data["email"]

    def test_duplicate_registration(self, test_user_data, registered_user):
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

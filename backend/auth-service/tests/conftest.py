import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from models.user_model import User as UserModel

client = TestClient(app)


@pytest.fixture(scope="function")
def clean_db():
    with get_db() as db:
        yield db
        db.query(UserModel).delete()
        db.commit()


@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User",
        "balance": 0
    }


@pytest.fixture
def registered_user(test_user_data, clean_db):
    response = client.post("/auth/register", json=test_user_data)
    return response.json()


@pytest.fixture
def auth_token(test_user_data, registered_user):
    response = client.post("/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    return response.json()["access_token"]

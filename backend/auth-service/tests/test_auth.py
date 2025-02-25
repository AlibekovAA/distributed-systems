from fastapi.testclient import TestClient

from app.main import app
from logger import log_time, logging

client = TestClient(app)


def register_test_user():
    logging.info(f"{log_time()} - Running test: register_test_user")
    return client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    })


def test_register():
    logging.info(f"{log_time()} - Running test: test_register")
    response = register_test_user()
    assert response.status_code == 200
    assert "id" in response.json()


def test_login():
    register_test_user()
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

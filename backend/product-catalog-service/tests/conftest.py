import pytest
import requests

BASE_URL = "http://localhost:7070"


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def test_product():
    product = {
        "name": "Test Product",
        "price": 100
    }
    yield product

    response = requests.get(f"{BASE_URL}/products")
    products = response.json()
    for p in products:
        if p["name"] == product["name"]:
            requests.delete(f"{BASE_URL}/products/{p['id']}")


@pytest.fixture
def test_user():
    user = {
        "id": 1,
        "balance": 500
    }
    yield user

    requests.post(f"{BASE_URL}/users/{user['id']}/balance/reset", json={"balance": 500})


@pytest.fixture
def clean_orders():
    yield
    requests.delete(f"{BASE_URL}/orders/1/all")


@pytest.fixture(autouse=True)
def setup_and_teardown():
    yield
    requests.post(f"{BASE_URL}/test/cleanup")

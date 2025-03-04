import pytest
import requests

BASE_URL = "http://localhost:7070"  

@pytest.fixture
def test_product():
    return {
        "name": "Test Product",
        "price": 100
    }

@pytest.fixture
def test_user():
    return {
        "id": 1,
        "balance": 500
    }

def test_get_products():
    response = requests.get(f"{BASE_URL}/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_product(test_product):
    response = requests.post(f"{BASE_URL}/products", json=test_product)
    assert response.status_code in [200, 201]  
    assert response.json()["name"] == test_product["name"]
    assert response.json()["price"] == test_product["price"]

def test_add_to_order():
    response = requests.post(f"{BASE_URL}/order/add", json={"user_id": 1, "product_id": 1})
    assert response.status_code == 200
    assert response.json()["message"] == "Product added to order"

def test_get_order():
    response = requests.get(f"{BASE_URL}/order/1")
    assert response.status_code == 200
    assert "products" in response.json()

def test_pay_for_order():
    response = requests.post(f"{BASE_URL}/order/1/pay")
    assert response.status_code == 200
    assert response.json()["message"] == "Order paid successfully"

def test_remove_from_order():
    response = requests.delete(f"{BASE_URL}/order/1/1")
    assert response.status_code == 200
    assert response.json()["message"] == "Product removed from order"

def test_get_balance():
    response = requests.get(f"{BASE_URL}/users/1/balance")
    assert response.status_code == 200
    assert "balance" in response.json()

def test_get_order_history():
    response = requests.get(f"{BASE_URL}/orders/1/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

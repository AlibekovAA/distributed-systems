import pytest
import requests


@pytest.mark.orders
def test_add_to_order(base_url, clean_orders):
    response = requests.post(f"{base_url}/order/add", json={"user_id": 1, "product_id": 1})
    assert response.status_code == 200
    assert response.json()["message"] == "Product added to order"


@pytest.mark.orders
def test_get_order(base_url, clean_orders):
    response = requests.get(f"{base_url}/order/1")
    assert response.status_code == 200
    assert "products" in response.json()


@pytest.mark.orders
def test_pay_for_order(base_url, clean_orders, test_user):
    response = requests.post(f"{base_url}/order/1/pay")
    assert response.status_code == 200
    assert response.json()["message"] == "Order paid successfully"


@pytest.mark.orders
def test_remove_from_order(base_url, clean_orders):
    response = requests.delete(f"{base_url}/order/1/1")
    assert response.status_code == 200
    assert response.json()["message"] == "Product removed from order"


@pytest.mark.orders
def test_get_order_history(base_url, clean_orders):
    response = requests.get(f"{base_url}/orders/1/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

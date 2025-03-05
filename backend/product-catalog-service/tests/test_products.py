import pytest
import requests


@pytest.mark.products
def test_get_products(base_url):
    response = requests.get(f"{base_url}/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.products
def test_create_product(base_url, test_product):
    response = requests.post(f"{base_url}/products", json=test_product)
    assert response.status_code in [200, 201]
    assert response.json()["name"] == test_product["name"]
    assert response.json()["price"] == test_product["price"]

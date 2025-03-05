import pytest
import requests


@pytest.mark.users
def test_get_balance(base_url, test_user):
    response = requests.get(f"{base_url}/users/1/balance")
    assert response.status_code == 200
    assert "balance" in response.json()

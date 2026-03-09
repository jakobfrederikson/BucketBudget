import pytest
from decimal import Decimal

def test_index(client):
    response = client.get("/")
    assert b"BucketBudget" in response.data


def test_read(client, auth):
    response = client.get("/budget/1")
    assert b'<a href="/auth/login">/auth/login</a>' in response.data

    auth.login()
    response = client.get("/budget/1")
    assert b'Total Weekly Income' in response.data
    assert b'Total Weekly Expenses' in response.data
    assert b'Total Weekly Net Income' in response.data
    assert b'test bucket' in response.data


@pytest.mark.parametrize("path", ("/budget/create", "/budget/1/update", "/budget/1/delete"))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"
import pytest


def test_index(client):
    response = client.get("/")
    assert b"BucketBudget" in response.data
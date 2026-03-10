import pytest
from decimal import Decimal

from bucketbudget.db import get_db

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


def test_create(client, auth, app):
    auth.login()
    assert client.get("/budget/create").status_code == 200
    client.post("/budget/create", data={"title": "created", "frequency": "Fortnightly"})
    
    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM budget").fetchone()[0]
        assert count == 2


def test_update(client, auth, app):
    auth.login()
    assert client.get("/budget/1/update").status_code == 200
    client.post("/budget/1/update", data={"title": "updated", "frequency": "Weekly"})
    
    with app.app_context():
        db = get_db()
        budget = db.execute("SELECT * FROM budget WHERE id  = 1").fetchone()
        assert budget["title"] == "updated"


@pytest.mark.parametrize("path", ("/budget/create", "/budget/1/update"))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={"title": "", "body": ""})
    assert response.status_code == 400


def test_delete(client, auth, app):
    auth.login()
    response = client.post("/budget/1/delete")
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM budget WHERE id = 1").fetchone()
        assert post is None


@pytest.mark.parametrize("path", ("/budget/create", "/budget/1/update", "/budget/1/delete"))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"
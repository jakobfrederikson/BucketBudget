import pytest
from sqlalchemy import text
from bucketbudget.auth.models import User, Role
from bucketbudget import create_app, db
import os


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # create the app with common test config
    app = create_app({
        "TESTING": True, 
        "SQLALCHEMY_DATABASE_URI": 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECURITY_PASSWORD_SALT': 'test',
        'SECURITY_PASSWORD_HASH': 'plaintext',
        'MAIL_BACKEND': 'locmem',
    })

    # create the database and load test data
    with app.app_context():
        db.create_all()

        sql_file_path = os.path.join(os.path.dirname(__file__), "data.sql")
        if os.path.exists(sql_file_path):
            with open(sql_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                db.engine.raw_connection().executescript(content)

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, email="test@test.com", username="testuser", password="testpassword"):
        return self._client.post(
            "/auth/login", data={"email": email, "username": username, "password": password}
        )

    def logout(self):
        return self._client.get("/auth/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
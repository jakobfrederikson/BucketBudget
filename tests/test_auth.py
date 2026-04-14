import pytest
from flask_security import current_user
from bucketbudget import db
from bucketbudget.auth.models import User


def test_register(client, app):
    # test that viewing the page renders without template errors
    assert client.get("/auth/register").status_code == 200

    # test that successful registration redirects to the login page
    response = client.post("/auth/register", data={
        "email": "abc@123.com",
        "username": "abc", 
        "password": "abc123password",
        "password_confirm": "abc123password"
    })
    assert response.headers["Location"] == "/auth/login"

    # test that the user was inserted into the database
    with app.app_context():
        user = User.query.filter_by(email="abc@123.com").first_or_404()
        assert user is not None
        assert user.email == "abc@123.com"


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (
        ("", "", b"Username is required."),
        ("a", "", b"Password is required."),
        ("test", "test", b"already registered"),
    ),
)
def test_register_validate_input(client, username, password, message):
    response = client.post(
        "/auth/register", data={"username": username, "password": password}
    )
    assert message in response.data


def test_login(client, auth):
    # test that viewing the page renders without template errors
    assert client.get("/auth/login").status_code == 200

    # test that successful login redirects to the index page
    response = auth.login(email="test@test.com", password="testpassword")
    assert response.headers["Location"] == "/"

    # login request set the user_id in the session
    # check that the user is loaded from the session
    with client:
        client.get("/")
        from flask_security import current_user
        assert current_user.is_authenticated
        assert current_user.email == "test@test.com"


@pytest.mark.parametrize(
    ("username", "email", "password", "message"),
    (
        ("t3st", "test@test.com", "testpassword", b"Incorrect username."), 
        ("test", "test@test.com", "t3stpassword", b"Incorrect password.")
    ),
)
def test_login_validate_input(auth, username, email, password, message):
    response = auth.login(username=username, email=email, password=password)
    assert message in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        client.get("/")
        from flask_security import current_user
        assert not current_user.is_authenticated
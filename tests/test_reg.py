from fastapi.testclient import TestClient
import os
import sys

sys.path.insert(1, os.getcwd())
from app.main import app


# _____________Tesing User Registration_____________

client = TestClient(app)


# Register a user using a unique username and email, and test that response is a success
def test_register_success():
    response = client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongP@ss123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login")


# Register with an valid email and username but use an invalid password
def test_invalid_password1():
    response = client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "1",
        },  # Password length < 8 characters
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert "Password must be at least 8 characters" in response.json()["detail"]


# Register with an valid email and username but use an invalid password
def test_invalid_password2():
    response = client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "aaaaaaaa1",
        },  # Password doesn't have uppercase letter
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert "Password must include an uppercase letter." in response.json()["detail"]


# Register with an valid email and username but use an invalid password
def test_invalid_password3():
    response = client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "Aaaaaaaa",
        },  # Password doesn't have a number
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert "Password must include a number." in response.json()["detail"]


# Register with an valid email and username but use an invalid password
def test_invalid_password4():
    response = client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "AAAAAAAA8",
        },  # Password doesn't have a lowercase letter
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert "Password must include a lowercase letter." in response.json()["detail"]


# Register with an already existing username, and test that response is unsuccessful
def test_invalid_username():
    response = client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "unique1@example.com",
            "password": "AAAAAAAa8",
        },
        follow_redirects=False,
    )

    response = client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "unique2@example.com",  # different email
            "password": "AAAAAAAa8",
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert "Either username or email has already been used!" in response.text


# Register with an already existing username, and test that response is unsuccessful
def test_invalid_email():
    response = client.post(
        "/register",
        data={
            "username": "testuser1",
            "email": "test@example.com",
            "password": "AAAAAAAa8",
        },
        follow_redirects=False,
    )

    response = client.post(
        "/register",
        data={
            "username": "testuser2",  # different username
            "email": "test@example.com",
            "password": "AAAAAAAa8",
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert "Either username or email has already been used!" in response.text

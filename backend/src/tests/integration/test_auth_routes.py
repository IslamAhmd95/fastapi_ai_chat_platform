import pytest


@pytest.fixture
def user_data():
    return {
        "email": "newuser@example.com",
        "username": "newuser",
        "name": "New User",
        "password": "password123",
        "recaptcha_token": "test-token-no-verification"
    }


def test_register_creates_user_successfully(client, user_data):

    response = client.post("/auth/register", json=user_data)

    assert response.status_code == 201
    assert "Account created successfully" in response.json()["message"]
    assert response.json()["user"]["email"] == user_data["email"]
    assert response.json()["user"]["username"] == user_data["username"]
    assert response.json()["user"]["name"] == user_data["name"]


def test_register_fails_with_duplicate_email(client, user_data):

    client.post("/auth/register", json=user_data)

    user_data["username"] = "newuser2"
    response = client.post("/auth/register", json=user_data)

    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_register_fails_with_duplicate_username(client, user_data):

    client.post("/auth/register", json=user_data)

    user_data["email"] = "newuser2@example.com"
    response = client.post("/auth/register", json=user_data)

    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


def test_register_fails_with_invalid_email(client):

    user_data = {
        "email": "notanemail",
        "username": "user",
        "name": "User",
        "password": "password123",
        "recaptcha_token": "test-token-no-verification"
    }

    response = client.post("/auth/register", json=user_data)

    assert response.status_code == 422


def test_login_with_email_returns_token(client, user_data):

    client.post("/auth/register", json=user_data)

    login_data = {
        "login": "newuser@example.com",
        "password": "password123",
        "recaptcha_token": "test-token-no-verification"
    }
    response = client.post("/auth/login", json=login_data)

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newuser@example.com"


def test_login_with_username_returns_token(client, user_data):

    client.post("/auth/register", json=user_data)

    login_data = {
        "login": "newuser",
        "password": "password123",
        "recaptcha_token": "test-token-no-verification"
    }
    response = client.post("/auth/login", json=login_data)

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "newuser"


def test_login_fails_with_wrong_password(client):

    user_data = {
        "email": "user@example.com",
        "username": "testuser",
        "name": "Test User",
        "password": "correctpassword",
        "recaptcha_token": "test-token-no-verification"
    }
    client.post("/auth/register", json=user_data)

    login_data = {
        "login": "user@example.com",
        "password": "wrongpassword",
        "recaptcha_token": "test-token-no-verification"
    }
    response = client.post("/auth/login", json=login_data)

    assert response.status_code == 403
    assert "Incorrect password" in response.json()["detail"]


def test_login_fails_with_nonexistent_user(client):

    login_data = {
        "login": "nonexistent@example.com",
        "password": "password123",
        "recaptcha_token": "test-token-no-verification"
    }
    response = client.post("/auth/login", json=login_data)

    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

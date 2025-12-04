from fastapi import HTTPException
import pytest

from src.models.user import User
from src.repositories import auth_repository
from src.schemas.auth_schema import LoginSchema, SignUpSchema


@pytest.fixture
def signup_data():
    return SignUpSchema(
        email="newuser@example.com",
        username="newuser",
        name="New User",
        password="password123"
    )

def test_signup_creates_user_in_database(test_db, signup_data):

    user = auth_repository.signup(signup_data, test_db)

    assert isinstance(user, User)
    assert user.id is not None
    assert user.password != "password123"


def test_signup_hashes_password(test_db, signup_data):

    user = auth_repository.signup(signup_data, test_db)

    assert user.password != "password123"
    assert len(user.password) > 20


def test_signup_raises_error_when_email_exists(test_db, signup_data):
    auth_repository.signup(signup_data, test_db)

    with pytest.raises(HTTPException) as error:
        auth_repository.signup(signup_data, test_db)

    assert error.value.status_code == 400
    assert error.value.detail == "Email already registered"


def test_signup_raises_error_when_username_exists(test_db, signup_data):
    auth_repository.signup(signup_data, test_db)

    with pytest.raises(HTTPException) as error:
        auth_repository.signup(
            SignUpSchema(
                email="user@example.com",
                username="newuser",
                name="New User",
                password="password123"
            )
            , test_db)

    assert error.value.status_code == 400
    assert error.value.detail == "Username already registered"


def test_login_with_email_returns_user_and_token(test_db, signup_data):
    auth_repository.signup(signup_data, test_db)

    login_data = LoginSchema(
        login="newuser@example.com",
        password="password123"
    )

    user, access_token = auth_repository.login(login_data, test_db)

    assert user.email == "newuser@example.com"
    assert user.username == "newuser"
    assert isinstance(access_token, str)
    assert len(access_token) > 20 


def test_login_with_username_returns_user_and_token(test_db, signup_data):

    auth_repository.signup(signup_data, test_db)
    
    login_data = LoginSchema(
        login="newuser", 
        password="password123"
    )
    
    user, access_token = auth_repository.login(login_data, test_db)
    
    assert user.username == "newuser"
    assert user.email == "newuser@example.com"
    assert isinstance(access_token, str) 
    assert len(access_token) > 20 


def test_login_raises_error_when_user_not_found(test_db):
    login_data = LoginSchema(
        login="newuser", 
        password="password123"
    )
    
    with pytest.raises(HTTPException) as error:
        auth_repository.login(login_data, test_db)

    assert error.value.status_code == 404
    assert "User not found" in error.value.detail


def test_login_raises_error_when_password_wrong(test_db, signup_data):
    
    auth_repository.signup(signup_data, test_db)
    
    login_data = LoginSchema(
        login="newuser@example.com",
        password="wrongpassword"
    )
    
    with pytest.raises(HTTPException) as error:
        auth_repository.login(login_data, test_db)
    
    assert error.value.status_code == 403
    assert "Incorrect password" in error.value.detail


def test_login_token_contains_user_email(test_db, signup_data):
    auth_repository.signup(signup_data, test_db)
    
    login_data = LoginSchema(
        login="newuser", 
        password="password123"
    )
    
    access_token = auth_repository.login(login_data, test_db)[1]

    import jwt
    decoded = jwt.decode(access_token, options={"verify_signature": False})
    assert decoded["sub"] == "newuser@example.com"
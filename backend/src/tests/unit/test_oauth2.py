import pytest

from fastapi import HTTPException
from unittest.mock import AsyncMock

from src.core.token import create_access_token
from src.models.user import User
from src.core.oauth2 import get_current_user, authenticate_websocket



def test_get_current_user_returns_user_when_valid(mocker, sample_user):

    token = create_access_token({"sub": "test@example.com"})

    fake_db = mocker.Mock()
    fake_db.scalar.return_value = sample_user

    result = get_current_user(token, fake_db)

    assert isinstance(result, User)
    assert result.email == sample_user.email
    fake_db.scalar.assert_called_once()


def test_get_current_user_raises_error_when_user_not_found(mocker):
    token = create_access_token({"sub": "test@example.com"})

    fake_db = mocker.Mock()
    fake_db.scalar.return_value = None

    with pytest.raises(HTTPException) as error:
        get_current_user(token, fake_db)

    assert error.value.status_code == 401
    assert error.value.detail == "Could not validate credentials"


def test_get_current_user_raises_error_when_token_invalid(mocker):    
    invalid_token = "this.is.an.invalid.token"

    fake_db = mocker.Mock()
    with pytest.raises(HTTPException) as error:
        get_current_user(invalid_token, fake_db)

    assert error.value.status_code == 401
    assert error.value.detail == "Could not validate credentials"


def test_get_current_user_raises_error_when_token_expired(mocker):
    from datetime import timedelta
    expired_token = create_access_token(
        {'sub': 'test@example.com'},
        expires_delta=timedelta(seconds=-1)
    )

    fake_db = mocker.Mock()
    with pytest.raises(HTTPException) as error:
        get_current_user(expired_token, fake_db)

    assert error.value.status_code == 401
    assert error.value.detail == "Token has expired"


@pytest.mark.asyncio
async def test_websocket_returns_token_data_when_valid():
    token = create_access_token({"sub": "test@example.com"})
    
    fake_websocket = AsyncMock()
    fake_websocket.query_params = {"token": token}
    result = await authenticate_websocket(fake_websocket)

    assert result is not None
    assert result.email == "test@example.com"
    fake_websocket.close.assert_not_called()  # It confirms that during the entire test run, the .close() method was NEVER executed on the fake_websocket object.


@pytest.mark.asyncio
async def test_websocket_closes_when_no_token():
    fake_websocket = AsyncMock()
    fake_websocket.query_params = {}  
    
    result = await authenticate_websocket(fake_websocket)
    
    assert result is None
    fake_websocket.close.assert_called_once()  # Should close connection


@pytest.mark.asyncio
async def test_websocket_closes_when_token_invalid():
    token = "this.is.an.invalid.token"
    
    fake_websocket = AsyncMock()
    fake_websocket.query_params = {"token": token}
    result = await authenticate_websocket(fake_websocket)

    assert result is None
    fake_websocket.close.assert_called_once()
from datetime import datetime, timedelta, timezone

import jwt
from freezegun import freeze_time

from src.tests.conftest import TEST_ALGORITHM, TEST_SECRET_KEY, TEST_TOKEN_EXPIRE_MINUTES
from src.core.token import create_access_token


def test_create_token_returns_string():
    data = {'sub': 'test@example.com'}
    token = create_access_token(data)

    assert isinstance(token, str)
    assert len(token) > 0


def test_token_contains_email():
    data = {'sub': 'test@example.com'}
    token = create_access_token(data)

    decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])

    assert decoded['sub'] == data['sub']


@freeze_time("2025-11-30 10:00:00") 
def test_token_has_correct_expiration():

    data = {'sub': 'test@example.com'}
    token = create_access_token(data) 

    frozen_datetime = datetime(2025, 11, 30, 10, 0, 0, tzinfo=timezone.utc)
    expected_datetime = frozen_datetime + timedelta(minutes=TEST_TOKEN_EXPIRE_MINUTES)
    
    expected_exp_timestamp = int(expected_datetime.timestamp()) 
    
    decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])

    assert 'exp' in decoded
    assert decoded['exp'] == expected_exp_timestamp
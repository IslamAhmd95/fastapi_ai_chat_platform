import pytest
from pwdlib import PasswordHash

from src.core.hashing import hash_password, verify_password

password_hash = PasswordHash.recommended()


@pytest.fixture(params=["password", "1234!@#$"])
def plain_password(request):
    return request.param

def test_hash_password(plain_password):
    hashed = hash_password(plain_password)
    assert password_hash.verify(plain_password, hashed)


def test_verify_password(plain_password):
    hashed_password = password_hash.hash(plain_password)
    assert verify_password(plain_password, hashed_password) is True

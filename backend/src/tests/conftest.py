import pytest
from fastapi.testclient import TestClient

from src.models.user import User

from main import app


TEST_SECRET_KEY = "testsecret"
TEST_ALGORITHM = "HS256"
TEST_TOKEN_EXPIRE_MINUTES = 30


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    monkeypatch.setattr("src.core.token.SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setattr("src.core.token.ALGORITHM", TEST_ALGORITHM)
    monkeypatch.setattr("src.core.token.ACCESS_TOKEN_EXPIRE_MINUTES", TEST_TOKEN_EXPIRE_MINUTES)


@pytest.fixture
def sample_user():
    return User(
        id=1,
        email="test@example.com",
        username="IslamAhmd",
        name="Islam Ahmed",
        password="password123"
    )


@pytest.fixture(scope="function")
def test_db():
    from sqlmodel import Session, create_engine, SQLModel

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    SQLModel.metadata.create_all(engine)

    with Session(engine) as db:
        yield db

    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client():
    return TestClient(app)
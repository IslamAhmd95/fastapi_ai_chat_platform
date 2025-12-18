import pytest

from src.core.config import settings
from src.models.chat_history import ChatHistory
from src.core.enums import AIModels


@pytest.fixture
def authenticated_user(client, test_db):
    from src.models.user import User
    from src.core.hashing import hash_password

    user = User(
        email="chatuser@example.com",
        username="chatuser",
        name="Chat User",
        password=hash_password("password123")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    response = client.post("/auth/login", json={
        "login": "chatuser@example.com",
        "password": "password123",
        "recaptcha_token": "test-token-no-verification"
    })

    assert response.status_code == 200, response.json()
    token = response.json()["access_token"]

    return user, token


def test_get_platforms_returns_all_models(client):

    response = client.get("/ai/platforms")

    assert response.status_code == 200
    data = response.json()
    assert "platforms" in data
    assert isinstance(data["platforms"], list)
    assert len(data["platforms"]) > 0


def test_get_platforms_includes_gemini(client):

    response = client.get("/ai/platforms")

    platforms = response.json()["platforms"]
    assert AIModels.GEMINI.value in platforms


def test_get_platforms_includes_groq(client):

    response = client.get("/ai/platforms")

    platforms = response.json()["platforms"]
    assert AIModels.GROQ.value in platforms


def test_get_chat_history_requires_authentication(client):

    response = client.get(
        f"/ai/chat-history?model_name={AIModels.GEMINI.value}")

    assert response.status_code == 401


def test_get_chat_history_returns_user_chats(client, test_db, authenticated_user):
    user, access_token = authenticated_user

    chat1 = ChatHistory(
        user_id=user.id,
        prompt="Hello",
        response="Hi there!",
        model_name=AIModels.GEMINI
    )
    chat2 = ChatHistory(
        user_id=user.id,
        prompt="How are you?",
        response="I'm doing well!",
        model_name=AIModels.GEMINI
    )
    test_db.add(chat1)
    test_db.add(chat2)
    test_db.commit()

    response = client.get(f'/ai/chat-history?model_name={AIModels.GEMINI.value}',
                          headers={"Authorization": f"Bearer {access_token}"}
                          )

    assert response.status_code == 200
    data = response.json()
    assert "chat" in data
    assert len(data["chat"]) == 2
    assert "usage_info" in data


def test_get_chat_history_filters_by_model(client, test_db, authenticated_user):

    user, token = authenticated_user

    gemini_chat = ChatHistory(
        user_id=user.id,
        prompt="Gemini prompt",
        response="Gemini response",
        model_name=AIModels.GEMINI
    )
    groq_chat = ChatHistory(
        user_id=user.id,
        prompt="Groq prompt",
        response="Groq response",
        model_name=AIModels.GROQ
    )
    test_db.add(gemini_chat)
    test_db.add(groq_chat)
    test_db.commit()

    response = client.get(
        f"/ai/chat-history?model_name={AIModels.GEMINI.value}",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = response.json()
    print(data['chat'])
    assert len(data["chat"]) == 1
    assert data["chat"][0]["model_name"] == AIModels.GEMINI.value


def test_get_chat_history_returns_empty_when_no_chats(client, authenticated_user):

    user, token = authenticated_user

    response = client.get(
        f"/ai/chat-history?model_name={AIModels.GEMINI.value}",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = response.json()
    assert data["chat"] == []


def test_get_chat_history_only_returns_own_chats(client, test_db, authenticated_user):
    from src.models.user import User
    from src.core.hashing import hash_password

    user, token = authenticated_user

    other_user = User(
        email="other@example.com",
        username="otheruser",
        name="Other User",
        password=hash_password("password123")
    )
    test_db.add(other_user)
    test_db.commit()
    test_db.refresh(other_user)

    other_chat = ChatHistory(
        user_id=other_user.id or 0,
        prompt="Other user's chat",
        response="Response",
        model_name=AIModels.GEMINI
    )
    test_db.add(other_chat)
    test_db.commit()

    response = client.get(
        f"/ai/chat-history?model_name={AIModels.GEMINI.value}",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = response.json()
    assert len(data["chat"]) == 0


def test_get_chat_history_includes_usage_info(client, test_db, authenticated_user, monkeypatch):
    """Chat history response should include usage_info with correct remaining/limit."""
    user, token = authenticated_user

    # Mock the AI usage limit so the test doesn't depend on real env/config
    mocked_limit = 5
    monkeypatch.setattr(settings, "AI_USAGE_LIMIT", mocked_limit)

    # Persist custom ai_requests_count in the test database
    user.ai_requests_count = 2
    user.is_unlimited = False
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    response = client.get(
        f"/ai/chat-history?model_name={AIModels.GEMINI.value}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "usage_info" in data
    assert "remaining_requests" in data["usage_info"]
    assert "limit" in data["usage_info"]
    assert data["usage_info"]["limit"] == mocked_limit
    assert data["usage_info"]["remaining_requests"] == mocked_limit - \
        user.ai_requests_count


def test_chat_endpoint_enforces_usage_limit(client, test_db, authenticated_user, monkeypatch):
    """Test that HTTP POST /ai/chat endpoint enforces usage limit"""
    from unittest.mock import patch

    user, token = authenticated_user

    # Mock limit so test does not depend on env
    mocked_limit = 7
    monkeypatch.setattr(settings, "AI_USAGE_LIMIT", mocked_limit)

    # Set user to mocked limit
    user.ai_requests_count = mocked_limit
    user.is_unlimited = False
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    with patch('src.repositories.chat_repository.get_ai_platform'):
        response = client.post(
            "/ai/chat",
            json={
                "model_name": AIModels.GEMINI.value,
                "prompt": "Test prompt"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert "usage limit reached" in response.json()["detail"].lower()


def test_chat_endpoint_returns_remaining_requests(client, test_db, authenticated_user, monkeypatch):
    """Test that HTTP POST /ai/chat endpoint returns remaining_requests"""
    from unittest.mock import Mock, patch

    user, token = authenticated_user

    # Mock limit so test does not depend on env
    mocked_limit = 10
    monkeypatch.setattr(settings, "AI_USAGE_LIMIT", mocked_limit)

    # Set user to have 5 requests used (leaving mocked_limit - 5 remaining before call)
    user.ai_requests_count = 5
    user.is_unlimited = False
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    with patch('src.repositories.chat_repository.get_ai_platform') as mock_platform:
        mock_ai = Mock()
        mock_ai.chat.return_value = "AI Response"
        mock_platform.return_value = mock_ai

        response = client.post(
            "/ai/chat",
            json={
                "model_name": AIModels.GEMINI.value,
                "prompt": "Test prompt"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "remaining_requests" in data
        # After successful call, counter increments by 1 → total used = 6
        expected_remaining = mocked_limit - (user.ai_requests_count + 1)
        assert data["remaining_requests"] == expected_remaining


def test_unlimited_user_bypasses_limit(client, test_db, authenticated_user):
    """Test that unlimited users can exceed the normal limit"""
    from unittest.mock import Mock, patch

    user, token = authenticated_user

    # Set user as unlimited with high count
    user.ai_requests_count = 50
    user.is_unlimited = True
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    with patch('src.repositories.chat_repository.get_ai_platform') as mock_platform:
        mock_ai = Mock()
        mock_ai.chat.return_value = "AI Response"
        mock_platform.return_value = mock_ai

        response = client.post(
            "/ai/chat",
            json={
                "model_name": AIModels.GEMINI.value,
                "prompt": "Test prompt"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "remaining_requests" in data
        assert data["remaining_requests"] == -1  # -1 indicates unlimited

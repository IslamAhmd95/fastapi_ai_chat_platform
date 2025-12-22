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


def test_get_platforms_includes_groq(client):

    response = client.get("/ai/platforms")

    platforms = response.json()["platforms"]
    assert AIModels.GROQ.value in platforms


def test_get_chat_history_requires_authentication(client):

    response = client.get(
        f"/ai/chat-history?model_name={AIModels.GROQ.value}")

    assert response.status_code == 401


def test_get_chat_history_returns_user_chats(client, test_db, authenticated_user):
    user, access_token = authenticated_user

    chat2 = ChatHistory(
        user_id=user.id,
        prompt="How are you?",
        response="I'm doing well!",
        model_name=AIModels.GROQ
    )
    test_db.add(chat2)
    test_db.commit()

    response = client.get(f'/ai/chat-history?model_name={AIModels.GROQ.value}',
                          headers={"Authorization": f"Bearer {access_token}"}
                          )

    assert response.status_code == 200
    data = response.json()
    assert "chat" in data
    assert len(data["chat"]) == 1
    assert "usage_info" in data


def test_get_chat_history_filters_by_model(client, test_db, authenticated_user):

    user, token = authenticated_user

    groq_chat = ChatHistory(
        user_id=user.id,
        prompt="Groq prompt",
        response="Groq response",
        model_name=AIModels.GROQ
    )
    test_db.add(groq_chat)
    test_db.commit()

    response = client.get(
        f"/ai/chat-history?model_name={AIModels.GROQ.value}",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = response.json()
    print(data['chat'])
    assert len(data["chat"]) == 1
    assert data["chat"][0]["model_name"] == AIModels.GROQ.value


def test_get_chat_history_returns_empty_when_no_chats(client, authenticated_user):

    user, token = authenticated_user

    response = client.get(
        f"/ai/chat-history?model_name={AIModels.GROQ.value}",
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
        model_name=AIModels.GROQ
    )
    test_db.add(other_chat)
    test_db.commit()

    response = client.get(
        f"/ai/chat-history?model_name={AIModels.GROQ.value}",
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
        f"/ai/chat-history?model_name={AIModels.GROQ.value}",
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


@pytest.mark.parametrize("mocked_model", [AIModels.GEMINI])
def test_unavailable_model(client, authenticated_user, mocked_model):
    from unittest.mock import patch, AsyncMock
    user, token = authenticated_user

    # Patch the ratelimit instance in the chat module
    with patch("src.api.chat.ratelimit", new_callable=AsyncMock) as mock_limit:
        
        with patch("src.repositories.chat_repository.is_provider_available") as mock_avail:
            mock_avail.return_value = False

            with client.websocket_connect(f"/ai/ws/chat?token={token}") as websocket:
                websocket.send_json({"model_name": mocked_model.value, "prompt": "Hello"})
                response = websocket.receive_json()
                assert response["error"] == "This AI provider is currently unavailable due to free-tier limits."
                mock_avail.assert_called_once_with(mocked_model)


def test_chat_endpoint_enforces_usage_limit(client, test_db, authenticated_user, monkeypatch):
    
    from unittest.mock import Mock, patch, AsyncMock

    user, token = authenticated_user

    with patch("src.api.chat.ratelimit", new_callable=AsyncMock):
        
        mocked_limit = 7
        monkeypatch.setattr(settings, "AI_USAGE_LIMIT", mocked_limit)

        user.ai_requests_count = mocked_limit
        user.is_unlimited = False
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        with patch('src.repositories.chat_repository.get_ai_platform') as mock_platform:
            mock_ai = Mock()
            mock_ai.chat.return_value = "AI Response"
            mock_platform.return_value = mock_ai

            # Connect via WebSocket with token
            with client.websocket_connect(f"/ai/ws/chat?token={token}") as websocket:
                # Send message
                websocket.send_json({
                    "model_name": AIModels.GROQ.value,
                    "prompt": "Test prompt"
                })
                
                # Should receive error about limit
                response = websocket.receive_json()
                
                assert "error" in response
                assert "usage limit reached" in response["error"].lower()


def test_chat_endpoint_returns_remaining_requests(client, test_db, authenticated_user, monkeypatch):
    from unittest.mock import Mock, patch, AsyncMock

    user, token = authenticated_user

    with patch("src.api.chat.ratelimit", new_callable=AsyncMock):

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

            # Connect via WebSocket
            with client.websocket_connect(f"/ai/ws/chat?token={token}") as websocket:
                # Send message
                websocket.send_json({
                    "model_name": AIModels.GROQ.value,
                    "prompt": "Test prompt"
                })
                
                response = websocket.receive_json()
                
                assert "remaining_requests" in response
                assert "response" in response
                assert response["response"] == "AI Response"
                
                expected_remaining = mocked_limit - (5 + 1)
                assert response["remaining_requests"] == expected_remaining


def test_unlimited_user_bypasses_limit(client, test_db, authenticated_user):
    
    from unittest.mock import Mock, patch, AsyncMock

    user, token = authenticated_user

    # Set user as unlimited with high count
    user.ai_requests_count = 50
    user.is_unlimited = True
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    with patch("src.api.chat.ratelimit", new_callable=AsyncMock):

        with patch('src.repositories.chat_repository.get_ai_platform') as mock_platform:
            mock_ai = Mock()
            mock_ai.chat.return_value = "AI Response"
            mock_platform.return_value = mock_ai

            # Connect via WebSocket
            with client.websocket_connect(f"/ai/ws/chat?token={token}") as websocket:
                # Send message
                websocket.send_json({
                    "model_name": AIModels.GROQ.value,
                    "prompt": "Test prompt"
                })
                
                response = websocket.receive_json()
                
                assert "remaining_requests" in response
                assert response["remaining_requests"] == -1  # -1 means unlimited
                assert response["response"] == "AI Response"


def test_successful_chat_flow(client, test_db, authenticated_user):
    """Test complete successful chat interaction"""
    from unittest.mock import Mock, patch, AsyncMock

    user, token = authenticated_user
    
    # Reset user's request count
    user.ai_requests_count = 0
    user.is_unlimited = False
    test_db.add(user)
    test_db.commit()
    
    with patch("src.api.chat.ratelimit", new_callable=AsyncMock):

        with patch('src.repositories.chat_repository.get_ai_platform') as mock_platform:
            mock_ai = Mock()
            mock_ai.chat.return_value = "Hello! How can I help you?"
            mock_platform.return_value = mock_ai
            
            with client.websocket_connect(f"/ai/ws/chat?token={token}") as websocket:
                # Send message
                websocket.send_json({
                    "model_name": AIModels.GROQ.value,
                    "prompt": "Hello AI"
                })
                
                # Receive response
                response = websocket.receive_json()
                
                # Verify response structure
                assert "prompt" in response
                assert "response" in response
                assert "created_at" in response
                assert "model_name" in response
                assert "remaining_requests" in response
                
                assert response["prompt"] == "Hello AI"
                assert response["response"] == "Hello! How can I help you?"
                assert response["model_name"] == AIModels.GROQ.value
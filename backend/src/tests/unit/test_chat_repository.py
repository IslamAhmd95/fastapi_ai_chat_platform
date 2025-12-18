from fastapi import HTTPException
import pytest
from unittest.mock import Mock, patch

from src.models.chat_history import ChatHistory
from src.core.enums import AIModels
from src.schemas.chat_schema import WebSocketMessage
from src.repositories import chat_repository


@pytest.fixture
def chat_user(sample_user):
    return sample_user


@pytest.fixture
def websocket_message():
    """Sample WebSocket message"""
    return WebSocketMessage(
        prompt="Hello, AI!",
        model_name=AIModels.GEMINI
    )


def test_generate_model_response_saves_to_database(test_db, chat_user, websocket_message):
    # Initialize user fields
    chat_user.ai_requests_count = 0
    chat_user.is_unlimited = False
    test_db.add(chat_user)
    test_db.commit()
    test_db.refresh(chat_user)
    
    with patch('src.repositories.chat_repository.get_ai_platform') as mock_platform:
        mock_ai = Mock()
        mock_ai.chat.return_value = "Hello! How can I help you?"
        mock_platform.return_value = mock_ai

        chat_record, remaining = chat_repository.generate_model_response(
            websocket_message, 
            chat_user, 
            test_db
        )
        
        assert isinstance(chat_record, ChatHistory)
        assert chat_record.prompt == "Hello, AI!"
        assert chat_record.response == "Hello! How can I help you?"
        assert chat_record.model_name == AIModels.GEMINI
        assert chat_record.user_id == chat_user.id
        assert isinstance(remaining, int)
        assert remaining >= 0


def test_generate_model_response_calls_correct_ai_platform(test_db, chat_user):
    chat_user.ai_requests_count = 0
    chat_user.is_unlimited = False
    test_db.add(chat_user)
    test_db.commit()
    test_db.refresh(chat_user)
    
    gemini_message = WebSocketMessage(
        prompt="Test Prompt",
        model_name=AIModels.GEMINI
    )

    with patch('src.repositories.chat_repository.get_ai_platform') as mock_platform:
        mock_ai = Mock()
        mock_ai.chat.return_value = "Response"
        mock_platform.return_value = mock_ai

        chat_repository.generate_model_response(
            gemini_message, 
            chat_user, 
            test_db
        )

        mock_platform.assert_called_once_with(AIModels.GEMINI)


def test_generate_model_response_raises_error_when_ai_fails(test_db, chat_user, websocket_message):
    chat_user.ai_requests_count = 0
    chat_user.is_unlimited = False
    test_db.add(chat_user)
    test_db.commit()
    test_db.refresh(chat_user)
    
    with patch('src.repositories.chat_repository.get_ai_platform') as mock_platform:
        mock_ai = Mock()
        mock_ai.chat.side_effect = Exception("API key invalid")
        mock_platform.return_value = mock_ai

        with pytest.raises(HTTPException) as exc_info:
            chat_repository.generate_model_response(
                websocket_message, 
                chat_user, 
                test_db
            )
        
        assert exc_info.value.status_code == 500
        assert "AI platform error" in exc_info.value.detail


def test_get_chat_history_returns_user_chats(test_db, chat_user):
    chat1 = ChatHistory(
        user_id=chat_user.id,
        prompt="First prompt",
        response="First response",
        model_name=AIModels.GEMINI
    )
    chat2 = ChatHistory(
        user_id=chat_user.id,
        prompt="Second prompt",
        response="Second response",
        model_name=AIModels.GEMINI
    )

    test_db.add(chat1)
    test_db.add(chat2)
    test_db.commit()

    result = chat_repository.get_chat_history(AIModels.GEMINI, chat_user, test_db)

    assert len(result) == 2
    assert result[0].prompt == "First prompt"
    assert result[1].prompt == "Second prompt"


def test_get_chat_history_filters_by_model_name(test_db, chat_user):
    """Test that get_chat_history only returns chats for specified model"""
    
    # Create chats for different models
    gemini_chat = ChatHistory(
        user_id=chat_user.id,
        prompt="Gemini prompt",
        response="Gemini response",
        model_name=AIModels.GEMINI
    )
    
    groq_chat = ChatHistory(
        user_id=chat_user.id,
        prompt="Groq prompt",
        response="Groq response",
        model_name=AIModels.GROQ
    )
    
    test_db.add(gemini_chat)
    test_db.add(groq_chat)
    test_db.commit()
    
    result = chat_repository.get_chat_history(AIModels.GEMINI, chat_user, test_db)
    
    assert len(result) == 1
    assert result[0].model_name == AIModels.GEMINI


def test_get_chat_history_returns_empty_for_no_chats(test_db, chat_user):
    
    result = chat_repository.get_chat_history(AIModels.GEMINI, chat_user, test_db)
    
    assert result == []


def test_get_chat_history_only_returns_current_user_chats(test_db, chat_user):
    from src.models.user import User
    
    other_user = User(
        id=999,
        email="other@example.com",
        username="otheruser",
        name="Other User",
        password="password123"
    )
    test_db.add(other_user)
    test_db.commit()
    
    other_chat = ChatHistory(
        user_id=other_user.id,
        prompt="Other user prompt",
        response="Other user response",
        model_name=AIModels.GEMINI
    )
    test_db.add(other_chat)
    test_db.commit()
    
    result = chat_repository.get_chat_history(AIModels.GEMINI, chat_user, test_db)
    
    assert len(result) == 0


def test_check_usage_limit_allows_when_under_limit(test_db, chat_user, monkeypatch):
    """Test that check_usage_limit allows requests when under limit"""
    mocked_limit = 10
    monkeypatch.setattr("src.core.config.settings.AI_USAGE_LIMIT", mocked_limit)

    chat_user.ai_requests_count = 5
    chat_user.is_unlimited = False
    
    allowed, remaining = chat_repository.check_usage_limit(chat_user)
    
    assert allowed is True
    # remaining = limit - used
    assert remaining == mocked_limit - chat_user.ai_requests_count


def test_check_usage_limit_rejects_when_limit_reached(test_db, chat_user, monkeypatch):
    """Test that check_usage_limit rejects when limit is reached"""
    mocked_limit = 10
    monkeypatch.setattr("src.core.config.settings.AI_USAGE_LIMIT", mocked_limit)

    chat_user.ai_requests_count = mocked_limit
    chat_user.is_unlimited = False
    
    allowed, remaining = chat_repository.check_usage_limit(chat_user)
    
    assert allowed is False
    assert remaining == 0


def test_check_usage_limit_allows_unlimited_users(test_db, chat_user):
    """Test that unlimited users bypass the limit"""
    chat_user.ai_requests_count = 100  # Way over limit
    chat_user.is_unlimited = True
    
    allowed, remaining = chat_repository.check_usage_limit(chat_user)
    
    assert allowed is True
    assert remaining == -1  # -1 indicates unlimited


def test_generate_model_response_increments_counter(test_db, chat_user, websocket_message):
    """Test that ai_requests_count is incremented after successful AI response"""
    chat_user.ai_requests_count = 3
    chat_user.is_unlimited = False
    test_db.add(chat_user)
    test_db.commit()
    test_db.refresh(chat_user)
    
    initial_count = chat_user.ai_requests_count
    
    with patch('src.repositories.chat_repository.get_ai_platform') as mock_platform:
        mock_ai = Mock()
        mock_ai.chat.return_value = "Response"
        mock_platform.return_value = mock_ai

        chat_repository.generate_model_response(
            websocket_message, 
            chat_user, 
            test_db
        )
        
        test_db.refresh(chat_user)
        assert chat_user.ai_requests_count == initial_count + 1


def test_generate_model_response_rejects_when_limit_reached(test_db, chat_user, websocket_message):
    """Test that generate_model_response rejects when usage limit is reached"""
    chat_user.ai_requests_count = 10
    chat_user.is_unlimited = False
    test_db.add(chat_user)
    test_db.commit()
    test_db.refresh(chat_user)
    
    with pytest.raises(HTTPException) as exc_info:
        chat_repository.generate_model_response(
            websocket_message, 
            chat_user, 
            test_db
        )
    
    assert exc_info.value.status_code == 403
    assert "usage limit reached" in exc_info.value.detail.lower()


def test_generate_model_response_allows_unlimited_users(test_db, chat_user, websocket_message):
    """Test that unlimited users can exceed the normal limit"""
    chat_user.ai_requests_count = 50  # Way over normal limit
    chat_user.is_unlimited = True
    test_db.add(chat_user)
    test_db.commit()
    test_db.refresh(chat_user)
    
    with patch('src.repositories.chat_repository.get_ai_platform') as mock_platform:
        mock_ai = Mock()
        mock_ai.chat.return_value = "Response"
        mock_platform.return_value = mock_ai

        chat_record, remaining = chat_repository.generate_model_response(
            websocket_message, 
            chat_user, 
            test_db
        )
        
        assert chat_record is not None
        assert remaining == -1  # Unlimited
        # Counter should not increment for unlimited users
        test_db.refresh(chat_user)
        assert chat_user.ai_requests_count == 50

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
    with patch('src.repositories.chat_repository.get_ai_platform') as mock_platform:
        mock_ai = Mock()
        mock_ai.chat.return_value = "Hello! How can I help you?"
        mock_platform.return_value = mock_ai

        result = chat_repository.generate_model_response(
            websocket_message, 
            chat_user, 
            test_db
        )
        
        assert isinstance(result, ChatHistory)
        assert result.prompt == "Hello, AI!"
        assert result.response == "Hello! How can I help you?"
        assert result.model_name == AIModels.GEMINI
        assert result.user_id == chat_user.id


def test_generate_model_response_calls_correct_ai_platform(test_db, chat_user):
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
    with patch('src.repositories.chat_repository.get_ai_platform') as mock_platform:
        mock_ai = Mock()
        mock_ai.chat.side_effect = Exception("API key invalid")
        mock_platform.return_value = Mock

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

from fastapi import HTTPException, status
from sqlmodel import Session, select

from src.schemas.chat_schema import ChatRequest, WebSocketMessage
from src.core.helpers import get_ai_platform
from src.models.user import User
from src.core.enums import AIModels, is_provider_available
from src.models.chat_history import ChatHistory
from src.core.config import settings


def check_usage_limit(user: User) -> tuple[bool, int]:

    if user.is_unlimited:
        return (True, -1)  # -1 indicates unlimited

    remaining = max(0, settings.AI_USAGE_LIMIT - user.ai_requests_count)

    if remaining == 0:
        return (False, 0)

    return (True, remaining)


def generate_model_response(data: WebSocketMessage, current_user: User, db: Session):
    """
    Generate AI response and increment usage counter.
    Returns tuple of (chat_record, remaining_requests).
    """
    # Check provider availability BEFORE any other checks
    if not is_provider_available(data.model_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This AI provider is currently unavailable due to free-tier limits."
        )

    # Check usage limit BEFORE calling AI provider
    allowed, remaining = check_usage_limit(current_user)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"AI usage limit reached. You have used all {settings.AI_USAGE_LIMIT} free messages."
        )

    platform = get_ai_platform(data.model_name)

    try:
        response_text = platform.chat(data.prompt)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"AI platform error: {str(e)}")

    try:
        chat = ChatHistory(user_id=current_user.id, prompt=data.prompt,
                           response=response_text, model_name=data.model_name)
        db.add(chat)

        # Increment counter AFTER successful AI response
        if not current_user.is_unlimited:
            current_user.ai_requests_count += 1

        db.add(current_user)
        db.commit()
        db.refresh(chat)
        db.refresh(current_user)

        if current_user.is_unlimited:
            final_remaining = -1
        else:
            final_remaining = max(
                0, settings.AI_USAGE_LIMIT - current_user.ai_requests_count)

        return chat, final_remaining
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


def get_chat_history(model_name: AIModels, current_user: User, db: Session):
    chat_records = db.scalars(select(ChatHistory).where(
        ChatHistory.user_id == current_user.id,
        ChatHistory.model_name == model_name)
    ).all()
    return chat_records


# old non-real-time chat code
def chat(data: ChatRequest, current_user: User, db: Session):
    """
    Legacy chat endpoint (non-WebSocket).
    Returns tuple of (response_text, remaining_requests).
    """
    # Check provider availability BEFORE any other checks
    if not is_provider_available(data.model_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This AI provider is currently unavailable due to free-tier limits."
        )

    # Check usage limit BEFORE calling AI provider
    allowed, remaining = check_usage_limit(current_user)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"AI usage limit reached. You have used all {settings.AI_USAGE_LIMIT} free messages."
        )

    platform = get_ai_platform(data.model_name)

    try:
        response_text = platform.chat(data.prompt)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"AI platform error: {str(e)}")

    try:
        chat_record = ChatHistory(user_id=current_user.id, prompt=data.prompt,
                                  response=response_text, model_name=data.model_name)
        db.add(chat_record)

        # Increment counter AFTER successful AI response
        if not current_user.is_unlimited:
            current_user.ai_requests_count += 1

        db.add(current_user)
        db.commit()
        db.refresh(chat_record)
        db.refresh(current_user)

        # Calculate remaining requests after increment
        if current_user.is_unlimited:
            final_remaining = -1
        else:
            final_remaining = max(
                0, settings.AI_USAGE_LIMIT - current_user.ai_requests_count)

        return response_text, final_remaining
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

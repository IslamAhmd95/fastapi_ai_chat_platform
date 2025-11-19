from fastapi import HTTPException, status
from sqlmodel import Session, select

from src.schemas.chat_schema import ChatRequest, WebSocketMessage
from src.core.helpers import get_ai_platform
from src.models.user import User
from src.core.enums import AIModels
from src.models.chat_history import ChatHistory


def generate_model_response(data: WebSocketMessage, current_user: User, db: Session):

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
        db.commit()
        db.refresh(chat)
        return chat
    except Exception as e:
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
    platform = get_ai_platform(data.model_name)

    try:
        response_text = platform.chat(data.prompt)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"AI platform error: {str(e)}")

    try:
        chat = ChatHistory(user_id=current_user.id, prompt=data.prompt,
                           response=response_text, model_name=data.model_name)
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return response_text
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

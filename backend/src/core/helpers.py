from __future__ import annotations
from typing import Optional

import openai
from fastapi import HTTPException, status
from sqlmodel import select, Session
from pydantic import EmailStr, ValidationError

from src.schemas.chat_schema import WebSocketMessage
from src.models.user import User
from src.ai.gemini import Gemini
from src.ai.groq import GroqAI
from src.core.config import settings
from src.core.enums import AIModels


SYSTEM_PROMPT = None

PLATFORM_MAP = {
    AIModels.GEMINI: Gemini,
    AIModels.GROQ: GroqAI,
    # AIModels.OPENAI: OpenAI,
}


def check_email_exists(email: str, db: Session, user: Optional[User] = None):
    query = select(User).where(User.email == email)
    if user:
        query = query.where(User.id != user.id)

    return db.scalar(query)


def check_username_exists(username: str, db: Session, user: Optional[User] = None):
    query = select(User).where(User.username == username)
    if user:
        query = query.where(User.id != user.id)

    return db.scalar(query)


def get_user_from_token(db: Session, email: EmailStr):
    return db.scalar(select(User).where(User.email == email))


async def parse_ws_message(websocket, raw_data):
    try:
        return WebSocketMessage(**raw_data)
    except ValidationError as e:
        await websocket.send_json({"error": "invalid_input", "detail": e.errors()})
        return None


async def process_ai_request(websocket, data, user, db):
    from src.repositories import chat_repository

    try:
        return chat_repository.generate_model_response(data, user, db)
    except HTTPException as e:
        await websocket.send_json({"error": e.detail})
        return None


def load_system_prompt():
    global SYSTEM_PROMPT
    if SYSTEM_PROMPT is None:
        try:
            with open('src/prompts/system-prompt.md', "r") as f:
                SYSTEM_PROMPT = f.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error loading system prompt: {str(e)}"
            )

    return SYSTEM_PROMPT


def get_ai_platform(model_name: AIModels):
    system_prompt = load_system_prompt()

    platform_class = PLATFORM_MAP.get(model_name)
    if not platform_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI platform '{model_name.value.upper()}' not found."
        )

    api_key_setting_name = f"{model_name.value.upper()}_API_KEY"
    api_key = getattr(settings, api_key_setting_name, None)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API key environment variable for {model_name} not set."
        )

    try:
        return platform_class(api_key=api_key, system_prompt=system_prompt)
    except openai.RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Error occurred: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred: {str(e)}"
        )

from fastapi import (
    APIRouter, Depends, WebSocket, WebSocketDisconnect, status, HTTPException
)
from sqlmodel import Session
from fastapi_limiter.depends import WebSocketRateLimiter

from src.models.user import User
from src.core.oauth2 import get_current_user
from src.repositories import chat_repository
from src.core.enums import AIModels, PROVIDER_AVAILABILITY
from src.core import database
from src.core.oauth2 import authenticate_websocket
from src.core.config import settings
from src.core.helpers import get_user_from_token, parse_ws_message, process_ai_request
from src.schemas.chat_schema import (
    ChatRequest, ChatResponse, GetPlatforms, ChatHistoryResponse, UsageInfo
)


router = APIRouter(
    prefix="/ai", tags=["Ai"]
)

# Create rate limiter ONCE at module level to be shared across all connections
ratelimit = WebSocketRateLimiter(
    times=settings.RATE_LIMIT_TIMES,
    seconds=settings.RATE_LIMIT_WINDOW
)


@router.get('/platforms', response_model=GetPlatforms)
def get_platforms():
    return {"platforms": [model.value for model in AIModels]}


@router.get('/provider-availability')
def get_provider_availability():
    return {
        "availability": {
            model.value: PROVIDER_AVAILABILITY.get(model, False)
            for model in AIModels
        }
    }


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    token_data = await authenticate_websocket(websocket)
    if not token_data:
        return

    with Session(database.engine) as db:
        user = get_user_from_token(db, token_data.email)
        if user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        user_id = user.id

    try:
        while True:
            raw_data = await websocket.receive_json()

            data = await parse_ws_message(websocket, raw_data)
            if not data:
                continue

            try:
                await ratelimit(websocket, context_key=f"user:{user_id}")
            except HTTPException:
                error_payload = {
                    "error": f"You have exceeded the rate limit. Please try again after {settings.RATE_LIMIT_WINDOW} seconds.",
                }
                await websocket.send_json(error_payload)
                continue

            # Create new session for each message to get fresh user state
            with Session(database.engine) as db:
                # Fetch user fresh from database for each request
                current_user = get_user_from_token(db, token_data.email)
                if current_user is None:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    break

                chat_record, remaining_requests = await process_ai_request(websocket, data, current_user, db)
                if not chat_record:
                    continue

                # Refresh user to get updated ai_requests_count after increment
                db.refresh(current_user)

                payload = {
                    "prompt": chat_record.prompt,
                    "response": chat_record.response,
                    "created_at": chat_record.created_at.isoformat(),
                    "model_name": chat_record.model_name.value,
                    "remaining_requests": remaining_requests if remaining_requests is not None else (max(0, settings.AI_USAGE_LIMIT - current_user.ai_requests_count) if not current_user.is_unlimited else -1)
                }
                await websocket.send_json(payload)

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except RuntimeError:
            pass
        print("Error:", e)


@router.get('/chat-history', response_model=ChatHistoryResponse)
def get_chat_history(model_name: AIModels, current_user: User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    chat_records = chat_repository.get_chat_history(
        model_name, current_user, db)

    # Calculate remaining requests
    if current_user.is_unlimited:
        remaining_requests = -1
    else:
        remaining_requests = max(
            0, settings.AI_USAGE_LIMIT - current_user.ai_requests_count)

    usage_info = UsageInfo(
        remaining_requests=remaining_requests,
        limit=settings.AI_USAGE_LIMIT
    )

    return ChatHistoryResponse(chat=chat_records, usage_info=usage_info)


# old non-real-time chat code
@router.post('/chat', response_model=ChatResponse)
def chat(data: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    response_text, remaining_requests = chat_repository.chat(
        data, current_user, db)
    return ChatResponse(response=response_text, remaining_requests=remaining_requests)

from fastapi import (
    APIRouter, Depends, WebSocket, WebSocketDisconnect, status, HTTPException
)
from sqlmodel import Session
from fastapi_limiter.depends import WebSocketRateLimiter

from src.models.user import User
from src.core.oauth2 import get_current_user
from src.repositories import chat_repository
from src.core.enums import AIModels
from src.core.database import get_db, engine
from src.core.oauth2 import authenticate_websocket
from src.core.config import settings
from src.core.helpers import get_user_from_token, parse_ws_message, process_ai_request
from src.schemas.chat_schema import (
    ChatRequest, ChatResponse, GetPlatforms, ChatHistoryResponse
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
    return {"platforms": list(AIModels)}


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    token_data = await authenticate_websocket(websocket)
    if not token_data:
        return

    with Session(engine) as db:
        user = get_user_from_token(db, token_data.email)
        if user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    try:
        while True:
            raw_data = await websocket.receive_json()

            data = await parse_ws_message(websocket, raw_data)
            if not data:
                continue

            try:
                await ratelimit(websocket, context_key=f"user:{user.id}")
            except HTTPException:
                error_payload = {
                    "error": f"You have exceeded the rate limit. Please try again after {settings.RATE_LIMIT_WINDOW} seconds.",
                }
                await websocket.send_json(error_payload)
                continue

            chat_record = await process_ai_request(websocket, data, user, db)
            if not chat_record:
                continue

            payload = {
                "prompt": chat_record.prompt,
                "response": chat_record.response,
                "created_at": chat_record.created_at.isoformat(),
                "model_name": chat_record.model_name.value
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
def get_chat_history(model_name: AIModels, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat_records = chat_repository.get_chat_history(model_name, current_user, db)
    return ChatHistoryResponse(chat=chat_records)


# old non-real-time chat code
@router.post('/chat', response_model=ChatResponse)
def chat(data: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    response_text = chat_repository.chat(data, current_user, db)
    return ChatResponse(response=response_text)
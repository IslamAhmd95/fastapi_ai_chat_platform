from typing import List
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from src.core.enums import AIModels



class ChatRequest(BaseModel):
    model_name: AIModels = AIModels.GEMINI
    prompt: str = Field(max_length=5000)


class WebSocketMessage(BaseModel):
    model_name: AIModels = AIModels.GEMINI
    prompt: str = Field(max_length=5000)


class UsageInfo(BaseModel):
    remaining_requests: int
    limit: int


class ChatResponse(BaseModel):
    response: str
    remaining_requests: int


class GetPlatforms(BaseModel):
    platforms: List[AIModels]


class ChatHistoryRequest(BaseModel):
    model_name: AIModels


class Chat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prompt: str
    response: str
    model_name: AIModels
    created_at: datetime 


class ChatHistoryResponse(BaseModel):
    chat: List[Chat]
    usage_info: UsageInfo
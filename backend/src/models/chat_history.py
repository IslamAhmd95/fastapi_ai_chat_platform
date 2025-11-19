from typing import Optional
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field, Relationship
import sqlalchemy as sa

from src.core.enums import AIModels


class ChatHistory(SQLModel, table=True):
    
    __tablename__ = "chat_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    model_name: AIModels
    prompt: str = Field(sa_type=sa.Text())
    response: str = Field(sa_type=sa.Text())

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )

    user: "User" = Relationship(back_populates="chat_history")  # type: ignore


from typing import Optional
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=100)
    username: str = Field(unique=True, max_length=100)
    email: EmailStr = Field(unique=True, max_length=255) 
    password: str = Field(min_length=8, max_length=255, nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # `sa_column_kwargs` allows us to pass arguments to SQLAlchemy's Column definition
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )

    chat_history: list["ChatHistory"] = Relationship(back_populates="user")  # type: ignore

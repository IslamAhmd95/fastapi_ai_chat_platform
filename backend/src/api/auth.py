from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from src.core.database import get_db
from src.core.config import settings
from src.repositories import auth_repository
from src.schemas.auth_schema import (
    SignUpSchema, LoginSchema, AfterSignUpSchema, AfterLoginSchema, UserReadSchema
)


router = APIRouter(
    prefix="/auth", tags=["Auth"]
)


@router.post('/register', response_model=AfterSignUpSchema, status_code=status.HTTP_201_CREATED)
async def sign_up(data: SignUpSchema, db: Session = Depends(get_db)):
    user = await auth_repository.signup(data, db)
    return {
        "user": user,
        "message": f"Account created successfully. You have {settings.AI_USAGE_LIMIT} free AI messages. Use them wisely!"
    }


@router.post('/login', response_model=AfterLoginSchema, status_code=status.HTTP_200_OK)
async def login(schema: LoginSchema, db: Session = Depends(get_db)):
    user, access_token = await auth_repository.login(schema, db)
    return {"user": UserReadSchema.model_validate(user), "access_token": access_token, "token_type": "bearer"}

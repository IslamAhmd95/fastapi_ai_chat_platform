from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from src.core.database import get_db
from src.repositories import auth_repository
from src.schemas.auth_schema import (
    SignUpSchema, LoginSchema, AfterSignUpSchema, AfterLoginSchema, UserReadSchema
)


router = APIRouter(
    prefix="/auth", tags=["Auth"]
)


@router.post('/register', response_model=AfterSignUpSchema, status_code=status.HTTP_201_CREATED)
def sign_up(data: SignUpSchema, db: Session = Depends(get_db)):
    user = auth_repository.signup(data, db)
    return {"user": user, "message": "User created successfully"}


@router.post('/login', response_model=AfterLoginSchema, status_code=status.HTTP_200_OK)
def login(schema: LoginSchema, db: Session = Depends(get_db)):
    user, access_token = auth_repository.login(schema, db)
    return {"user": UserReadSchema.model_validate(user), "access_token": access_token, "token_type": "bearer"}



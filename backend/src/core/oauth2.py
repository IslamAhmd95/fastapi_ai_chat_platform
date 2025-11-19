from typing import Annotated

from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer  
from sqlmodel import select, Session
from src.core.database import get_db

from src.models.user import User
from src.core.token import verify_access_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token_str: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_access_token(token_str, credentials_exception)

    user = db.scalar(select(User).where(User.email == token_data.email))
    if user is None:
        raise credentials_exception

    return user


async def authenticate_websocket(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    try:
        token_data = verify_access_token(token, None)
        return token_data
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
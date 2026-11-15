from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import TokenType, decode_token
from app.db import get_db
from app.models.user import User
from app.repositories.users import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials"
    )
    try:
        payload = decode_token(token, settings)
        if payload.get("type") != TokenType.ACCESS.value:
            raise error
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise error from exc
    user = await UserRepository(db).get(user_id)
    if not user or not user.is_active:
        raise error
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_roles(*roles: str):
    async def dependency(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return dependency

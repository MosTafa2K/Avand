from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import Settings, get_settings
from app.core.security import TokenType, create_token, verify_password
from app.db import get_db
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.users import ConflictError, UserService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db=Depends(get_db)):
    try:
        return await UserService(db).create(data)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db=Depends(get_db), settings: Settings = Depends(get_settings)):
    user = await UserRepository(db).get_by_email(str(data.email))
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return TokenResponse(
        access_token=create_token(str(user.id), TokenType.ACCESS, settings),
        refresh_token=create_token(str(user.id), TokenType.REFRESH, settings),
    )


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
async def oauth_login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db=Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    return await login(LoginRequest(email=form.username, password=form.password), db, settings)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, settings: Settings = Depends(get_settings)):
    try:
        payload = jwt.decode(
            data.refresh_token, settings.secret_key.get_secret_value(), algorithms=["HS256"]
        )
        if payload.get("type") != TokenType.REFRESH.value:
            raise ValueError("wrong token type")
        subject = payload["sub"]
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
    return TokenResponse(
        access_token=create_token(subject, TokenType.ACCESS, settings),
        refresh_token=create_token(subject, TokenType.REFRESH, settings),
    )

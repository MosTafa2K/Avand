from datetime import UTC, datetime, timedelta
from enum import StrEnum

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings

password_hash = PasswordHash.recommended()


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_token(subject: str, token_type: TokenType, settings: Settings) -> str:
    now = datetime.now(UTC)
    lifetime = (
        timedelta(minutes=settings.access_token_expire_minutes)
        if token_type == TokenType.ACCESS
        else timedelta(days=settings.refresh_token_expire_days)
    )
    return jwt.encode(
        {"sub": subject, "type": token_type.value, "iat": now, "exp": now + lifetime},
        settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )


def decode_token(token: str, settings: Settings) -> dict:
    return jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=["HS256"])

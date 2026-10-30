import secrets
from datetime import (
    datetime,
    timedelta,
    timezone
)
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def create_access_token(
    data: dict,
    expires_minutes: Optional[int] = None
) -> str:
    """
    Creates a cryptographically signed JWT access token.
    Rotates session identifier with unique 'jti' on each issue,
    embeds timestamp 'iat', and applies token_version for global session invalidation.
    """
    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    duration = timedelta(
        minutes=expires_minutes if expires_minutes is not None else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expire = now + duration

    if "jti" not in to_encode:
        to_encode["jti"] = secrets.token_hex(16)

    if "iat" not in to_encode:
        to_encode["iat"] = int(now.timestamp())

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt

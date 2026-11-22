
import hashlib
import secrets
from typing import Optional, Union, Any
from datetime import datetime, timedelta

from jose import jwt, JWTError
from backend.app.core.config import settings


def get_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    hash_value = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"sha256${salt}${hash_value}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        algorithm, salt, hash_value = hashed_password.split("$")
        if algorithm == "sha256":
            computed_hash = hashlib.sha256(
                (plain_password + salt).encode()
            ).hexdigest()
            return secrets.compare_digest(computed_hash, hash_value)
    except (ValueError, AttributeError):
        pass
    return False


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {"exp": expire, "sub": str(subject)}

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def decode_access_token(token: str) -> str:
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )

    subject = payload.get("sub")

    if not subject:
        raise JWTError("Token subject missing")

    return subject


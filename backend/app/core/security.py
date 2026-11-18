import hashlib
import secrets
from typing import Optional, Union, Any
from datetime import datetime, timedelta
from jose import jwt
from backend.app.core.config import settings

def get_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    hash_value = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"sha256${salt}${hash_value}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        algorithm, salt, hash_value = hashed_password.split("$")
        if algorithm == "sha256":
            computed_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()
            return secrets.compare_digest(computed_hash, hash_value)
    except (ValueError, AttributeError):
        pass
    return False

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

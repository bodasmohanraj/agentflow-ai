
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from backend.app.core.config import settings
from backend.app.core.security import decode_access_token
from backend.app.db.session import get_db
from backend.app.models.models import User


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        email = decode_access_token(token)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


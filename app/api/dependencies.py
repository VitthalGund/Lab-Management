from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from typing import List

from app.db.session import SessionLocal
from app.core.security import decode_access_token
from app.services import user_service
from app.models.user import User, UserRole
from app.schemas.auth import TokenData

# This tells FastAPI where to look for the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/token")


def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get the current user from a JWT token.
    This performs AUTHENTICATION (verifying who the user is).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception
        mobile_number: str = payload.get("sub")
        if mobile_number is None:
            raise credentials_exception
        token_data = TokenData(mobile_number=mobile_number)
    except JWTError:
        raise credentials_exception

    user = user_service.get_user_by_mobile(db, mobile_number=token_data.mobile_number)
    if user is None:
        raise credentials_exception
    return user


class RoleChecker:
    """
    A dependency factory to check for user roles.
    This performs AUTHORIZATION (verifying what the user can do).
    """

    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

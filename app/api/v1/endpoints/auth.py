from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.schemas.auth import Token, UserLogin
from app.schemas.user import UserCreate, User as UserSchema
from app.services import user_service
from app.core.security import create_access_token, verify_password
from app.api.dependencies import get_db, RoleChecker  # Import RoleChecker
from app.models.user import User, UserRole  # Import User and UserRole

router = APIRouter()

# This dependency will ensure only admins can access the endpoint
admin_permission = RoleChecker([UserRole.admin])


@router.post("/login/token", response_model=Token)
def login_for_access_token(
    # db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
    login_data: UserLogin,  # This correctly expects a JSON body matching the UserLogin schema
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return a JWT token.
    Accepts a JSON body.
    """
    user = user_service.get_user_by_mobile(db, mobile_number=login_data.mobile_number)
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect mobile number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.mobile_number, "role": user.role.value}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/users/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),  # This protects the route
):
    """
    Create a new user. This endpoint is now protected and can only be
    accessed by an authenticated admin user.

    This is how you will create Lab Heads, other Admins, etc.
    """
    db_user = user_service.get_user_by_mobile(db, mobile_number=user.mobile_number)
    if db_user:
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    # You could add more logic here, e.g., an admin can't create a student directly

    return user_service.create_user(db=db, user=user)

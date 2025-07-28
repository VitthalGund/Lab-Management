from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.user import User as UserSchema, UserMeUpdate, UserPasswordChange
from app.services import user_service
from app.api.dependencies import get_db, get_current_user
from app.models.user import User

router = APIRouter()


@router.put("/me/", response_model=UserSchema)
def update_current_user(
    data: UserMeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the profile of the currently authenticated user."""
    return user_service.update_me(db=db, user=current_user, data=data)


@router.post("/me/change-password")
def change_current_user_password(
    data: UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the password of the currently authenticated user."""
    success = user_service.change_password(db=db, user=current_user, data=data)
    if not success:
        raise HTTPException(status_code=400, detail="Incorrect current password")
    return {"message": "Password changed successfully"}

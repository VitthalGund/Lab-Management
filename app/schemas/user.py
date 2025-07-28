from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole


# --- Existing Schemas ---
class UserBase(BaseModel):
    name: str
    last_name: str
    mobile_number: str
    email: Optional[EmailStr] = None
    role: UserRole


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserMeUpdate(BaseModel):
    """Schema for a user updating their own profile."""

    name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None


class UserPasswordChange(BaseModel):
    """Schema for changing a password."""

    current_password: str
    new_password: str

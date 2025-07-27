from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole


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

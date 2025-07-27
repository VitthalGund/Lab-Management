from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date
from .user import User  # Import the base User schema for nesting


# --- Schema for creating a new Teacher ---
# This includes creating the underlying user account and the teacher profile.
class TeacherCreate(BaseModel):
    name: str
    last_name: str
    mobile_number: str
    password: str
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None
    date_of_joining: Optional[date] = None
    skills: Optional[List[str]] = []


# --- Schema for updating a Teacher ---
# All fields are optional.
class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_number: Optional[str] = None
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None
    date_of_joining: Optional[date] = None
    skills: Optional[List[str]] = None


# --- Schema for API Response ---
# This will be the detailed teacher profile returned by the API.
class Teacher(BaseModel):
    user: User  # The full user object
    lab_id: int
    bio: Optional[str] = None
    date_of_joining: Optional[date] = None
    skills: List[str] = []

    class Config:
        from_attributes = True

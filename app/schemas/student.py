from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date

from .user import User


# --- Schema for creating a single Student ---
class StudentCreate(BaseModel):
    name: str
    last_name: str
    mobile_number: str
    password: str
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    join_date_in_lab: Optional[date] = date.today()
    last_year_marks: Optional[str] = None
    mother_name: Optional[str] = None
    mother_contact: Optional[str] = None
    father_name: Optional[str] = None
    father_contact: Optional[str] = None


# --- Schema for Bulk Creation ---
# This schema will be used as the request body for the bulk endpoint.
class StudentBulkCreate(BaseModel):
    students: List[StudentCreate]


# --- Schema for API Response ---
class StudentProfileDetails(BaseModel):
    join_date_in_lab: Optional[date]
    last_year_marks: Optional[str]
    mother_name: Optional[str]
    mother_contact: Optional[str]
    father_name: Optional[str]
    father_contact: Optional[str]


class Student(BaseModel):
    user: User  # The full user object
    profile: StudentProfileDetails

    class Config:
        from_attributes = True


# --- Schema for Updating a Student ---
class StudentUpdate(BaseModel):
    name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_number: Optional[str] = None
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    join_date_in_lab: Optional[date] = None
    last_year_marks: Optional[str] = None
    mother_name: Optional[str] = None
    mother_contact: Optional[str] = None
    father_name: Optional[str] = None
    father_contact: Optional[str] = None

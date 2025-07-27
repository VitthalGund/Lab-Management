from pydantic import BaseModel
from typing import Optional


# --- Base Schema ---
class SchoolBase(BaseModel):
    name: str
    location: Optional[str] = None
    principal_name: Optional[str] = None
    trustees: Optional[str] = None
    about: Optional[str] = None


# --- Schema for Creation ---
# Inherits from Base, all fields are required for creation.
class SchoolCreate(SchoolBase):
    pass


# --- Schema for Updates ---
# All fields are optional for updates.
class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    principal_name: Optional[str] = None
    trustees: Optional[str] = None
    about: Optional[str] = None


# --- Schema for API Response ---
# This is the model that will be returned to the client.
class School(SchoolBase):
    id: int

    class Config:
        from_attributes = True

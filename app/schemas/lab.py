from pydantic import BaseModel
from typing import Optional
from datetime import date

from .school import School  # Import the School schema for nesting


# --- Base Schema ---
class LabBase(BaseModel):
    name: str
    start_date: Optional[date] = None


# --- Schema for Creation ---
# Requires school_id to link the lab to a school.
class LabCreate(LabBase):
    school_id: int


# --- Schema for Updates ---
# All fields are optional when updating.
class LabUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    school_id: Optional[int] = None


# --- Schema for API Response ---
# This model will be returned to the client. It includes the full School object.
class Lab(LabBase):
    id: int
    school_id: int
    school: School  # Nested school details

    class Config:
        from_attributes = True

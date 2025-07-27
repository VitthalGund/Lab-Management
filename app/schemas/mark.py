from pydantic import BaseModel
from typing import Optional
from datetime import date


# --- Schema for Creating a Mark ---
class MarkCreate(BaseModel):
    assessment_name: str
    marks_obtained: float
    total_marks: float


# --- Schema for API Response ---
# This model will be returned to the client.
class Mark(MarkCreate):
    id: int
    enrollment_id: int
    date_recorded: date

    class Config:
        from_attributes = True


# --- Schema for Updating a Mark ---
class MarkUpdate(BaseModel):
    assessment_name: Optional[str] = None
    marks_obtained: Optional[float] = None
    total_marks: Optional[float] = None

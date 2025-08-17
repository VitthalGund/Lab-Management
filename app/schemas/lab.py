from pydantic import BaseModel
from typing import Optional, List
from datetime import date

from .school import School


class LabBase(BaseModel):
    name: str
    start_date: Optional[date] = None


class LabCreate(LabBase):
    school_id: int


class LabUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    school_id: Optional[int] = None


class Lab(LabBase):
    id: int
    school_id: int
    school: School

    class Config:
        from_attributes = True


class PaginatedLabsResponse(BaseModel):
    labs: List[Lab]
    total: int

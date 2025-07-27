from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from .user import User  # To show author details


# --- Base Schema for Project ---
class ProjectBase(BaseModel):
    project_name: str
    description: Optional[str] = None
    video_links: Optional[List[str]] = []
    photo_urls: Optional[List[str]] = []


# --- Schema for Creating a Project ---
# A student must specify which cohort they are submitting for.
class ProjectCreate(ProjectBase):
    cohort_id: int


# --- Schema for API Response ---
# This is the detailed model returned by the API.
class Project(ProjectBase):
    id: int
    submission_date: datetime
    author: User  # Nested user object for the student
    star_count: int  # A calculated field for the number of stars

    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    video_links: Optional[List[str]] = None
    photo_urls: Optional[List[str]] = None

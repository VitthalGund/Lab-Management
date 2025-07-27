from pydantic import BaseModel
from typing import List

from .project import Project  # Reuse existing schemas
from .mark import Mark


class StudentDashboardStats(BaseModel):
    total_projects_submitted: int
    total_stars_received: int
    recent_projects: List[Project]  # Top 5 recent
    recent_marks: List[Mark]  # Top 5 recent

    class Config:
        from_attributes = True

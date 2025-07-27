from pydantic import BaseModel
from typing import List

from .project import Project  # Reuse the detailed project schema


class ProjectDashboardStats(BaseModel):
    top_rated_projects: List[Project]  # Top 10 by stars
    most_recent_projects: List[Project]  # Top 10 recent

    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import List, Optional

# --- Data Structures for Dashboard Components ---


class KPIStats(BaseModel):
    """Key Performance Indicators for the lab."""

    total_students: int
    total_teachers: int
    total_projects: int
    total_stars: int


class ChartDataPoint(BaseModel):
    """A single data point for a chart (e.g., pie, bar, donut)."""

    name: str
    value: int


class TrendDataPoint(BaseModel):
    """A single data point for a time-series trend chart."""

    month: str  # Format: "YYYY-MM"
    count: int


class TopStudent(BaseModel):
    """Represents a top-performing student on the leaderboard."""

    student_id: int
    student_name: str
    projects_submitted: int
    stars_received: int


class TopProject(BaseModel):
    """Represents a top-rated project."""

    project_id: int
    project_name: str
    student_name: str
    star_count: int


# --- Main Dashboard Response Model ---


class LabDashboardStats(BaseModel):
    """The complete data model for the lab dashboard response."""

    kpis: KPIStats
    student_distribution: List[ChartDataPoint]
    grok_specialization: List[ChartDataPoint]
    project_trend: List[TrendDataPoint]
    performance_distribution: List[ChartDataPoint]
    top_students: List[TopStudent]
    top_projects: List[TopProject]

    class Config:
        from_attributes = True

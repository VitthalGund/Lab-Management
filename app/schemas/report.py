from pydantic import BaseModel
from typing import List

from .teacher import Teacher  # Reuse existing detailed schemas
from .student import Student
from .project import Project


# --- Schema for the Lab Report Response ---
class LabReport(BaseModel):
    cohort_id: int
    lab_id: int
    lab_name: str
    cohort_name: str
    teachers: List[Teacher]
    students: List[Student]
    projects: List[Project]


# --- Schema for an entry in the Top Student Report ---
class TopStudentEntry(BaseModel):
    rank: int
    student: Student
    projects_submitted_in_month: int
    stars_received_in_month: int
    score: int  # A calculated score for ranking


# --- Schema for the Top Student Report Response ---
class TopStudentReport(BaseModel):
    month: int
    year: int
    report: List[TopStudentEntry]

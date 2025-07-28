from pydantic import BaseModel
from typing import Optional, List
from datetime import date

from app.models.enrollment import LabSection, GrokSpecialization
from .user import User


class EnrollmentCohortCreate(BaseModel):
    academic_year: int
    section: LabSection
    standard: int
    semester_start_date: Optional[date] = None
    semester_end_date: Optional[date] = None
    batch_name: Optional[str] = None
    grok_specialization: Optional[GrokSpecialization] = None


class EnrollmentCohort(EnrollmentCohortCreate):
    id: int
    lab_id: int
    created_by_user_id: int

    class Config:
        from_attributes = True


class StudentEnrollmentCreate(BaseModel):
    student_user_ids: List[int]


class EnrollmentCohortUpdate(BaseModel):
    academic_year: Optional[int] = None
    section: Optional[LabSection] = None
    standard: Optional[int] = None
    semester_start_date: Optional[date] = None
    semester_end_date: Optional[date] = None
    batch_name: Optional[str] = None
    grok_specialization: Optional[GrokSpecialization] = None


class StudentEnrollmentDetails(BaseModel):
    """Detailed view of a student's enrollment."""

    id: int
    cohort: EnrollmentCohort

    class Config:
        from_attributes = True


class TeacherAssignmentDetails(BaseModel):
    """Detailed view of a teacher's assignment."""

    id: int
    cohort: EnrollmentCohort

    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import Optional, List
from datetime import date

from app.models.enrollment import LabSection, GrokSpecialization


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
        from_attributes = True  # FIX: Renamed from orm_mode


class StudentEnrollmentCreate(BaseModel):
    student_user_ids: List[int]


# --- Schema for Updating a Cohort ---
class EnrollmentCohortUpdate(BaseModel):
    academic_year: Optional[int] = None
    section: Optional[LabSection] = None
    standard: Optional[int] = None
    semester_start_date: Optional[date] = None
    semester_end_date: Optional[date] = None
    batch_name: Optional[str] = None
    grok_specialization: Optional[GrokSpecialization] = None

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.schemas.report import LabReport, TopStudentReport
from app.services import report_service
from app.api.dependencies import get_db, RoleChecker
from app.models.user import User, UserRole

router = APIRouter()

# --- Permission Dependencies ---
staff_permission = RoleChecker(
    [UserRole.admin, UserRole.sub_admin, UserRole.lab_head, UserRole.teacher]
)


@router.get("/lab-report/{cohort_id}", response_model=LabReport)
def get_lab_report(
    cohort_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_permission),
):
    """
    Generate a detailed report for a specific cohort.
    - **Permissions**: admin, sub_admin, lab_head, teacher
    """
    report = report_service.generate_lab_report(db, cohort_id=cohort_id)
    if not report:
        raise HTTPException(status_code=404, detail="Cohort not found")
    return report


@router.get("/top-student-report/", response_model=TopStudentReport)
def get_top_student_report(
    month: int = Query(datetime.now().month, ge=1, le=12),
    year: int = Query(datetime.now().year, ge=2020),
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_permission),
):
    """
    Generate a ranked report of top students for a given month and year.
    - **Permissions**: admin, sub_admin, lab_head, teacher
    """
    return report_service.generate_top_student_report(db, month=month, year=year)

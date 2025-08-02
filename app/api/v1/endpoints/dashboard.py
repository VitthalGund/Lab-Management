from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Import new schemas and services
from app.schemas.dashboard import LabDashboardStats
from app.schemas.dashboard_student import StudentDashboardStats
from app.schemas.dashboard_project import ProjectDashboardStats
from app.services import (
    dashboard_service,
    dashboard_student_service,
    dashboard_project_service,
)

# Import new dependencies
from app.api.dependencies import get_db, RoleChecker
from app.models.user import User, UserRole

router = APIRouter()

# --- Permission Dependencies ---
student_permission = RoleChecker([UserRole.student])
any_user_permission = RoleChecker(
    [
        UserRole.admin,
        UserRole.sub_admin,
        UserRole.lab_head,
        UserRole.teacher,
        UserRole.student,
    ]
)


@router.get("/lab/{lab_id}/", response_model=LabDashboardStats)
def read_lab_dashboard(
    lab_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(any_user_permission),
):
    """
    Retrieve dashboard statistics for a specific lab.
    """
    # Note: Add permission check here if not all users should see all lab dashboards
    stats = dashboard_service.get_lab_dashboard_stats(db=db, lab_id=lab_id)
    return stats


@router.get("/me/", response_model=StudentDashboardStats)
def read_student_dashboard(
    db: Session = Depends(get_db), current_user: User = Depends(student_permission)
):
    """
    Retrieve personalized dashboard statistics for the currently authenticated student.
    - **Permissions**: student
    """
    return dashboard_student_service.get_student_dashboard_stats(
        db=db, student_id=current_user.id
    )


@router.get("/projects/", response_model=ProjectDashboardStats)
def read_project_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        any_user_permission
    ),  # Any authenticated user can see this
):
    """
    Retrieve global project dashboard statistics (top-rated and recent).
    - **Permissions**: any authenticated user
    """
    return dashboard_project_service.get_project_dashboard_stats(db=db)

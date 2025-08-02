from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.services import dashboard_admin_service
from app.api.dependencies import get_db, RoleChecker
from app.models.user import UserRole

router = APIRouter()

admin_permission = RoleChecker([UserRole.admin, UserRole.sub_admin])


@router.get("/")
def read_admin_dashboard_stats(
    db: Session = Depends(get_db), current_user=Depends(admin_permission)
):
    """
    Retrieve aggregated statistics for the admin dashboard.
    """
    return dashboard_admin_service.get_admin_dashboard_stats(db=db)

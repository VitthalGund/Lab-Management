from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from enum import Enum
from typing import List, Union

from app.services import leaderboard_service
from app.api.dependencies import get_db, RoleChecker
from app.models.user import User, UserRole
from app.schemas.leaderboard import (
    LeaderboardStudentEntry,
    LeaderboardProjectEntry,
    LeaderboardUser,
)

router = APIRouter()

admin_permission = RoleChecker([UserRole.admin, UserRole.sub_admin])


class LeaderboardType(str, Enum):
    student = "student"
    project = "project"


class LeaderboardPeriod(str, Enum):
    month = "month"
    year = "year"
    all_time = "all_time"


@router.get(
    "/",
    response_model=Union[List[LeaderboardStudentEntry], List[LeaderboardProjectEntry]],
)
def get_leaderboards(
    type: LeaderboardType = Query(..., description="Type of leaderboard"),
    period: LeaderboardPeriod = Query(
        LeaderboardPeriod.month, description="Time period for the leaderboard"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),
):
    """
    Get filterable leaderboards for top students or projects.
    """
    results = leaderboard_service.get_leaderboard(
        db, item_type=type.value, period=period.value
    )

    if type == LeaderboardType.student:
        # FIX: Correctly populate the Pydantic model from the dictionary
        return [
            LeaderboardStudentEntry(
                rank=i + 1,
                student=LeaderboardUser.model_validate(r["user"]),
                score=r["score"],
            )
            for i, r in enumerate(results)
        ]
    elif type == LeaderboardType.project:
        # FIX: Correctly populate the Pydantic model from the (Project, star_count) tuple
        return [
            LeaderboardProjectEntry(
                id=p.id,
                project_name=p.project_name,
                author=LeaderboardUser.model_validate(p.student),
                star_count=s_count,
            )
            for p, s_count in results
        ]
    return []

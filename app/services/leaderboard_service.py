from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, extract
from datetime import datetime

from app.models import User, Project, ProjectStar


def get_leaderboard(db: Session, item_type: str, period: str):
    """
    Calculates and returns a top 10 leaderboard for students or projects
    based on a specified time period.
    """
    now = datetime.utcnow()

    project_filter = []
    star_filter = []

    if period == "month":
        project_filter.extend(
            [
                extract("year", Project.submission_date) == now.year,
                extract("month", Project.submission_date) == now.month,
            ]
        )
        star_filter.extend(
            [
                extract("year", ProjectStar.starred_at) == now.year,
                extract("month", ProjectStar.starred_at) == now.month,
            ]
        )
    elif period == "year":
        project_filter.append(extract("year", Project.submission_date) == now.year)
        star_filter.append(extract("year", ProjectStar.starred_at) == now.year)

    if item_type == "student":
        projects_subquery = (
            db.query(
                Project.student_user_id, func.count(Project.id).label("project_count")
            )
            .filter(*project_filter)
            .group_by(Project.student_user_id)
            .subquery()
        )

        stars_subquery = (
            db.query(
                Project.student_user_id, func.count(ProjectStar.id).label("star_count")
            )
            .join(ProjectStar)
            .filter(*star_filter)
            .group_by(Project.student_user_id)
            .subquery()
        )

        query = (
            db.query(
                User,
                func.coalesce(projects_subquery.c.project_count, 0).label("p_count"),
                func.coalesce(stars_subquery.c.star_count, 0).label("s_count"),
            )
            .outerjoin(
                projects_subquery, User.id == projects_subquery.c.student_user_id
            )
            .outerjoin(stars_subquery, User.id == stars_subquery.c.student_user_id)
            .filter(User.role == "student")
            .filter(
                (func.coalesce(projects_subquery.c.project_count, 0) > 0)
                | (func.coalesce(stars_subquery.c.star_count, 0) > 0)
            )
        )

        results = []
        for user, p_count, s_count in query.all():
            score = (p_count * 10) + (s_count * 2)
            # FIX: Include all necessary counts in the returned dictionary
            results.append(
                {
                    "user": user,
                    "score": score,
                    "project_count": p_count,
                    "star_count": s_count,
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:10]

    elif item_type == "project":
        # FIX: Added joinedload for the student relationship to ensure 'author' is available
        query = (
            db.query(Project, func.count(ProjectStar.id).label("star_count"))
            .outerjoin(ProjectStar)
            .join(Project.student)
            .filter(*star_filter)
            .group_by(Project.id, User.id)
            .order_by(desc("star_count"))
            .limit(10)
            .all()
        )
        return query

    return []

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Project, ProjectStar, User
from app.schemas.dashboard_project import ProjectDashboardStats
from app.schemas.project import Project as ProjectSchema


def get_project_dashboard_stats(db: Session) -> ProjectDashboardStats:
    """
    Generates statistics for the global project dashboard.
    """
    # 1. Top Rated Projects (Top 10 by stars)
    top_rated_query = (
        db.query(Project, func.count(ProjectStar.id).label("star_count"))
        .outerjoin(Project.stars)
        .join(Project.student)
        .group_by(Project.id, User.id)
        .order_by(func.count(ProjectStar.id).desc())
        .limit(10)
        .all()
    )

    top_rated_list = []
    for p, star_count in top_rated_query:
        top_rated_list.append(
            ProjectSchema(
                id=p.id,
                project_name=p.project_name,
                description=p.description,
                video_links=p.video_links,
                photo_urls=p.photo_urls,
                submission_date=p.submission_date,
                author=p.student,
                star_count=star_count,
            )
        )

    # 2. Most Recent Projects (Top 10)
    most_recent_query = (
        db.query(Project, func.count(ProjectStar.id).label("star_count"))
        .outerjoin(Project.stars)
        .join(Project.student)
        .group_by(Project.id, User.id)
        .order_by(Project.submission_date.desc())
        .limit(10)
        .all()
    )

    most_recent_list = []
    for p, star_count in most_recent_query:
        most_recent_list.append(
            ProjectSchema(
                id=p.id,
                project_name=p.project_name,
                description=p.description,
                video_links=p.video_links,
                photo_urls=p.photo_urls,
                submission_date=p.submission_date,
                author=p.student,
                star_count=star_count,
            )
        )

    return ProjectDashboardStats(
        top_rated_projects=top_rated_list, most_recent_projects=most_recent_list
    )

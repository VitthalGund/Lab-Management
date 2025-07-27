from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import Project, ProjectStar, Mark, StudentEnrollment
from app.schemas.dashboard_student import StudentDashboardStats
from app.schemas.project import Project as ProjectSchema


def get_student_dashboard_stats(db: Session, student_id: int) -> StudentDashboardStats:
    """
    Generates personalized dashboard statistics for a single student.
    """
    # 1. Total Projects Submitted
    total_projects = (
        db.query(func.count(Project.id))
        .filter(Project.student_user_id == student_id)
        .scalar()
    )

    # 2. Total Stars Received
    total_stars = (
        db.query(func.count(ProjectStar.id))
        .join(Project)
        .filter(Project.student_user_id == student_id)
        .scalar()
    )

    # 3. Recent Projects (Top 5)
    recent_projects_query = (
        db.query(Project, func.count(ProjectStar.id).label("star_count"))
        .filter(Project.student_user_id == student_id)
        .outerjoin(ProjectStar, Project.id == ProjectStar.project_id)
        .group_by(Project.id)
        .options(joinedload(Project.student))
        .order_by(Project.submission_date.desc())
        .limit(5)
        .all()
    )

    recent_projects_list = []
    for p, star_count in recent_projects_query:
        recent_projects_list.append(
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

    # 4. Recent Marks (Top 5)
    recent_marks = (
        db.query(Mark)
        .join(StudentEnrollment)
        .filter(StudentEnrollment.student_user_id == student_id)
        .order_by(Mark.date_recorded.desc())
        .limit(5)
        .all()
    )

    return StudentDashboardStats(
        total_projects_submitted=total_projects or 0,
        total_stars_received=total_stars or 0,
        recent_projects=recent_projects_list,
        recent_marks=recent_marks,
    )

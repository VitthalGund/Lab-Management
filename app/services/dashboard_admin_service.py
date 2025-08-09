from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract
from datetime import datetime

from app.models import School, Lab, User, Project, ProjectStar
from app.models.user import UserRole


def get_admin_dashboard_stats(db: Session):
    """
    Efficiently calculates all statistics for the admin dashboard on the server.
    """
    now = datetime.utcnow()
    current_month = now.month
    current_year = now.year

    # --- Core Counts ---
    schools_count = db.query(func.count(School.id)).scalar() or 0
    labs_count = db.query(func.count(Lab.id)).scalar() or 0
    teachers_count = (
        db.query(func.count(User.id))
        .filter(User.role.in_([UserRole.teacher, UserRole.lab_head]))
        .scalar()
        or 0
    )
    students_count = (
        db.query(func.count(User.id)).filter(User.role == UserRole.student).scalar()
        or 0
    )

    # --- Monthly Stats ---
    projects_this_month = (
        db.query(func.count(Project.id))
        .filter(
            extract("year", Project.submission_date) == current_year,
            extract("month", Project.submission_date) == current_month,
        )
        .scalar()
        or 0
    )

    stars_this_month = (
        db.query(func.count(ProjectStar.id))
        .filter(
            extract("year", ProjectStar.starred_at) == current_year,
            extract("month", ProjectStar.starred_at) == current_month,
        )
        .scalar()
        or 0
    )

    # --- School Rankings ---
    school_ranking_query = (
        db.query(
            School.name,
            func.count(func.distinct(Project.id)).label("project_count"),
            func.count(ProjectStar.id).label("star_count"),
        )
        .select_from(School)
        .outerjoin(Lab)
        .outerjoin(Project, Project.cohort.has(lab_id=Lab.id))
        .outerjoin(ProjectStar, Project.id == ProjectStar.project_id)
        .group_by(School.id)
        .all()
    )

    school_rankings = []
    for name, p_count, s_count in school_ranking_query:
        score = (p_count * 10) + (s_count * 2)
        school_rankings.append(
            {"name": name, "projects": p_count, "stars": s_count, "score": score}
        )

    school_rankings.sort(key=lambda x: x["score"], reverse=True)

    # --- Recent Activities ---
    recent_projects = (
        db.query(Project).order_by(desc(Project.submission_date)).limit(3).all()
    )
    recent_users = db.query(User).order_by(desc(User.id)).limit(3).all()

    activities = []
    for project in recent_projects:
        activities.append(f"New project '{project.project_name}' submitted.")
    for user in recent_users:
        activities.append(f"User '{user.name}' ({user.role.value}) registered.")

    return {
        "schools": schools_count,
        "labs": labs_count,
        "teachers": teachers_count,
        "students": students_count,
        "projects_this_month": projects_this_month,
        "stars_this_month": stars_this_month,
        "avg_projects_per_school": (
            (db.query(func.count(Project.id)).scalar() or 0) / schools_count
            if schools_count > 0
            else 0
        ),
        "school_rankings": school_rankings[:5],
        "recent_activities": activities[:5],
    }

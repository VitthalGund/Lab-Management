from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models import School, Lab, User, Project, ProjectStar
from app.models.user import UserRole


def get_admin_dashboard_stats(db: Session):
    """
    Efficiently calculates all statistics for the admin dashboard on the server.
    """
    schools_count = db.query(func.count(School.id)).scalar()
    labs_count = db.query(func.count(Lab.id)).scalar()
    teachers_count = (
        db.query(func.count(User.id))
        .filter(User.role.in_([UserRole.teacher, UserRole.lab_head]))
        .scalar()
    )
    students_count = (
        db.query(func.count(User.id)).filter(User.role == UserRole.student).scalar()
    )

    labs_per_school = (
        db.query(School.name, func.count(Lab.id).label("lab_count"))
        .outerjoin(Lab, School.id == Lab.school_id)
        .group_by(School.id)
        .all()
    )

    # NEW: Fetch recent activities
    recent_projects = (
        db.query(Project).order_by(desc(Project.submission_date)).limit(3).all()
    )
    recent_users = (
        db.query(User).order_by(desc(User.id)).limit(3).all()
    )  # Assuming higher ID is newer

    activities = []
    for project in recent_projects:
        activities.append(f"New project '{project.project_name}' submitted.")
    for user in recent_users:
        activities.append(
            f"User '{user.name} {user.last_name}' ({user.role.value}) registered."
        )

    print(
        {
            "schools": schools_count or 0,
            "labs": labs_count or 0,
            "teachers": teachers_count or 0,
            "students": students_count or 0,
            "labs_per_school": [
                {"name": name, "labs": count} for name, count in labs_per_school
            ],
            "recent_activities": activities[:5],  # Return the top 5 mixed activities
        }
    )
    return {
        "schools": schools_count or 0,
        "labs": labs_count or 0,
        "teachers": teachers_count or 0,
        "students": students_count or 0,
        "labs_per_school": [
            {"name": name, "labs": count} for name, count in labs_per_school
        ],
        "recent_activities": activities[:5],  # Return the top 5 mixed activities
    }

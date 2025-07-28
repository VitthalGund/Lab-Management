from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional

from app.models.project import Project, ProjectStar
from app.models.enrollment import StudentEnrollment
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(
    db: Session, project_data: ProjectCreate, student_id: int
) -> Optional[Project]:
    """
    Creates a new project for a student.
    - Validates that the student is enrolled in the specified cohort.
    """
    # 1. Validation: Check if the student is enrolled in the cohort
    enrollment = (
        db.query(StudentEnrollment)
        .filter(
            StudentEnrollment.student_user_id == student_id,
            StudentEnrollment.cohort_id == project_data.cohort_id,
        )
        .first()
    )

    if not enrollment:
        # The student is not enrolled in the cohort they are trying to submit to.
        return None

    # 2. Creation
    db_project = Project(**project_data.dict(), student_user_id=student_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_projects_by_lab(db: Session, lab_id: int) -> List[Project]:
    """
    Retrieves all projects associated with a lab, including author and star count.
    """
    # This query is complex: Project -> EnrollmentCohort -> Lab
    # We also need to count stars for each project.
    projects = (
        db.query(Project, func.count(ProjectStar.id).label("star_count"))
        .join(Project.cohort)
        .filter(Project.cohort.has(lab_id=lab_id))
        .outerjoin(ProjectStar, Project.id == ProjectStar.project_id)
        .group_by(Project.id)
        .options(joinedload(Project.student))  # Eager load the student author
        .all()
    )

    # The result is a list of tuples (Project, star_count). We need to combine them.
    response_objects = []
    for project, star_count in projects:
        project.star_count = star_count
        response_objects.append(project)

    return response_objects


def star_unstar_project(db: Session, project_id: int, user_id: int) -> bool:
    """
    Adds or removes a star from a project for a given user.
    Returns True if the project was starred, False if it was unstarred.
    """
    existing_star = (
        db.query(ProjectStar)
        .filter(ProjectStar.project_id == project_id, ProjectStar.user_id == user_id)
        .first()
    )

    if existing_star:
        # User has already starred, so unstar it.
        db.delete(existing_star)
        db.commit()
        return False
    else:
        # User has not starred it, so add a star.
        new_star = ProjectStar(project_id=project_id, user_id=user_id)
        db.add(new_star)
        db.commit()
        return True


def update_project(
    db: Session, project_id: int, project_data: ProjectUpdate
) -> Optional[Project]:
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        return None
    update_data = project_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project_id: int) -> Optional[Project]:
    """Deletes a project from the database."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    db.delete(project)
    db.commit()
    return project

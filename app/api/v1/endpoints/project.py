from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List

from app.schemas.project import Project, ProjectCreate, ProjectUpdate
from app.services import project_service
from app.api.dependencies import get_db, get_current_user, RoleChecker
from app.models.user import User, UserRole
from app.models.project import Project as ProjectModel, ProjectStar

router = APIRouter()

student_permission = RoleChecker([UserRole.student])
staff_permission = RoleChecker(
    [UserRole.admin, UserRole.sub_admin, UserRole.lab_head, UserRole.teacher]
)


def check_lab_permission(current_user: User, lab_id: int):
    if current_user.role in [UserRole.admin, UserRole.sub_admin]:
        return True
    if current_user.teacher_profile and current_user.teacher_profile.lab_id == lab_id:
        return True
    return False


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
def submit_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(student_permission),
):
    db_project = project_service.create_project(
        db=db, project_data=project, student_id=current_user.id
    )
    if db_project is None:
        raise HTTPException(
            status_code=403,
            detail="Submission failed: You are not enrolled in the specified cohort.",
        )

    response_project = Project(
        id=db_project.id,
        project_name=db_project.project_name,
        description=db_project.description,
        video_links=db_project.video_links,
        photo_urls=db_project.photo_urls,
        submission_date=db_project.submission_date,
        author=db_project.student,
        star_count=0,
    )
    return response_project


@router.get("/labs/{lab_id}/", response_model=List[Project])
def read_projects_in_lab(
    lab_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_permission),
):
    if not check_lab_permission(current_user, lab_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to view this lab's projects"
        )

    projects = project_service.get_projects_by_lab(db, lab_id=lab_id)
    return [
        Project(
            id=p.id,
            project_name=p.project_name,
            description=p.description,
            video_links=p.video_links,
            photo_urls=p.photo_urls,
            submission_date=p.submission_date,
            author=p.student,
            star_count=p.star_count,
        )
        for p in projects
    ]


@router.put("/{project_id}", response_model=Project)
def update_a_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(student_permission),
):
    """
    Update a project's details.
    - **Permissions**: The student who owns the project.
    """
    db_project = (
        db.query(ProjectModel)
        .options(joinedload(ProjectModel.student))
        .filter(ProjectModel.id == project_id)
        .first()
    )
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    if db_project.student_user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this project"
        )

    updated_project = project_service.update_project(
        db, project_id=project_id, project_data=project_data
    )

    star_count = (
        db.query(func.count(ProjectStar.id))
        .filter(ProjectStar.project_id == project_id)
        .scalar()
    )

    return Project(
        id=updated_project.id,
        project_name=updated_project.project_name,
        description=updated_project.description,
        video_links=updated_project.video_links,
        photo_urls=updated_project.photo_urls,
        submission_date=updated_project.submission_date,
        author=updated_project.student,
        star_count=star_count,
    )


@router.post("/{project_id}/star", status_code=status.HTTP_200_OK)
def star_a_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_permission),
):
    was_starred = project_service.star_unstar_project(
        db=db, project_id=project_id, user_id=current_user.id
    )
    if was_starred:
        return {"message": "Project starred successfully"}
    else:
        return {"message": "Project unstarred successfully"}


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_a_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a project.
    - **Permissions**: The student who owns the project, or an admin/sub-admin.
    """
    db_project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_owner = db_project.student_user_id == current_user.id
    is_admin = current_user.role in [UserRole.admin, UserRole.sub_admin]

    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this project"
        )

    project_service.delete_project(db, project_id=project_id)
    return None

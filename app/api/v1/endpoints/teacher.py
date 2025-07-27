from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.teacher import Teacher, TeacherCreate, TeacherUpdate
from app.services import teacher_service
from app.api.dependencies import get_db, get_current_user
from app.models.user import User, UserRole

router = APIRouter()


def check_lab_permission(current_user: User, lab_id: int):
    """
    Helper function to verify if a user has permission for a lab.
    Admins have universal access. Lab Heads must be assigned to the lab.
    """
    if current_user.role in [UserRole.admin, UserRole.sub_admin]:
        return True
    # FIX: Check for existence of teacher_profile before accessing its attributes
    if (
        current_user.role == UserRole.lab_head
        and current_user.teacher_profile
        and current_user.teacher_profile.lab_id == lab_id
    ):
        return True
    return False


@router.post(
    "/labs/{lab_id}/teachers/",
    response_model=Teacher,
    status_code=status.HTTP_201_CREATED,
)
def create_teacher(
    lab_id: int,
    teacher: TeacherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new teacher within a specific lab.
    - **Permissions**: admin, sub_admin, or the lab_head of the specified lab.
    """
    if not check_lab_permission(current_user, lab_id):
        raise HTTPException(status_code=403, detail="Not authorized to manage this lab")

    db_teacher = teacher_service.create_teacher_in_lab(
        db=db, teacher_data=teacher, lab_id=lab_id
    )
    if db_teacher is None:
        raise HTTPException(
            status_code=400, detail="A user with this mobile number already exists."
        )

    teacher_profile = db_teacher.teacher_profile
    skills = [skill.skill_name for skill in db_teacher.skills]
    return Teacher(
        user=db_teacher,
        lab_id=teacher_profile.lab_id,
        bio=teacher_profile.bio,
        date_of_joining=teacher_profile.date_of_joining,
        skills=skills,
    )


@router.get("/labs/{lab_id}/teachers/", response_model=List[Teacher])
def read_teachers_in_lab(
    lab_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all teachers for a specific lab.
    - **Permissions**: admin, sub_admin, or the lab_head of the specified lab.
    """
    if not check_lab_permission(current_user, lab_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to view this lab's teachers"
        )

    teachers = teacher_service.get_teachers_by_lab(db, lab_id=lab_id)
    response = []
    for user in teachers:
        teacher_profile = user.teacher_profile
        skills = [skill.skill_name for skill in user.skills]
        response.append(
            Teacher(
                user=user,
                lab_id=teacher_profile.lab_id,
                bio=teacher_profile.bio,
                date_of_joining=teacher_profile.date_of_joining,
                skills=skills,
            )
        )
    return response


@router.put("/{teacher_id}", response_model=Teacher)
def update_a_teacher(
    teacher_id: int,
    teacher_data: TeacherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a teacher's details.
    - **Permissions**: admin, sub_admin, or the lab_head of the teacher's lab.
    """
    target_teacher = teacher_service.get_teacher_profile(db, teacher_user_id=teacher_id)
    if not target_teacher or not target_teacher.teacher_profile:
        raise HTTPException(status_code=404, detail="Teacher not found")

    if not check_lab_permission(current_user, target_teacher.teacher_profile.lab_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to manage this teacher"
        )

    updated_teacher = teacher_service.update_teacher(
        db, teacher_user_id=teacher_id, teacher_data=teacher_data
    )

    # Manually construct the response model
    teacher_profile = updated_teacher.teacher_profile
    skills = [skill.skill_name for skill in updated_teacher.skills]
    return Teacher(
        user=updated_teacher,
        lab_id=teacher_profile.lab_id,
        bio=teacher_profile.bio,
        date_of_joining=teacher_profile.date_of_joining,
        skills=skills,
    )

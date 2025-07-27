from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.student import (
    Student,
    StudentBulkCreate,
    StudentUpdate,
)
from app.models.enrollment import EnrollmentCohort, StudentEnrollment
from app.services import student_service
from app.api.dependencies import get_db, get_current_user
from app.models.user import User, UserRole

router = APIRouter()


def check_lab_permission(current_user: User, lab_id: int):
    """
    Helper function to verify if a user has permission for a lab.
    Admins have universal access. Lab Heads and Teachers must be assigned to the lab.
    """
    if current_user.role in [UserRole.admin, UserRole.sub_admin]:
        return True

    # FIX: Check for existence of teacher_profile before accessing its attributes
    if current_user.role in [UserRole.lab_head, UserRole.teacher]:
        if (
            current_user.teacher_profile
            and current_user.teacher_profile.lab_id == lab_id
        ):
            return True

    return False


@router.post(
    "/labs/{lab_id}/students/bulk",
    response_model=List[Student],
    status_code=status.HTTP_201_CREATED,
)
def create_students_in_bulk(
    lab_id: int,
    bulk_data: StudentBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create multiple new students within a specific lab in a single transaction.
    - **Permissions**: admin, sub_admin, lab_head, or teacher of the specified lab.
    """
    if not check_lab_permission(current_user, lab_id):
        raise HTTPException(status_code=403, detail="Not authorized to manage this lab")

    try:
        created_users = student_service.bulk_create_students_in_lab(
            db=db, students_data=bulk_data.students, lab_id=lab_id
        )

        response = [
            Student(user=user, profile=user.student_profile) for user in created_users
        ]
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred during bulk creation."
        )


@router.get("/labs/{lab_id}/students/", response_model=List[Student])
def read_students_in_lab(
    lab_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all students for a specific lab.
    - **Permissions**: admin, sub_admin, lab_head, or teacher of the specified lab.
    """
    if not check_lab_permission(current_user, lab_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to view this lab's students"
        )

    users = student_service.get_students_by_lab(db, lab_id=lab_id)
    response = [Student(user=user, profile=user.student_profile) for user in users]
    return response


@router.put("/{student_id}", response_model=Student)
def update_a_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a student's details.
    - **Permissions**: admin, sub_admin, or a lab_head/teacher from a lab the student is enrolled in.
    """
    target_student = (
        db.query(User)
        .filter(User.id == student_id, User.role == UserRole.student)
        .first()
    )
    if not target_student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check permissions by finding which lab the student belongs to
    student_labs = (
        db.query(EnrollmentCohort.lab_id)
        .join(StudentEnrollment)
        .filter(StudentEnrollment.student_user_id == student_id)
        .distinct()
        .all()
    )
    student_lab_ids = {lab[0] for lab in student_labs}

    has_permission = any(
        check_lab_permission(current_user, lab_id) for lab_id in student_lab_ids
    )

    if not has_permission and current_user.role not in [
        UserRole.admin,
        UserRole.sub_admin,
    ]:
        raise HTTPException(
            status_code=403, detail="Not authorized to manage this student"
        )

    updated_student = student_service.update_student(
        db, student_user_id=student_id, student_data=student_data
    )
    return Student(user=updated_student, profile=updated_student.student_profile)

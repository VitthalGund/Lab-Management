from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.enrollment import (
    EnrollmentCohort as EnrollmentCohortSchema,
    EnrollmentCohortCreate,
    StudentEnrollmentCreate,
    EnrollmentCohortUpdate,
    StudentEnrollmentDetails,
    TeacherAssignmentDetails,
)
from app.services import enrollment_service
from app.api.dependencies import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.enrollment import EnrollmentCohort, StudentEnrollment

router = APIRouter()


def check_lab_permission(current_user: User, lab_id: int):
    """Helper to verify if a user has permission for a lab."""
    if current_user.role in [UserRole.admin, UserRole.sub_admin]:
        return True
    if current_user.teacher_profile and current_user.teacher_profile.lab_id == lab_id:
        return True
    return False


@router.post(
    "/labs/{lab_id}/cohorts/",
    response_model=EnrollmentCohortSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment_cohort(
    lab_id: int,
    cohort: EnrollmentCohortCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not check_lab_permission(current_user, lab_id):
        raise HTTPException(status_code=403, detail="Not authorized to manage this lab")
    return enrollment_service.create_cohort_in_lab(
        db=db, cohort_data=cohort, lab_id=lab_id, creator_id=current_user.id
    )


@router.get("/labs/{lab_id}/cohorts/", response_model=List[EnrollmentCohortSchema])
def read_cohorts_in_lab(
    lab_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not check_lab_permission(current_user, lab_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to view this lab's cohorts"
        )
    return enrollment_service.get_cohorts_by_lab(db, lab_id=lab_id)


@router.put("/cohorts/{cohort_id}", response_model=EnrollmentCohortSchema)
def update_a_cohort(
    cohort_id: int,
    cohort_data: EnrollmentCohortUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a cohort's details.
    - **Permissions**: admin, sub_admin, or a lab_head/teacher from the cohort's lab.
    """
    cohort = db.query(EnrollmentCohort).filter(EnrollmentCohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")
    if not check_lab_permission(current_user, cohort.lab_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to manage this cohort"
        )
    return enrollment_service.update_cohort(
        db, cohort_id=cohort_id, cohort_data=cohort_data
    )


@router.post("/cohorts/{cohort_id}/enroll/", status_code=status.HTTP_201_CREATED)
def enroll_students(
    cohort_id: int,
    enrollment_data: StudentEnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cohort = db.query(EnrollmentCohort).filter(EnrollmentCohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(
            status_code=404, detail=f"Cohort with id {cohort_id} not found."
        )
    if not check_lab_permission(current_user, cohort.lab_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to enroll students in this cohort"
        )
    try:
        enrollment_service.enroll_students_in_cohort(
            db=db, cohort_id=cohort_id, student_ids=enrollment_data.student_user_ids
        )
        return {"message": "Students enrolled successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me/", response_model=List[StudentEnrollmentDetails])
def read_my_enrollments(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get all cohort enrollments for the current student."""
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=403, detail="This endpoint is for students only"
        )
    return enrollment_service.get_student_enrollments(db, student_id=current_user.id)


@router.get("/teachers/me/assignments/", response_model=List[TeacherAssignmentDetails])
def read_my_assignments(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get all cohort assignments for the current teacher/lab head."""
    if current_user.role not in [UserRole.teacher, UserRole.lab_head]:
        raise HTTPException(
            status_code=403, detail="This endpoint is for teachers and lab heads only"
        )
    return enrollment_service.get_teacher_assignments(db, teacher_id=current_user.id)


@router.delete("/{enrollment_id}")
def unenroll_a_student(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Un-enroll a student from a cohort.
    - **Permissions**: admin, sub_admin, or a lab_head/teacher from the cohort's lab.
    """
    enrollment = (
        db.query(StudentEnrollment)
        .join(EnrollmentCohort)
        .filter(StudentEnrollment.id == enrollment_id)
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment record not found")

    if not check_lab_permission(current_user, enrollment.cohort.lab_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to manage this enrollment"
        )

    enrollment_service.unenroll_student(db, enrollment_id=enrollment_id)
    return {"message": "Student unenrolled successfully"}

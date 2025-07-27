from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.mark import Mark, MarkCreate, MarkUpdate
from app.services import mark_service
from app.api.dependencies import get_db, get_current_user, RoleChecker
from app.models.user import User, UserRole
from app.models.enrollment import StudentEnrollment, EnrollmentCohort
from app.models.mark import Mark as MarkModel

router = APIRouter()

staff_permission = RoleChecker(
    [UserRole.admin, UserRole.sub_admin, UserRole.lab_head, UserRole.teacher]
)
student_permission = RoleChecker([UserRole.student])


def check_staff_permission_for_enrollment(
    db: Session, current_user: User, enrollment_id: int
):
    enrollment = (
        db.query(StudentEnrollment)
        .join(EnrollmentCohort)
        .filter(StudentEnrollment.id == enrollment_id)
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment record not found")
    lab_id = enrollment.cohort.lab_id
    if current_user.role in [UserRole.admin, UserRole.sub_admin]:
        return True
    if current_user.teacher_profile and current_user.teacher_profile.lab_id == lab_id:
        return True
    raise HTTPException(
        status_code=403, detail="Not authorized to manage marks for this enrollment"
    )


@router.post(
    "/enrollments/{enrollment_id}/marks/",
    response_model=Mark,
    status_code=status.HTTP_201_CREATED,
)
def add_mark_to_enrollment(
    enrollment_id: int,
    mark: MarkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_permission),
):
    check_staff_permission_for_enrollment(db, current_user, enrollment_id)
    db_mark = mark_service.create_mark_for_enrollment(
        db=db, mark_data=mark, enrollment_id=enrollment_id
    )
    if db_mark is None:
        raise HTTPException(status_code=404, detail="Enrollment record not found")
    return db_mark


@router.get("/enrollments/{enrollment_id}/marks/", response_model=List[Mark])
def read_marks_for_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_permission),
):
    check_staff_permission_for_enrollment(db, current_user, enrollment_id)
    return mark_service.get_marks_for_enrollment(db=db, enrollment_id=enrollment_id)


@router.put("/marks/{mark_id}", response_model=Mark)
def update_a_mark(
    mark_id: int,
    mark_data: MarkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_permission),
):
    """
    Update a mark.
    - **Permissions**: admin, sub_admin, lab_head, teacher (of the correct lab)
    """
    db_mark = db.query(MarkModel).filter(MarkModel.id == mark_id).first()
    if not db_mark:
        raise HTTPException(status_code=404, detail="Mark not found")

    check_staff_permission_for_enrollment(db, current_user, db_mark.enrollment_id)

    return mark_service.update_mark(db, mark_id=mark_id, mark_data=mark_data)


@router.get("/me/marks/", response_model=List[Mark])
def read_my_marks(
    db: Session = Depends(get_db), current_user: User = Depends(student_permission)
):
    return mark_service.get_marks_for_student(db=db, student_id=current_user.id)

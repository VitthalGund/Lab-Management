from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.mark import Mark
from app.models.enrollment import StudentEnrollment
from app.schemas.mark import MarkCreate


def create_mark_for_enrollment(
    db: Session, mark_data: MarkCreate, enrollment_id: int
) -> Optional[Mark]:
    """
    Creates a new mark for a specific student enrollment.
    - Validates that the enrollment record exists.
    """
    # 1. Validate that the enrollment record exists
    enrollment = (
        db.query(StudentEnrollment)
        .filter(StudentEnrollment.id == enrollment_id)
        .first()
    )
    if not enrollment:
        return None  # Enrollment not found

    # 2. Create the mark
    db_mark = Mark(**mark_data.dict(), enrollment_id=enrollment_id)
    db.add(db_mark)
    db.commit()
    db.refresh(db_mark)
    return db_mark


def get_marks_for_student(db: Session, student_id: int) -> List[Mark]:
    """
    Retrieves all marks for a specific student across all their enrollments.
    """
    return (
        db.query(Mark)
        .join(StudentEnrollment)
        .filter(StudentEnrollment.student_user_id == student_id)
        .all()
    )


def get_marks_for_enrollment(db: Session, enrollment_id: int) -> List[Mark]:
    """
    Retrieves all marks for a specific enrollment record.
    """
    return db.query(Mark).filter(Mark.enrollment_id == enrollment_id).all()

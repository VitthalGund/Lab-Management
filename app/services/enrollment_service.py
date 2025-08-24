from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.models.user import User, UserRole
from app.schemas.enrollment import EnrollmentCohortCreate, EnrollmentCohortUpdate
from app.models.enrollment import EnrollmentCohort, StudentEnrollment, CohortTeacher


def generate_cohort_name(cohort_data: EnrollmentCohortCreate) -> str:
    """Generates a standardized cohort name."""
    name_parts = [
        cohort_data.academic_year.split("-")[0],
        cohort_data.section,
        f"{cohort_data.standard}th std",
    ]
    if cohort_data.specialization:
        name_parts.append(cohort_data.specialization)
    return ", ".join(name_parts)


def create_cohort_in_lab(
    db: Session, cohort_data: EnrollmentCohortCreate, lab_id: int, creator_id: int
) -> EnrollmentCohort:
    """
    Creates a new EnrollmentCohort in the database.
    """
    cohort_data.name = generate_cohort_name(cohort_data)
    db_cohort = EnrollmentCohort(
        **cohort_data.dict(), lab_id=lab_id, created_by_user_id=creator_id
    )
    db.add(db_cohort)
    db.commit()
    db.refresh(db_cohort)
    return db_cohort


def get_cohorts_by_lab(db: Session, lab_id: int) -> List[EnrollmentCohort]:
    """
    Retrieves all cohorts for a specific lab.
    """
    return db.query(EnrollmentCohort).filter(EnrollmentCohort.lab_id == lab_id).all()


def enroll_students_in_cohort(
    db: Session, cohort_id: int, student_ids: List[int]
) -> List[StudentEnrollment]:
    """
    Enrolls a list of students into a specific cohort.
    - Validates that the cohort exists.
    - Validates that all student IDs correspond to actual students.
    - Avoids creating duplicate enrollments.
    """
    # 1. Validate Cohort
    cohort = db.query(EnrollmentCohort).filter(EnrollmentCohort.id == cohort_id).first()
    if not cohort:
        raise ValueError(f"Cohort with id {cohort_id} not found.")

    # 2. Validate Students
    valid_students = (
        db.query(User)
        .filter(User.id.in_(student_ids), User.role == UserRole.student)
        .all()
    )
    if len(valid_students) != len(student_ids):
        found_ids = {s.id for s in valid_students}
        missing_ids = set(student_ids) - found_ids
        raise ValueError(
            f"The following student IDs were not found or are not students: {missing_ids}"
        )

    # 3. Avoid Duplicates
    existing_enrollments = (
        db.query(StudentEnrollment.student_user_id)
        .filter(
            StudentEnrollment.cohort_id == cohort_id,
            StudentEnrollment.student_user_id.in_(student_ids),
        )
        .all()
    )
    existing_student_ids = {e[0] for e in existing_enrollments}

    new_enrollments = []
    for student_id in student_ids:
        if student_id not in existing_student_ids:
            enrollment = StudentEnrollment(
                cohort_id=cohort_id, student_user_id=student_id
            )
            db.add(enrollment)
            new_enrollments.append(enrollment)

    db.commit()
    for enrollment in new_enrollments:
        db.refresh(enrollment)

    return new_enrollments


def update_cohort(
    db: Session, cohort_id: int, cohort_data: EnrollmentCohortUpdate
) -> Optional[EnrollmentCohort]:
    db_cohort = (
        db.query(EnrollmentCohort).filter(EnrollmentCohort.id == cohort_id).first()
    )
    if not db_cohort:
        return None
    update_data = cohort_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cohort, key, value)
    db.commit()
    db.refresh(db_cohort)
    return db_cohort


def get_student_enrollments(db: Session, student_id: int) -> List[StudentEnrollment]:
    """Retrieves all enrollments for a specific student."""
    return (
        db.query(StudentEnrollment)
        .options(joinedload(StudentEnrollment.cohort))
        .filter(StudentEnrollment.student_user_id == student_id)
        .all()
    )


def get_teacher_assignments(db: Session, teacher_id: int) -> List[CohortTeacher]:
    """Retrieves all cohort assignments for a specific teacher."""
    return (
        db.query(CohortTeacher)
        .options(joinedload(CohortTeacher.cohort))
        .filter(CohortTeacher.teacher_user_id == teacher_id)
        .all()
    )


def unenroll_student(db: Session, enrollment_id: int) -> Optional[StudentEnrollment]:
    """Un-enrolls a student by deleting the enrollment record."""
    enrollment = (
        db.query(StudentEnrollment)
        .filter(StudentEnrollment.id == enrollment_id)
        .first()
    )
    if not enrollment:
        return None
    db.delete(enrollment)
    db.commit()
    return enrollment

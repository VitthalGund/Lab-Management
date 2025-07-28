from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.models.user import User, UserRole, StudentProfile
from app.schemas.student import StudentCreate, StudentUpdate
from app.models.enrollment import (
    StudentEnrollment,
    EnrollmentCohort,
    LabSection,
)  # Import enrollment models
from app.core.security import get_password_hash


def bulk_create_students_in_lab(
    db: Session, students_data: List[StudentCreate], lab_id: int
) -> List[User]:
    """
    Creates multiple students in a single transaction.
    First, it validates that none of the mobile numbers already exist.
    """
    mobile_numbers = [s.mobile_number for s in students_data]
    existing_users = (
        db.query(User.mobile_number)
        .filter(User.mobile_number.in_(mobile_numbers))
        .all()
    )
    if existing_users:
        existing_numbers = {u.mobile_number for u in existing_users}
        raise ValueError(
            f"The following mobile numbers are already registered: {existing_numbers}"
        )

    new_users = []
    try:
        for student_data in students_data:
            hashed_password = get_password_hash(student_data.password)
            db_user = User(
                name=student_data.name,
                last_name=student_data.last_name,
                mobile_number=student_data.mobile_number,
                email=student_data.email,
                password_hash=hashed_password,
                role=UserRole.student,
                date_of_birth=student_data.date_of_birth,
                gender=student_data.gender,
                address=student_data.address,
            )
            db.add(db_user)
            db.flush()

            db_student_profile = StudentProfile(
                user_id=db_user.id,
                join_date_in_lab=student_data.join_date_in_lab,
                last_year_marks=student_data.last_year_marks,
                mother_name=student_data.mother_name,
                mother_contact=student_data.mother_contact,
                father_name=student_data.father_name,
                father_contact=student_data.father_contact,
            )
            db.add(db_student_profile)
            new_users.append(db_user)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    for user in new_users:
        db.refresh(user)

    return new_users


# def get_students_by_lab(db: Session, lab_id: int) -> List[User]:
#     """
#     FIX: Retrieves all students who are enrolled in any cohort belonging to the specified lab.
#     """
#     return (
#         db.query(User)
#         .options(joinedload(User.student_profile))
#         .join(StudentEnrollment, User.id == StudentEnrollment.student_user_id)
#         .join(EnrollmentCohort, StudentEnrollment.cohort_id == EnrollmentCohort.id)
#         .filter(EnrollmentCohort.lab_id == lab_id)
#         .distinct(User.id)
#         .all()
#     )


def update_student(
    db: Session, student_user_id: int, student_data: StudentUpdate
) -> Optional[User]:
    """
    Updates a student's user and profile details.
    """
    db_user = (
        db.query(User)
        .filter(User.id == student_user_id, User.role == UserRole.student)
        .first()
    )
    if not db_user:
        return None

    # Update User model fields
    user_update_data = student_data.dict(
        include={
            "name",
            "last_name",
            "mobile_number",
            "email",
            "date_of_birth",
            "gender",
            "address",
        },
        exclude_unset=True,
    )
    for key, value in user_update_data.items():
        setattr(db_user, key, value)

    # Update StudentProfile fields
    if db_user.student_profile:
        profile_update_data = student_data.dict(
            include={
                "join_date_in_lab",
                "last_year_marks",
                "mother_name",
                "mother_contact",
                "father_name",
                "father_contact",
            },
            exclude_unset=True,
        )
        for key, value in profile_update_data.items():
            setattr(db_user.student_profile, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def get_students_by_lab(
    db: Session,
    lab_id: int,
    standard: Optional[int] = None,
    section: Optional[LabSection] = None,
) -> List[User]:
    """
    Retrieves students in a lab, with optional filters for standard and section.
    """
    query = (
        db.query(User)
        .options(joinedload(User.student_profile))
        .join(StudentEnrollment, User.id == StudentEnrollment.student_user_id)
        .join(EnrollmentCohort, StudentEnrollment.cohort_id == EnrollmentCohort.id)
        .filter(EnrollmentCohort.lab_id == lab_id)
    )

    if standard:
        query = query.filter(EnrollmentCohort.standard == standard)
    if section:
        query = query.filter(EnrollmentCohort.section == section)

    return query.distinct(User.id).all()


def search_students(
    db: Session, school_id: Optional[int] = None, lab_id: Optional[int] = None
) -> List[User]:
    """
    Searches for students across the system with optional filters.
    """
    query = (
        db.query(User)
        .options(joinedload(User.student_profile))
        .filter(User.role == UserRole.student)
    )

    if lab_id:
        query = (
            query.join(StudentEnrollment)
            .join(EnrollmentCohort)
            .filter(EnrollmentCohort.lab_id == lab_id)
        )
    elif school_id:
        query = (
            query.join(StudentEnrollment)
            .join(EnrollmentCohort)
            .filter(EnrollmentCohort.lab.has(school_id=school_id))
        )

    return query.distinct(User.id).all()

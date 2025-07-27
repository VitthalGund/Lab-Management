from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.models.user import User, UserRole, TeacherProfile, TeacherSkill
from app.schemas.teacher import TeacherCreate, TeacherUpdate
from app.services import user_service
from app.core.security import get_password_hash


def create_teacher_in_lab(
    db: Session, teacher_data: TeacherCreate, lab_id: int
) -> Optional[User]:
    """
    Creates a new teacher, including their user account and profile,
    and links them to a specific lab.
    """
    # Check if a user with this mobile number already exists
    if user_service.get_user_by_mobile(db, mobile_number=teacher_data.mobile_number):
        return None  # Indicate that the user already exists

    # Create the base user account
    hashed_password = get_password_hash(teacher_data.password)
    db_user = User(
        name=teacher_data.name,
        last_name=teacher_data.last_name,
        mobile_number=teacher_data.mobile_number,
        email=teacher_data.email,
        password_hash=hashed_password,
        role=UserRole.teacher,
        date_of_birth=teacher_data.date_of_birth,
        gender=teacher_data.gender,
        address=teacher_data.address,
    )
    db.add(db_user)
    db.flush()  # Use flush to get the db_user.id before commit

    # Create the teacher profile
    db_teacher_profile = TeacherProfile(
        user_id=db_user.id,
        lab_id=lab_id,
        bio=teacher_data.bio,
        date_of_joining=teacher_data.date_of_joining,
    )
    db.add(db_teacher_profile)

    # Add skills
    if teacher_data.skills:
        for skill_name in teacher_data.skills:
            db_skill = TeacherSkill(user_id=db_user.id, skill_name=skill_name)
            db.add(db_skill)

    db.commit()
    db.refresh(db_user)
    return db_user


def get_teachers_by_lab(db: Session, lab_id: int) -> List[User]:
    """
    Retrieves all teachers associated with a specific lab.
    """
    return (
        db.query(User)
        .join(TeacherProfile)
        .filter(TeacherProfile.lab_id == lab_id)
        .all()
    )


def get_teacher_profile(db: Session, teacher_user_id: int) -> Optional[User]:
    """
    Retrieves a single teacher's full profile.
    """
    return (
        db.query(User)
        .options(joinedload(User.teacher_profile), joinedload(User.skills))
        .filter(User.id == teacher_user_id, User.role == UserRole.teacher)
        .first()
    )


def update_teacher(
    db: Session, teacher_user_id: int, teacher_data: TeacherUpdate
) -> Optional[User]:
    """
    Updates a teacher's user and profile details.
    """
    db_user = (
        db.query(User)
        .filter(User.id == teacher_user_id, User.role == UserRole.teacher)
        .first()
    )
    if not db_user:
        return None

    # Update User model fields
    user_update_data = teacher_data.dict(
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

    # Update TeacherProfile fields
    if db_user.teacher_profile:
        profile_update_data = teacher_data.dict(
            include={"bio", "date_of_joining"}, exclude_unset=True
        )
        for key, value in profile_update_data.items():
            setattr(db_user.teacher_profile, key, value)

    # Update skills (replace all existing skills)
    if teacher_data.skills is not None:
        # Delete old skills
        db.query(TeacherSkill).filter(TeacherSkill.user_id == teacher_user_id).delete()
        # Add new skills
        for skill_name in teacher_data.skills:
            db.add(TeacherSkill(user_id=teacher_user_id, skill_name=skill_name))

    db.commit()
    db.refresh(db_user)
    return db_user

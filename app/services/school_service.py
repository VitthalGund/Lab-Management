from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.school import School
from app.schemas.school import SchoolCreate, SchoolUpdate


def get_school(db: Session, school_id: int) -> Optional[School]:
    """
    Retrieves a single school by its ID.
    """
    return db.query(School).filter(School.id == school_id).first()


def get_schools(db: Session, skip: int = 0, limit: int = 100) -> List[School]:
    """
    Retrieves a list of schools with pagination.
    """
    return db.query(School).offset(skip).limit(limit).all()


def create_school(db: Session, school: SchoolCreate) -> School:
    """
    Creates a new school in the database.
    """
    db_school = School(**school.dict())
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school


def update_school(
    db: Session, school_id: int, school_update: SchoolUpdate
) -> Optional[School]:
    """
    Updates an existing school's details.
    """
    db_school = get_school(db, school_id)
    if not db_school:
        return None

    update_data = school_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_school, key, value)

    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school


def delete_school(db: Session, school_id: int) -> Optional[School]:
    """
    Deletes a school from the database.
    """
    db_school = get_school(db, school_id)
    if not db_school:
        return None

    db.delete(db_school)
    db.commit()
    return db_school

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.models.lab import Lab
from app.schemas.lab import LabCreate, LabUpdate
from app.services import school_service  # To verify school existence


def get_lab(db: Session, lab_id: int) -> Optional[Lab]:
    """
    Retrieves a single lab by its ID, including its related school data.
    """
    return (
        db.query(Lab).options(joinedload(Lab.school)).filter(Lab.id == lab_id).first()
    )


def get_all_labs(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: str = None,
    school_id: int = None,
):
    query = db.query(Lab)
    if search:
        query = query.filter(Lab.name.ilike(f"%{search}%"))
    if school_id:
        query = query.filter(Lab.school_id == school_id)

    total = query.count()
    labs = query.offset(skip).limit(limit).all()
    return labs, total


def get_labs(db: Session, skip: int = 0, limit: int = 100) -> List[Lab]:
    """
    Retrieves a list of labs with pagination, including related school data.
    """
    return db.query(Lab).options(joinedload(Lab.school)).offset(skip).limit(limit).all()


def create_lab(db: Session, lab: LabCreate) -> Optional[Lab]:
    """
    Creates a new lab in the database.
    Returns None if the specified school does not exist.
    """
    # Verify that the school exists
    db_school = school_service.get_school(db, school_id=lab.school_id)
    if not db_school:
        return None

    db_lab = Lab(**lab.dict())
    db.add(db_lab)
    db.commit()
    db.refresh(db_lab)
    return db_lab


def update_lab(db: Session, lab_id: int, lab_update: LabUpdate) -> Optional[Lab]:
    """
    Updates an existing lab's details.
    """
    db_lab = get_lab(db, lab_id)
    if not db_lab:
        return None

    update_data = lab_update.dict(exclude_unset=True)

    # If school_id is being updated, verify the new school exists
    if "school_id" in update_data:
        db_school = school_service.get_school(db, school_id=update_data["school_id"])
        if not db_school:
            # Or raise an exception indicating the new school is not found
            return None

    for key, value in update_data.items():
        setattr(db_lab, key, value)

    db.add(db_lab)
    db.commit()
    db.refresh(db_lab)
    return db_lab


def delete_lab(db: Session, lab_id: int) -> Optional[Lab]:
    """
    Deletes a lab from the database.
    """
    db_lab = get_lab(db, lab_id)
    if not db_lab:
        return None

    db.delete(db_lab)
    db.commit()
    return db_lab

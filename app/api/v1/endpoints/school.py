from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.school import School, SchoolCreate, SchoolUpdate
from app.services import school_service
from app.api.dependencies import get_db, RoleChecker
from app.models.user import User, UserRole

router = APIRouter()

# Dependency to enforce admin/sub-admin roles
admin_permission = RoleChecker([UserRole.admin, UserRole.sub_admin])


@router.post("/", response_model=School, status_code=status.HTTP_201_CREATED)
def create_school(
    school: SchoolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),
):
    """
    Create a new school.
    - **Permissions**: admin, sub_admin
    """
    return school_service.create_school(db=db, school=school)


@router.get("/", response_model=List[School])
def read_schools(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),
):
    """
    Retrieve a list of all schools.
    - **Permissions**: admin, sub_admin
    """
    schools = school_service.get_schools(db, skip=skip, limit=limit)
    return schools


@router.get("/{school_id}", response_model=School)
def read_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),
):
    """
    Retrieve a single school by its ID.
    - **Permissions**: admin, sub_admin
    """
    db_school = school_service.get_school(db, school_id=school_id)
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return db_school


@router.put("/{school_id}", response_model=School)
def update_school(
    school_id: int,
    school_update: SchoolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),
):
    """
    Update a school's details.
    - **Permissions**: admin, sub_admin
    """
    db_school = school_service.update_school(
        db, school_id=school_id, school_update=school_update
    )
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return db_school


@router.delete("/{school_id}", response_model=School)
def delete_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),
):
    """
    Delete a school.
    - **Permissions**: admin, sub_admin
    """
    db_school = school_service.delete_school(db, school_id=school_id)
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return db_school

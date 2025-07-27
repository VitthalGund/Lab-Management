from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.lab import Lab, LabCreate, LabUpdate
from app.services import lab_service
from app.api.dependencies import get_db, RoleChecker
from app.models.user import User, UserRole

router = APIRouter()

# Dependency to enforce admin/sub-admin roles
admin_permission = RoleChecker([UserRole.admin, UserRole.sub_admin])


@router.post("/", response_model=Lab, status_code=status.HTTP_201_CREATED)
def create_lab(
    lab: LabCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),
):
    """
    Create a new lab.
    - **Permissions**: admin, sub_admin
    """
    db_lab = lab_service.create_lab(db=db, lab=lab)
    if db_lab is None:
        raise HTTPException(
            status_code=404, detail=f"School with id {lab.school_id} not found"
        )
    return db_lab


@router.get("/", response_model=List[Lab])
def read_labs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),
):
    """
    Retrieve a list of all labs.
    - **Permissions**: admin, sub_admin
    """
    labs = lab_service.get_labs(db, skip=skip, limit=limit)
    return labs


@router.get("/{lab_id}", response_model=Lab)
def read_lab(
    lab_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),
):
    """
    Retrieve a single lab by its ID.
    - **Permissions**: admin, sub_admin
    """
    db_lab = lab_service.get_lab(db, lab_id=lab_id)
    if db_lab is None:
        raise HTTPException(status_code=404, detail="Lab not found")
    return db_lab


@router.put("/{lab_id}", response_model=Lab)
def update_lab(
    lab_id: int,
    lab_update: LabUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),
):
    """
    Update a lab's details.
    - **Permissions**: admin, sub_admin
    """
    db_lab = lab_service.update_lab(db, lab_id=lab_id, lab_update=lab_update)
    if db_lab is None:
        raise HTTPException(
            status_code=404, detail="Lab not found or invalid school_id provided"
        )
    return db_lab


@router.delete("/{lab_id}", response_model=Lab)
def delete_lab(
    lab_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),
):
    """
    Delete a lab.
    - **Permissions**: admin, sub_admin
    """
    db_lab = lab_service.delete_lab(db, lab_id=lab_id)
    if db_lab is None:
        raise HTTPException(status_code=404, detail="Lab not found")
    return db_lab

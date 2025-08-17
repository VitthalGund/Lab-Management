from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.schemas.user import (
    User as UserSchema,
    UserMeUpdate,
    UserPasswordChange,
    AdminPasswordReset,
    UserUpdate,
    PaginatedUsersResponse,
)
from app.services import user_service
from app.api.dependencies import get_db, get_current_user, RoleChecker
from app.models.user import User, UserRole, TeacherProfile
from app.models.lab import Lab
from app.models.enrollment import StudentEnrollment, EnrollmentCohort

router = APIRouter()
admin_permission = RoleChecker([UserRole.admin, UserRole.sub_admin])


@router.get("/me/", response_model=UserSchema)
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Get the profile of the currently authenticated user.
    """
    return current_user


@router.put("/me/", response_model=UserSchema)
def update_current_user(
    data: UserMeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the profile of the currently authenticated user."""
    return user_service.update_me(db=db, user=current_user, data=data)


@router.post("/me/change-password")
def change_current_user_password(
    data: UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the password of the currently authenticated user."""
    success = user_service.change_password(db=db, user=current_user, data=data)
    if not success:
        raise HTTPException(status_code=400, detail="Incorrect current password")
    return {"message": "Password changed successfully"}


@router.post("/{user_id}/reset-password", status_code=status.HTTP_200_OK)
def reset_password_by_superior(
    user_id: int,
    data: AdminPasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reset a user's password. Permissions are hierarchical.
    - Admins can reset any non-admin user.
    - Lab Heads can reset teachers and students in their lab.
    - Teachers can reset students in their lab.
    """
    target_user = user_service.get_user_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.id == target_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot reset your own password using this endpoint. Use /me/change-password instead.",
        )

    has_permission = False
    current_role = current_user.role
    target_role = target_user.role

    # Admin/Sub-admin logic
    if current_role in [UserRole.admin, UserRole.sub_admin]:
        if target_role != UserRole.admin:
            has_permission = True
        else:
            raise HTTPException(
                status_code=403, detail="Admins cannot reset other admins' passwords."
            )

    # Lab Head logic
    elif current_role == UserRole.lab_head:
        if target_role in [UserRole.teacher, UserRole.student]:
            lab_id = (
                current_user.teacher_profile.lab_id
                if current_user.teacher_profile
                else None
            )
            if lab_id:
                if (
                    target_role == UserRole.teacher
                    and target_user.teacher_profile
                    and target_user.teacher_profile.lab_id == lab_id
                ):
                    has_permission = True
                elif target_role == UserRole.student:
                    is_in_lab = (
                        db.query(StudentEnrollment)
                        .join(EnrollmentCohort)
                        .filter(
                            StudentEnrollment.student_user_id == target_user.id,
                            EnrollmentCohort.lab_id == lab_id,
                        )
                        .first()
                    )
                    if is_in_lab:
                        has_permission = True

    # Teacher logic
    elif current_role == UserRole.teacher:
        if target_role == UserRole.student:
            lab_id = (
                current_user.teacher_profile.lab_id
                if current_user.teacher_profile
                else None
            )
            if lab_id:
                is_in_lab = (
                    db.query(StudentEnrollment)
                    .join(EnrollmentCohort)
                    .filter(
                        StudentEnrollment.student_user_id == target_user.id,
                        EnrollmentCohort.lab_id == lab_id,
                    )
                    .first()
                )
                if is_in_lab:
                    has_permission = True

    if not has_permission:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to reset this user's password.",
        )

    user_service.reset_user_password(
        db, user=target_user, new_password=data.new_password
    )
    return {
        "message": f"Password for user {target_user.name} has been reset successfully."
    }


@router.get("/", response_model=List[UserSchema])
def read_all_users(
    db: Session = Depends(get_db), current_user: User = Depends(admin_permission)
):
    """Retrieve all users. Admin only."""
    # This requires a new service function, for now we can do a simple query
    return db.query(User).all()


@router.put("/{user_id}", response_model=UserSchema)
def update_user_details(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),
):
    """Update a user's details. Admin only."""
    user_to_update = user_service.get_user_by_id(db, user_id=user_id)
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    return user_service.update_user_by_admin(db, user=user_to_update, data=data)


@router.delete("/{user_id}", response_model=UserSchema)
def delete_a_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_permission),
):
    """Delete a user. Admin only."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Admins cannot delete their own account."
        )
    deleted_user = user_service.delete_user_by_id(db, user_id=user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted_user


@router.get("/search/", response_model=PaginatedUsersResponse)
def search_for_users(
    role: Optional[UserRole] = None,
    school_id: Optional[int] = None,
    lab_id: Optional[int] = None,
    name: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search for users with advanced filters and pagination.
    """
    query = db.query(User).options(
        joinedload(User.teacher_profile), joinedload(User.student_profile)
    )

    if role:
        query = query.filter(User.role == role)

    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))

    if lab_id:
        if role in [UserRole.teacher, UserRole.lab_head]:
            query = query.join(TeacherProfile).filter(TeacherProfile.lab_id == lab_id)
        elif role == UserRole.student:
            query = (
                query.join(StudentEnrollment)
                .join(EnrollmentCohort)
                .filter(EnrollmentCohort.lab_id == lab_id)
            )
    elif school_id:
        if role in [UserRole.teacher, UserRole.lab_head]:
            query = (
                query.join(TeacherProfile).join(Lab).filter(Lab.school_id == school_id)
            )
        elif role == UserRole.student:
            query = (
                query.join(StudentEnrollment)
                .join(EnrollmentCohort)
                .join(Lab)
                .filter(Lab.school_id == school_id)
            )

    if current_user.role not in [UserRole.admin, UserRole.sub_admin]:
        user_lab_id = (
            current_user.teacher_profile.lab_id
            if current_user.teacher_profile
            else None
        )
        if not user_lab_id:
            raise HTTPException(
                status_code=403, detail="You are not assigned to a lab."
            )

        if role in [UserRole.teacher, UserRole.lab_head, UserRole.student]:
            query = (
                query.join(TeacherProfile).filter(TeacherProfile.lab_id == user_lab_id)
                if role != UserRole.student
                else query.join(StudentEnrollment)
                .join(EnrollmentCohort)
                .filter(EnrollmentCohort.lab_id == user_lab_id)
            )
        else:
            raise HTTPException(
                status_code=403, detail="You do not have permission to view this role."
            )

    total = query.distinct(User.id).count()
    users = query.distinct(User.id).offset(skip).limit(limit).all()

    return {"users": users, "total": total}

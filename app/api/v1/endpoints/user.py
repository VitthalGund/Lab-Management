from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.user import (
    User as UserSchema,
    UserMeUpdate,
    UserPasswordChange,
    AdminPasswordReset,
)
from app.services import user_service
from app.api.dependencies import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.enrollment import StudentEnrollment, EnrollmentCohort

router = APIRouter()


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

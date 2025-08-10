from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserMeUpdate, UserPasswordChange, UserUpdate
from app.core.security import get_password_hash, verify_password


def get_user_by_mobile(db: Session, mobile_number: str) -> User | None:
    """Fetches a user by their mobile number."""
    return db.query(User).filter(User.mobile_number == mobile_number).first()


def create_user(db: Session, user: UserCreate) -> User:
    """Creates a new user in the database."""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        name=user.name,
        last_name=user.last_name,
        mobile_number=user.mobile_number,
        email=user.email,
        role=user.role,
        password_hash=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_me(db: Session, user: User, data: UserMeUpdate) -> User:
    """Updates the current user's profile."""
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, data: UserPasswordChange) -> bool:
    """Changes the current user's password."""
    if not verify_password(data.current_password, user.password_hash):
        return False
    user.password_hash = get_password_hash(data.new_password)
    db.add(user)
    db.commit()
    return True


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Fetches a user by their ID."""
    return db.query(User).filter(User.id == user_id).first()


def reset_user_password(db: Session, user: User, new_password: str) -> User:
    """
    Forcefully resets a user's password by an admin or superior.
    This function does not check for the old password.
    """
    user.password_hash = get_password_hash(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_by_admin(db: Session, user: User, data: UserUpdate) -> User:
    """Updates a user's details by an admin."""
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user_by_id(db: Session, user_id: int) -> User | None:
    """Deletes a user by their ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return user

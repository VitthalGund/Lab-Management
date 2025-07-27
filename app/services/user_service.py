from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


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

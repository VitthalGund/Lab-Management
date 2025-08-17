import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Enum as SQLAlchemyEnum,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    sub_admin = "sub_admin"
    lab_head = "lab_head"
    teacher = "teacher"
    student = "student"


class PerformanceStatus(str, enum.Enum):
    excellent = "Excellent"
    satisfactory = "Satisfactory"
    needs_improvement = "Needs Improvement"


class User(Base):
    """
    Represents a user in the system, can be any role.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    mobile_number = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    address = Column(Text, nullable=True)

    # One-to-one relationships
    teacher_profile = relationship(
        "TeacherProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    student_profile = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # One-to-many relationships
    skills = relationship(
        "TeacherSkill", back_populates="user", cascade="all, delete-orphan"
    )
    projects_submitted = relationship("Project", back_populates="student")
    stars_given = relationship("ProjectStar", back_populates="user")
    enrollments = relationship("StudentEnrollment", back_populates="student")
    cohorts_created = relationship("EnrollmentCohort", back_populates="creator")
    cohorts_taught = relationship("CohortTeacher", back_populates="teacher")


class TeacherProfile(Base):
    """
    Stores additional details specific to teachers.
    """

    __tablename__ = "teacher_profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=True)
    photo_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    date_of_joining = Column(Date, nullable=True)

    user = relationship("User", back_populates="teacher_profile")
    lab = relationship("Lab", back_populates="teacher_profiles")


class TeacherSkill(Base):
    """
    Stores individual skills for a teacher.
    """

    __tablename__ = "teacher_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_name = Column(String, nullable=False)

    user = relationship("User", back_populates="skills")


class StudentProfile(Base):
    """
    Stores additional details specific to students.
    """

    __tablename__ = "student_profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    join_date_in_lab = Column(Date, nullable=True)
    last_year_marks = Column(String, nullable=True)
    performance_status = Column(SQLAlchemyEnum(PerformanceStatus), nullable=True)
    mother_name = Column(String, nullable=True)
    mother_contact = Column(String, nullable=True)
    father_name = Column(String, nullable=True)
    father_contact = Column(String, nullable=True)

    user = relationship("User", back_populates="student_profile")

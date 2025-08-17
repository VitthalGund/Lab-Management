import enum
from sqlalchemy import Column, Integer, String, Date, Enum as SQLAlchemyEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class LabSection(str, enum.Enum):
    cflc = "CFLC"
    grok = "GROK"


class GrokSpecialization(str, enum.Enum):
    iot = "IOT"
    robotics = "Robotics"
    three_d_printing = "3D Printing"
    abc_of_technology = "ABC of Technology"


class EnrollmentCohort(Base):
    """
    Represents a specific batch of students for a given year, semester, etc.
    This is the unique identifier for a group.
    """

    __tablename__ = "enrollment_cohorts"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False)
    academic_year = Column(Integer, nullable=False)
    section = Column(SQLAlchemyEnum(LabSection), nullable=False)
    standard = Column(Integer, nullable=False)
    semester_start_date = Column(Date, nullable=True)
    semester_end_date = Column(Date, nullable=True)
    batch_name = Column(String, nullable=True)
    grok_specialization = Column(SQLAlchemyEnum(GrokSpecialization), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    lab = relationship("Lab", back_populates="enrollment_cohorts")
    creator = relationship("User", back_populates="cohorts_created")

    student_enrollments = relationship(
        "StudentEnrollment", back_populates="cohort", cascade="all, delete-orphan"
    )
    teachers_assigned = relationship(
        "CohortTeacher", back_populates="cohort", cascade="all, delete-orphan"
    )
    projects = relationship(
        "Project", back_populates="cohort", cascade="all, delete-orphan"
    )


class StudentEnrollment(Base):
    """
    Junction table linking a student to a specific cohort.
    """

    __tablename__ = "student_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cohort_id = Column(Integer, ForeignKey("enrollment_cohorts.id"), nullable=False)

    student = relationship("User", back_populates="enrollments")
    cohort = relationship("EnrollmentCohort", back_populates="student_enrollments")
    marks = relationship(
        "Mark", back_populates="enrollment", cascade="all, delete-orphan"
    )


class CohortTeacher(Base):
    """
    Junction table linking a teacher to a specific cohort they are teaching.
    """

    __tablename__ = "cohort_teachers"

    id = Column(Integer, primary_key=True, index=True)
    teacher_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cohort_id = Column(Integer, ForeignKey("enrollment_cohorts.id"), nullable=False)

    teacher = relationship("User", back_populates="cohorts_taught")
    cohort = relationship("EnrollmentCohort", back_populates="teachers_assigned")

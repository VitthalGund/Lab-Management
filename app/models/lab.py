from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Lab(Base):
    """
    Represents a lab entity in the database.
    """

    __tablename__ = "labs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    school = relationship("School", back_populates="labs")

    teacher_profiles = relationship(
        "TeacherProfile", back_populates="lab", cascade="all, delete-orphan"
    )
    enrollment_cohorts = relationship(
        "EnrollmentCohort", back_populates="lab", cascade="all, delete-orphan"
    )

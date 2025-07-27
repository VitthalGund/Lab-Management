from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Lab(Base):
    """
    Represents a lab entity, linked to a school.
    """

    __tablename__ = "labs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    start_date = Column(Date, nullable=True)

    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    # Relationship to School: A lab belongs to one school.
    school = relationship("School", back_populates="labs")

    # Relationship to TeacherProfile: A lab has multiple teachers.
    teachers = relationship("TeacherProfile", back_populates="lab")

    # Relationship to EnrollmentCohort: A lab has multiple cohorts.
    enrollment_cohorts = relationship("EnrollmentCohort", back_populates="lab")

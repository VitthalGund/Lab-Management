from sqlalchemy import Column, Integer, String, Date, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Mark(Base):
    """
    Stores marks for a student for a specific assessment.
    """

    __tablename__ = "marks"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(
        Integer, ForeignKey("student_enrollments.id"), nullable=False
    )
    assessment_name = Column(String, nullable=False)
    marks_obtained = Column(DECIMAL(5, 2), nullable=False)
    total_marks = Column(DECIMAL(5, 2), nullable=False)
    date_recorded = Column(Date, server_default=func.now())

    enrollment = relationship("StudentEnrollment", back_populates="marks")

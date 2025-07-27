from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Project(Base):
    """
    Represents a project submitted by a student.
    """

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    student_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cohort_id = Column(Integer, ForeignKey("enrollment_cohorts.id"), nullable=False)
    project_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    video_links = Column(JSON, nullable=True)
    photo_urls = Column(JSON, nullable=True)
    submission_date = Column(DateTime, nullable=False, server_default=func.now())

    student = relationship("User", back_populates="projects_submitted")
    cohort = relationship("EnrollmentCohort", back_populates="projects")
    stars = relationship(
        "ProjectStar", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectStar(Base):
    """
    Represents a 'star' or 'like' given to a project by a user.
    """

    __tablename__ = "project_stars"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    starred_at = Column(DateTime, nullable=False, server_default=func.now())

    project = relationship("Project", back_populates="stars")
    user = relationship("User", back_populates="stars_given")

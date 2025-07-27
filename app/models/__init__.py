# This file makes it easy to import all models from a single point.
# It's particularly useful for Alembic migrations.

from app.db.base import Base
from .school import School
from .lab import Lab
from .user import User, TeacherProfile, TeacherSkill, StudentProfile
from .enrollment import EnrollmentCohort, StudentEnrollment, CohortTeacher
from .project import Project, ProjectStar
from .mark import Mark

from fastapi import APIRouter
from app.api.v1.endpoints import (
    dashboard,
    auth,
    school,
    lab,
    teacher,
    student,
    enrollment,
    project,
    mark,
    report,
    user,
)

api_router = APIRouter()

# Authentication and User Self-Service
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(user.router, prefix="/users", tags=["Users"])

# Dashboards and Reports
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(report.router, prefix="/reports", tags=["Reports"])

# Core Data Management
api_router.include_router(school.router, prefix="/schools", tags=["Schools"])
api_router.include_router(lab.router, prefix="/labs", tags=["Labs"])
api_router.include_router(teacher.router, prefix="/teachers", tags=["Teachers"])
api_router.include_router(student.router, prefix="/students", tags=["Students"])

# Academic and Engagement Management
api_router.include_router(
    enrollment.router, prefix="/enrollments", tags=["Enrollments & Cohorts"]
)
api_router.include_router(project.router, prefix="/projects", tags=["Projects"])
api_router.include_router(mark.router, prefix="/marks", tags=["Marks"])

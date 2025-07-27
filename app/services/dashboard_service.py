from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta

from app.schemas.dashboard import (
    KPIStats,
    LabDashboardStats,
    ChartDataPoint,
    TrendDataPoint,
    TopStudent,
    TopProject,
)
from app.models import (
    User,
    StudentEnrollment,
    EnrollmentCohort,
    Project,
    ProjectStar,
    TeacherProfile,
    StudentProfile,
)
from app.models.user import UserRole, PerformanceStatus
from app.models.enrollment import LabSection


def get_lab_dashboard_stats(db: Session, lab_id: int) -> LabDashboardStats:
    """
    Computes and returns all statistics for the lab dashboard.
    """
    # --- 1. KPI Calculations ---

    # Total active students in the lab
    total_students = (
        db.query(func.count(StudentEnrollment.student_user_id.distinct()))
        .join(EnrollmentCohort)
        .filter(EnrollmentCohort.lab_id == lab_id)
        .scalar()
    )

    # Total teachers assigned to the lab
    total_teachers = (
        db.query(func.count(TeacherProfile.user_id))
        .filter(TeacherProfile.lab_id == lab_id)
        .scalar()
    )

    # Total projects submitted from the lab
    total_projects = (
        db.query(func.count(Project.id))
        .join(EnrollmentCohort)
        .filter(EnrollmentCohort.lab_id == lab_id)
        .scalar()
    )

    # Total stars received by projects in the lab
    total_stars = (
        db.query(func.count(ProjectStar.id))
        .join(Project)
        .join(EnrollmentCohort)
        .filter(EnrollmentCohort.lab_id == lab_id)
        .scalar()
    )

    kpis = KPIStats(
        total_students=total_students or 0,
        total_teachers=total_teachers or 0,
        total_projects=total_projects or 0,
        total_stars=total_stars or 0,
    )

    # --- 2. Data for Charts ---

    # Student distribution by section (CFLC vs GROK)
    student_dist_query = (
        db.query(
            EnrollmentCohort.section,
            func.count(StudentEnrollment.student_user_id.distinct()),
        )
        .join(StudentEnrollment)
        .filter(EnrollmentCohort.lab_id == lab_id)
        .group_by(EnrollmentCohort.section)
        .all()
    )
    student_distribution = [
        ChartDataPoint(name=row[0].value, value=row[1]) for row in student_dist_query
    ]

    # GROK specialization breakdown
    grok_spec_query = (
        db.query(
            EnrollmentCohort.grok_specialization,
            func.count(StudentEnrollment.student_user_id.distinct()),
        )
        .join(StudentEnrollment)
        .filter(
            EnrollmentCohort.lab_id == lab_id,
            EnrollmentCohort.section == LabSection.grok,
        )
        .group_by(EnrollmentCohort.grok_specialization)
        .all()
    )
    grok_specialization = [
        ChartDataPoint(name=row[0].value, value=row[1])
        for row in grok_spec_query
        if row[0]
    ]

    # Student performance status distribution
    perf_dist_query = (
        db.query(StudentProfile.performance_status, func.count(StudentProfile.user_id))
        .join(User)
        .join(StudentEnrollment, User.id == StudentEnrollment.student_user_id)
        .join(EnrollmentCohort, StudentEnrollment.cohort_id == EnrollmentCohort.id)
        .filter(EnrollmentCohort.lab_id == lab_id)
        .group_by(StudentProfile.performance_status)
        .all()
    )
    performance_distribution = [
        ChartDataPoint(name=row[0].value, value=row[1])
        for row in perf_dist_query
        if row[0]
    ]

    # --- 3. Project Submission Trend (Last 12 months) ---
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)
    project_trend_query = (
        db.query(
            func.to_char(Project.submission_date, "YYYY-MM").label("month"),
            func.count(Project.id).label("count"),
        )
        .join(EnrollmentCohort)
        .filter(
            EnrollmentCohort.lab_id == lab_id,
            Project.submission_date >= twelve_months_ago,
        )
        .group_by("month")
        .order_by("month")
        .all()
    )
    project_trend = [
        TrendDataPoint(month=row.month, count=row.count) for row in project_trend_query
    ]

    # --- 4. Leaderboards (Top 5) ---

    # Top students (by stars + projects)
    top_students_query = (
        db.query(
            User.id,
            (User.name + " " + User.last_name).label("full_name"),
            func.count(func.distinct(Project.id)).label("project_count"),
            func.count(func.distinct(ProjectStar.id)).label("star_count"),
        )
        .select_from(User)
        .join(StudentEnrollment, User.id == StudentEnrollment.student_user_id)
        .join(EnrollmentCohort, StudentEnrollment.cohort_id == EnrollmentCohort.id)
        .outerjoin(Project, User.id == Project.student_user_id)
        .outerjoin(ProjectStar, Project.id == ProjectStar.project_id)
        .filter(EnrollmentCohort.lab_id == lab_id, User.role == UserRole.student)
        .group_by(User.id, "full_name")
        .order_by(
            func.count(func.distinct(ProjectStar.id)).desc(),
            func.count(func.distinct(Project.id)).desc(),
        )
        .limit(5)
        .all()
    )
    top_students = [
        TopStudent(
            student_id=row[0],
            student_name=row[1],
            projects_submitted=row[2],
            stars_received=row[3],
        )
        for row in top_students_query
    ]

    # Top projects (by stars)
    top_projects_query = (
        db.query(
            Project.id,
            Project.project_name,
            (User.name + " " + User.last_name).label("student_name"),
            func.count(ProjectStar.id).label("star_count"),
        )
        .join(EnrollmentCohort)
        .join(User, Project.student_user_id == User.id)
        .outerjoin(ProjectStar, Project.id == ProjectStar.project_id)
        .filter(EnrollmentCohort.lab_id == lab_id)
        .group_by(Project.id, Project.project_name, "student_name")
        .order_by(func.count(ProjectStar.id).desc())
        .limit(5)
        .all()
    )
    top_projects = [
        TopProject(
            project_id=row[0],
            project_name=row[1],
            student_name=row[2],
            star_count=row[3],
        )
        for row in top_projects_query
    ]

    # --- 5. Assemble and Return Final Dashboard Object ---
    return LabDashboardStats(
        kpis=kpis,
        student_distribution=student_distribution,
        grok_specialization=grok_specialization,
        performance_distribution=performance_distribution,
        project_trend=project_trend,
        top_students=top_students,
        top_projects=top_projects,
    )

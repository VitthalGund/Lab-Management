from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from typing import List, Optional

from app.models import (
    User,
    TeacherProfile,
    StudentProfile,
    Project,
    ProjectStar,
    EnrollmentCohort,
    StudentEnrollment,
)
from app.schemas.report import LabReport, TopStudentEntry, TopStudentReport
from app.schemas.teacher import Teacher as TeacherSchema
from app.schemas.student import Student as StudentSchema, StudentProfileDetails
from app.schemas.project import Project as ProjectSchema


def generate_lab_report(db: Session, cohort_id: int) -> Optional[LabReport]:
    """
    Generates a comprehensive report for a single cohort.
    """
    cohort = (
        db.query(EnrollmentCohort)
        .options(joinedload(EnrollmentCohort.lab))
        .filter(EnrollmentCohort.id == cohort_id)
        .first()
    )
    if not cohort:
        return None

    # 1. Get Teachers for the Lab
    teachers_query = (
        db.query(User)
        .join(TeacherProfile)
        .filter(TeacherProfile.lab_id == cohort.lab_id)
        .all()
    )
    teachers_list = [
        TeacherSchema(
            user=t,
            lab_id=t.teacher_profile.lab_id,
            bio=t.teacher_profile.bio,
            date_of_joining=t.teacher_profile.date_of_joining,
            skills=[s.skill_name for s in t.skills],
        )
        for t in teachers_query
    ]

    # 2. Get Students enrolled in the Cohort
    students_query = (
        db.query(User)
        .join(StudentEnrollment)
        .filter(StudentEnrollment.cohort_id == cohort_id)
        .all()
    )
    students_list = [
        StudentSchema(
            user=s, profile=StudentProfileDetails(**s.student_profile.__dict__)
        )
        for s in students_query
    ]

    # 3. Get Projects submitted for the Cohort
    projects_query = (
        db.query(Project, func.count(ProjectStar.id).label("star_count"))
        .filter(Project.cohort_id == cohort_id)
        .outerjoin(ProjectStar, Project.id == ProjectStar.project_id)
        .group_by(Project.id)
        .options(joinedload(Project.student))
        .all()
    )

    projects_list = []
    for p, star_count in projects_query:
        projects_list.append(
            ProjectSchema(
                id=p.id,
                project_name=p.project_name,
                description=p.description,
                video_links=p.video_links,
                photo_urls=p.photo_urls,
                submission_date=p.submission_date,
                author=p.student,
                star_count=star_count,
            )
        )

    return LabReport(
        cohort_id=cohort.id,
        lab_id=cohort.lab_id,
        lab_name=cohort.lab.name,
        cohort_name=f"{cohort.academic_year} - {cohort.standard}th Std - {cohort.batch_name or cohort.section.value}",
        teachers=teachers_list,
        students=students_list,
        projects=projects_list,
    )


def generate_top_student_report(db: Session, month: int, year: int) -> TopStudentReport:
    """
    Generates a ranked report of top students for a given month and year.
    Score = (projects * 10) + (stars * 2)
    """
    # Projects submitted in the given month/year
    projects_in_month = (
        db.query(Project.student_user_id, func.count(Project.id).label("project_count"))
        .filter(
            extract("year", Project.submission_date) == year,
            extract("month", Project.submission_date) == month,
        )
        .group_by(Project.student_user_id)
        .subquery()
    )

    # Stars received in the given month/year
    stars_in_month = (
        db.query(
            Project.student_user_id, func.count(ProjectStar.id).label("star_count")
        )
        .join(ProjectStar, Project.id == ProjectStar.project_id)
        .filter(
            extract("year", ProjectStar.starred_at) == year,
            extract("month", ProjectStar.starred_at) == month,
        )
        .group_by(Project.student_user_id)
        .subquery()
    )

    # Combine the data
    query = (
        db.query(
            User,
            func.coalesce(projects_in_month.c.project_count, 0).label(
                "monthly_projects"
            ),
            func.coalesce(stars_in_month.c.star_count, 0).label("monthly_stars"),
        )
        .outerjoin(projects_in_month, User.id == projects_in_month.c.student_user_id)
        .outerjoin(stars_in_month, User.id == stars_in_month.c.student_user_id)
        .filter(User.role == "student")
        .all()
    )

    # Calculate scores and rank
    ranked_students = []
    for user, project_count, star_count in query:
        if project_count > 0 or star_count > 0:
            score = (project_count * 10) + (star_count * 2)
            ranked_students.append(
                {
                    "student": StudentSchema(
                        user=user,
                        profile=StudentProfileDetails(**user.student_profile.__dict__),
                    ),
                    "projects_submitted_in_month": project_count,
                    "stars_received_in_month": star_count,
                    "score": score,
                }
            )

    # Sort by score descending
    ranked_students.sort(key=lambda x: x["score"], reverse=True)

    # Add rank
    report_entries = [
        TopStudentEntry(rank=i + 1, **data) for i, data in enumerate(ranked_students)
    ]

    return TopStudentReport(month=month, year=year, report=report_entries)

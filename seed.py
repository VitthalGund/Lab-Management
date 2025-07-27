import random
from faker import Faker
from sqlalchemy.orm import Session

# --- Setup to allow standalone script execution ---
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
# --- End Setup ---

from app.db.session import SessionLocal
from app.services import (
    user_service,
    school_service,
    lab_service,
    teacher_service,
    student_service,
    enrollment_service,
    project_service,
    mark_service,
)
from app.schemas import (
    user as user_schema,
    school as school_schema,
    lab as lab_schema,
    teacher as teacher_schema,
    student as student_schema,
    enrollment as enrollment_schema,
    project as project_schema,
    mark as mark_schema,
)
from app.models.user import UserRole
from app.models.enrollment import CohortTeacher  # Import CohortTeacher model

# --- Configuration ---
NUM_SCHOOLS = 5
NUM_LABS_PER_SCHOOL = 2
NUM_LAB_HEADS = NUM_SCHOOLS * NUM_LABS_PER_SCHOOL
NUM_TEACHERS_PER_LAB = 5
NUM_STUDENTS = 500
NUM_COHORTS_PER_LAB = 4
NUM_PROJECTS_PER_STUDENT = 3
NUM_MARKS_PER_ENROLLMENT = 2
STARS_PER_PROJECT_RANGE = (0, 15)

# Initialize Faker
fake = Faker("en_IN")  # Use Indian locale for more realistic names/addresses


def seed_data(db: Session):
    """
    Main function to seed all data.
    """
    print("--- Starting Database Seeding ---")

    # 1. Create a master Admin user
    print("Creating admin user...")
    admin_user = user_schema.UserCreate(
        name="Admin",
        last_name="User",
        mobile_number="9999999999",
        password="adminpassword",
        role=UserRole.admin,
        email=fake.email(),
    )
    user_service.create_user(db, user=admin_user)

    # --- Data Storage ---
    schools = []
    labs = []
    lab_heads = []
    teachers = []
    students = []
    cohorts = []
    teachers_by_lab = {}  # To map teachers to their labs

    # 2. Create Schools
    print(f"Creating {NUM_SCHOOLS} schools...")
    for _ in range(NUM_SCHOOLS):
        school_data = school_schema.SchoolCreate(
            name=f"{fake.city()} Public School",
            location=fake.address(),
            principal_name=fake.name(),
            trustees=f"{fake.name()}, {fake.name()}",
            about=fake.text(max_nb_chars=200),
        )
        school = school_service.create_school(db, school=school_data)
        schools.append(school)

    # 3. Create Labs and Lab Heads
    print(f"Creating {NUM_LABS_PER_SCHOOL * len(schools)} labs and their lab heads...")
    for school in schools:
        for _ in range(NUM_LABS_PER_SCHOOL):
            lab_data = lab_schema.LabCreate(
                name=f"{random.choice(['Innovation', 'Discovery', 'Explorer', 'Tech'])} Lab",
                school_id=school.id,
                start_date=fake.date_between(start_date="-5y", end_date="-1y"),
            )
            lab = lab_service.create_lab(db, lab=lab_data)
            labs.append(lab)
            teachers_by_lab[lab.id] = []  # Initialize list for this lab

            # Create a Lab Head for this lab
            lab_head_user_data = user_schema.UserCreate(
                name=fake.first_name(),
                last_name=fake.last_name(),
                mobile_number=fake.unique.numerify(text="98#######"),
                password="password123",
                role=UserRole.lab_head,
                email=fake.unique.email(),
            )
            lab_head_user = user_service.create_user(db, user=lab_head_user_data)
            db.add(
                teacher_service.TeacherProfile(user_id=lab_head_user.id, lab_id=lab.id)
            )
            db.commit()
            lab_heads.append(lab_head_user)
            teachers_by_lab[lab.id].append(
                lab_head_user
            )  # Add lab head to the lab's staff list

    # 4. Create Teachers
    print(f"Creating {NUM_TEACHERS_PER_LAB * len(labs)} teachers...")
    for lab in labs:
        for _ in range(NUM_TEACHERS_PER_LAB):
            teacher_data = teacher_schema.TeacherCreate(
                name=fake.first_name(),
                last_name=fake.last_name(),
                mobile_number=fake.unique.numerify(text="97#######"),
                password="password123",
                email=fake.unique.email(),
                skills=["Python", "Robotics", "3D Printing", "IoT"][_ % 4 :],
            )
            teacher = teacher_service.create_teacher_in_lab(
                db, teacher_data=teacher_data, lab_id=lab.id
            )
            teachers.append(teacher)
            teachers_by_lab[lab.id].append(
                teacher
            )  # Add teacher to the lab's staff list

    all_staff = lab_heads + teachers

    # 5. Create Students
    print(f"Creating {NUM_STUDENTS} students...")
    student_creation_list = []
    for i in range(NUM_STUDENTS):
        student_data = student_schema.StudentCreate(
            name=fake.first_name(),
            last_name=fake.last_name(),
            mobile_number=fake.unique.numerify(text="77#######"),
            password="password123",
            email=fake.unique.email(),
            last_year_marks=f"{random.randint(60, 98)}%",
            father_name=fake.name_male(),
        )
        student_creation_list.append(student_data)

    students = student_service.bulk_create_students_in_lab(
        db, students_data=student_creation_list, lab_id=random.choice(labs).id
    )

    # 6. Create Cohorts
    print(f"Creating {NUM_COHORTS_PER_LAB * len(labs)} cohorts...")
    for lab in labs:
        for i in range(NUM_COHORTS_PER_LAB):
            cohort_data = enrollment_schema.EnrollmentCohortCreate(
                academic_year=2025,
                section=random.choice(list(enrollment_schema.LabSection)),
                standard=random.randint(5, 10),
                batch_name=f"Batch {chr(65+i)}",
                semester_start_date=fake.date_this_year(
                    before_today=True, after_today=False
                ),
            )
            cohort = enrollment_service.create_cohort_in_lab(
                db,
                cohort_data=cohort_data,
                lab_id=lab.id,
                creator_id=random.choice(all_staff).id,
            )
            cohorts.append(cohort)

    # 7. Assign Teachers to Cohorts (FIXED)
    print("Assigning teachers to cohorts...")
    for cohort in cohorts:
        lab_id = cohort.lab_id
        available_staff = teachers_by_lab.get(lab_id, [])
        if available_staff:
            num_to_assign = random.randint(1, min(2, len(available_staff)))
            assigned_teachers = random.sample(available_staff, num_to_assign)
            for teacher in assigned_teachers:
                db.add(CohortTeacher(cohort_id=cohort.id, teacher_user_id=teacher.id))
    db.commit()

    # 8. Enroll Students in Cohorts
    print("Enrolling students into cohorts...")
    for student in students:
        num_enrollments = random.randint(1, 2)
        enrolled_cohorts = random.sample(cohorts, num_enrollments)
        for cohort in enrolled_cohorts:
            enrollment_service.enroll_students_in_cohort(
                db, cohort_id=cohort.id, student_ids=[student.id]
            )

    # 9. Create Projects
    print(f"Creating ~{NUM_PROJECTS_PER_STUDENT * len(students)} projects...")
    all_enrollments = db.query(enrollment_service.StudentEnrollment).all()
    for enrollment in all_enrollments:
        for _ in range(random.randint(1, NUM_PROJECTS_PER_STUDENT)):
            project_data = project_schema.ProjectCreate(
                project_name=fake.bs().title(),
                description=fake.text(max_nb_chars=250),
                cohort_id=enrollment.cohort_id,
            )
            project = project_service.create_project(
                db, project_data=project_data, student_id=enrollment.student_user_id
            )

            # 10. Add Stars to Projects
            if project:
                num_stars = random.randint(*STARS_PER_PROJECT_RANGE)
                starrers = random.sample(all_staff, min(num_stars, len(all_staff)))
                for starrer in starrers:
                    project_service.star_unstar_project(
                        db, project_id=project.id, user_id=starrer.id
                    )

    # 11. Add Marks
    print("Adding marks for enrollments...")
    for enrollment in all_enrollments:
        for i in range(NUM_MARKS_PER_ENROLLMENT):
            mark_data = mark_schema.MarkCreate(
                assessment_name=f"Unit Test {i+1}",
                marks_obtained=random.uniform(15.5, 25.0),
                total_marks=25.0,
            )
            mark_service.create_mark_for_enrollment(
                db, mark_data=mark_data, enrollment_id=enrollment.id
            )

    print("--- Seeding Complete! ---")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()

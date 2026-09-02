import asyncio
import uuid
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, Student, Faculty, Department

async def seed_users():
    async with AsyncSessionLocal() as db:
        # Create a Department for Demo
        dept = Department(
            id=uuid.uuid4(),
            name="Demo Department",
            code="DEMO"
        )
        db.add(dept)
        await db.flush()

        # Create Demo Student User
        student_user = User(
            id=uuid.uuid4(),
            email="student@demo.ccip",
            password_hash=hash_password("password123"),
            role="student",
            first_name="Demo",
            last_name="Student",
            is_active=True
        )
        db.add(student_user)
        
        # Create Demo Student Profile
        student = Student(
            id=student_user.id,
            roll_number="DEMO1234",
            department_id=dept.id,
            current_semester=6,
            admission_year=2021,
            cgpa=8.5,
        )
        db.add(student)
        
        # Create Demo TPO User
        tpo_user = User(
            id=uuid.uuid4(),
            email="tpo@demo.ccip",
            password_hash=hash_password("password123"),
            role="tpo",
            first_name="Demo",
            last_name="TPO",
            is_active=True
        )
        db.add(tpo_user)

        # Create Demo Faculty User
        faculty_user = User(
            id=uuid.uuid4(),
            email="faculty@demo.ccip",
            password_hash=hash_password("password123"),
            role="faculty",
            first_name="Demo",
            last_name="Faculty",
            is_active=True
        )
        db.add(faculty_user)
        await db.flush()

        # Create Demo Faculty Profile
        faculty = Faculty(
            id=faculty_user.id,
            department_id=dept.id,
            employee_id="FAC001",
        )
        db.add(faculty)

        try:
            await db.commit()
            print("Demo users seeded successfully.")
        except Exception as e:
            await db.rollback()
            print("Error seeding users (they may already exist):", e)

if __name__ == "__main__":
    asyncio.run(seed_users())

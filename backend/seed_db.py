import asyncio
import os
import sys

# Ensure we can import app modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import async_sessionmaker_db, engine
from app.models.user import User, Student, Faculty, TPOOfficer
from app.models.academic import Department
from app.core.security import hash_password
import uuid

async def seed_demo_users():
    async with async_sessionmaker_db() as db:
        print("Seeding demo users...")
        # 1. Create a Department if it doesn't exist
        from sqlalchemy import select
        res = await db.execute(select(Department).where(Department.code == "CS"))
        dept = res.scalar_one_or_none()
        if not dept:
            dept = Department(id=uuid.uuid4(), name="Computer Science", code="CS")
            db.add(dept)
            await db.flush()

        # 2. Demo Student
        res = await db.execute(select(User).where(User.email == "student@demo.ccip"))
        if not res.scalar_one_or_none():
            u_id = uuid.uuid4()
            user = User(
                id=u_id,
                email="student@demo.ccip",
                password_hash=hash_password("password123"),
                role="student",
                first_name="Demo",
                last_name="Student",
                is_active=True
            )
            db.add(user)
            await db.flush()
            student = Student(
                id=u_id,
                roll_number="DEMO001",
                department_id=dept.id,
                current_semester=6,
                admission_year=2021,
                cgpa=8.5
            )
            db.add(student)

        # 3. Demo TPO
        res = await db.execute(select(User).where(User.email == "tpo@demo.ccip"))
        if not res.scalar_one_or_none():
            u_id = uuid.uuid4()
            user = User(
                id=u_id,
                email="tpo@demo.ccip",
                password_hash=hash_password("password123"),
                role="tpo",
                first_name="Demo",
                last_name="Admin",
                is_active=True
            )
            db.add(user)
            await db.flush()
            tpo = TPOOfficer(
                id=u_id,
                employee_id="TPO001",
                department_id=dept.id
            )
            db.add(tpo)

        # 4. Demo Faculty
        res = await db.execute(select(User).where(User.email == "faculty@demo.ccip"))
        if not res.scalar_one_or_none():
            u_id = uuid.uuid4()
            user = User(
                id=u_id,
                email="faculty@demo.ccip",
                password_hash=hash_password("password123"),
                role="faculty",
                first_name="Demo",
                last_name="Faculty",
                is_active=True
            )
            db.add(user)
            await db.flush()
            faculty = Faculty(
                id=u_id,
                employee_id="FAC001",
                department_id=dept.id,
                designation="Professor"
            )
            db.add(faculty)

        await db.commit()
        print("Demo users created successfully!")

if __name__ == "__main__":
    asyncio.run(seed_demo_users())

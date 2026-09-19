"""
pytest configuration & shared fixtures.

Design: All fixtures are function-scoped to avoid asyncio cross-loop issues.
Seed data uses ON-CONFLICT-IGNORE patterns so multiple test runs don't fail
on UNIQUE constraints. The DB is a single file-based SQLite that is reset
once per session (via setup_db autouse fixture).
"""

import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_ccip.db"

import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.main import app
from app.models.user import User, Student, Department
from app.models.skill import Skill, StudentSkill


# ---------------------------------------------------------------------------
# Test DB engine — file-based SQLite (single file shared across session)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_ccip.db"

_test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
_TestSession = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False
)


# ---------------------------------------------------------------------------
# Override app's get_db to point at the test database
# ---------------------------------------------------------------------------

async def _override_get_db():
    async with _TestSession() as session:
        yield session

app.dependency_overrides[get_db] = _override_get_db


# ---------------------------------------------------------------------------
# Session-level: create & drop all tables once
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def create_tables(event_loop):
    """Synchronously create all DB tables before any test, drop after."""
    async def _create():
        async with _test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    async def _drop():
        async with _test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    event_loop.run_until_complete(_create())
    yield
    event_loop.run_until_complete(_drop())


# ---------------------------------------------------------------------------
# Seed all shared data (once per session, synchronously via the loop)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def seed_all(create_tables, event_loop):
    """Create all shared seed data once per session."""
    event_loop.run_until_complete(_seed_data())


async def _get_or_create_department() -> Department:
    async with _TestSession() as db:
        r = await db.execute(select(Department).where(Department.code == "CS"))
        dept = r.scalar_one_or_none()
        if dept is None:
            dept = Department(id=uuid.uuid4(), name="Computer Science", code="CS")
            db.add(dept)
            await db.commit()
            await db.refresh(dept)
        return dept


async def _get_or_create_student(dept: Department) -> tuple[User, Student]:
    async with _TestSession() as db:
        r = await db.execute(select(User).where(User.email == "aryan.sharma@university.ac.in"))
        user = r.scalar_one_or_none()
        if user is None:
            user = User(
                id=uuid.uuid4(),
                email="aryan.sharma@university.ac.in",
                password_hash=hash_password("Student123!"),
                role="student",
                first_name="Aryan",
                last_name="Sharma",
            )
            db.add(user)
            await db.flush()
            student = Student(
                id=user.id,
                roll_number="CS2022001",
                department_id=dept.id,
                current_semester=6,
                admission_year=2022,
                cgpa=8.4,
            )
            db.add(student)
            await db.commit()
        r2 = await db.execute(select(Student).where(Student.id == user.id))
        student = r2.scalar_one()
        return user, student


async def _get_or_create_tpo() -> User:
    async with _TestSession() as db:
        r = await db.execute(select(User).where(User.email == "tpo@university.ac.in"))
        user = r.scalar_one_or_none()
        if user is None:
            user = User(
                id=uuid.uuid4(),
                email="tpo@university.ac.in",
                password_hash=hash_password("TpoPass123!"),
                role="tpo",
                first_name="TPO",
                last_name="Officer",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user


async def _get_or_create_skills() -> list[Skill]:
    skills_data = [
        ("Python", "python", "language"),
        ("SQL", "sql", "database"),
        ("Machine Learning", "machine learning", "concept"),
        ("React", "react", "framework"),
        ("Docker", "docker", "tool"),
    ]
    async with _TestSession() as db:
        skills = []
        for name, norm, cat in skills_data:
            r = await db.execute(select(Skill).where(Skill.normalized_name == norm))
            skill = r.scalar_one_or_none()
            if skill is None:
                skill = Skill(id=uuid.uuid4(), name=name, normalized_name=norm, category=cat)
                db.add(skill)
            skills.append(skill)
        await db.commit()
        return skills


async def _get_or_create_student_skills(student: Student, skills: list[Skill]) -> list[StudentSkill]:
    confidences = [0.9, 0.85, 0.7, 0.4, 0.2]
    async with _TestSession() as db:
        result = []
        for skill, conf in zip(skills, confidences):
            r = await db.execute(
                select(StudentSkill).where(
                    StudentSkill.student_id == student.id,
                    StudentSkill.skill_id == skill.id,
                    StudentSkill.source == "manual",
                )
            )
            ss = r.scalar_one_or_none()
            if ss is None:
                ss = StudentSkill(
                    id=uuid.uuid4(),
                    student_id=student.id,
                    skill_id=skill.id,
                    confidence=conf,
                    source="manual",
                )
                db.add(ss)
            result.append(ss)
        await db.commit()
        return result


async def _seed_data():
    dept = await _get_or_create_department()
    user, student = await _get_or_create_student(dept)
    await _get_or_create_tpo()
    skills = await _get_or_create_skills()
    await _get_or_create_student_skills(student, skills)


# ---------------------------------------------------------------------------
# Convenience fixtures (return already-seeded data from the DB)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def seed_department(seed_all, event_loop) -> Department:
    return event_loop.run_until_complete(_get_or_create_department())


@pytest.fixture(scope="session")
def seed_student(seed_all, event_loop) -> tuple[User, Student]:
    dept = event_loop.run_until_complete(_get_or_create_department())
    return event_loop.run_until_complete(_get_or_create_student(dept))


@pytest.fixture(scope="session")
def seed_tpo(seed_all, event_loop) -> User:
    return event_loop.run_until_complete(_get_or_create_tpo())


@pytest.fixture(scope="session")
def seed_skills(seed_all, event_loop) -> list[Skill]:
    return event_loop.run_until_complete(_get_or_create_skills())


@pytest.fixture(scope="session")
def seed_student_skills(seed_student, seed_skills, event_loop) -> list[StudentSkill]:
    _, student = seed_student
    skills = event_loop.run_until_complete(_get_or_create_skills())
    return event_loop.run_until_complete(_get_or_create_student_skills(student, skills))


# ---------------------------------------------------------------------------
# Function-scoped fixtures (safe — no session-scoped event loop sharing)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db() -> AsyncSession:
    """Yield a DB session for use in tests."""
    async with _TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Async HTTPX client wired to the FastAPI test app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Auth token helpers
# ---------------------------------------------------------------------------

def make_token(user: User) -> str:
    return create_access_token({"sub": str(user.id), "role": user.role})


def auth_headers(user: User) -> dict:
    return {"Authorization": f"Bearer {make_token(user)}"}

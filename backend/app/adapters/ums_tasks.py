"""
UMS Celery Tasks — background sync jobs.

Task modules registered in app/worker.py.

Tasks:
  - sync_student_task: Sync a single student by roll number.
  - sync_department_task: Sync all students in a department.
  - scheduled_full_sync_task: Triggered by Celery Beat to run a nightly full sync.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: create a fresh DB session inside a Celery task context
# ---------------------------------------------------------------------------

def _get_sync_db_and_adapter():
    """
    Return a synchronous-compatible (run_until_complete) wrapper.

    Because Celery tasks are synchronous by default and our DB is async,
    we run the coroutines using asyncio.run().
    """
    import asyncio
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from app.core.config import get_settings
    from app.adapters.mock_ums_adapter import MockUMSAdapter

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return factory, MockUMSAdapter, asyncio, engine


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@shared_task(
    name="ums.sync_student",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def sync_student_task(self, roll_number: str) -> dict:
    """
    Sync a single student's data from UMS.

    Args:
        roll_number: The student's roll number (e.g. "CS2022001")

    Returns:
        A summary dict with sync results.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from app.core.config import get_settings
    from app.adapters.mock_ums_adapter import MockUMSAdapter
    from app.services.ums_sync_service import sync_single_student

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _run():
        async with factory() as db:
            adapter = MockUMSAdapter(db)
            return await sync_single_student(db, adapter, roll_number)

    try:
        result = asyncio.run(_run())
        logger.info("sync_student_task(%s): %s", roll_number, result)
        return result
    except Exception as exc:
        logger.error("sync_student_task(%s) error: %s", roll_number, exc, exc_info=True)
        raise self.retry(exc=exc)


@shared_task(
    name="ums.sync_department",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    acks_late=True,
)
def sync_department_task(self, department_code: str) -> dict:
    """
    Sync all students in a department.

    Args:
        department_code: Department code e.g. "CS", "EC", "ME"
    """
    import asyncio
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from app.core.config import get_settings
    from app.adapters.mock_ums_adapter import MockUMSAdapter
    from app.services.ums_sync_service import sync_department

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _run():
        async with factory() as db:
            adapter = MockUMSAdapter(db)
            return await sync_department(db, adapter, department_code)

    try:
        result = asyncio.run(_run())
        logger.info("sync_department_task(%s): %s", department_code, result)
        return result
    except Exception as exc:
        logger.error("sync_department_task(%s) error: %s", department_code, exc, exc_info=True)
        raise self.retry(exc=exc)


@shared_task(
    name="ums.scheduled_full_sync",
    bind=True,
    acks_late=True,
)
def scheduled_full_sync_task(self) -> dict:
    """
    Nightly full sync — sync all students across all departments.
    Designed to be triggered by Celery Beat on a cron schedule.

    Add to worker.py beat_schedule:
        "nightly-ums-sync": {
            "task": "ums.scheduled_full_sync",
            "schedule": crontab(hour=2, minute=0),
        }
    """
    import asyncio
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from app.core.config import get_settings
    from app.adapters.mock_ums_adapter import MockUMSAdapter
    from app.services.ums_sync_service import sync_single_student
    from app.models.user import Student

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _run():
        async with factory() as db:
            result = await db.execute(select(Student.roll_number))
            roll_numbers = [r for (r,) in result.all()]

        total = len(roll_numbers)
        success = 0
        failed = 0

        for roll in roll_numbers:
            async with factory() as db:
                adapter = MockUMSAdapter(db)
                r = await sync_single_student(db, adapter, roll)
                if r["success"]:
                    success += 1
                else:
                    failed += 1

        return {
            "task": "scheduled_full_sync",
            "total_students": total,
            "synced": success,
            "failed": failed,
        }

    try:
        result = asyncio.run(_run())
        logger.info("scheduled_full_sync complete: %s", result)
        return result
    except Exception as exc:
        logger.error("scheduled_full_sync error: %s", exc, exc_info=True)
        raise

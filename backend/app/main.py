"""
CCIP — Campus Career & Curriculum Intelligence Platform

Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
import redis.asyncio as aioredis
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine, IS_SQLITE, Base
from app.api.v1.auth import router as auth_router
from app.api.v1.students import router as students_router
from app.api.v1.drives import router as drives_router
from app.api.v1.applications import router as applications_router
from app.api.v1.matching import router as matching_router
from app.api.v1.roadmap import router as roadmap_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.copilot import router as copilot_router
from app.api.v1.skills import router as skills_router
from app.api.v1.resume import router as resume_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.ums import router as ums_router
from app.api.v1.curriculum import router as curriculum_router
from app.api.v1.tpo import router as tpo_router
from app.api.v1.system import router as system_router
from app.api.v1.admin import router as admin_router
from app.api.v1.notifications import router as notifications_router
"""
CCIP — Campus Career & Curriculum Intelligence Platform

Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
import redis.asyncio as aioredis
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine, IS_SQLITE, Base
from app.api.v1.auth import router as auth_router
from app.api.v1.students import router as students_router
from app.api.v1.drives import router as drives_router
from app.api.v1.applications import router as applications_router
from app.api.v1.matching import router as matching_router
from app.api.v1.roadmap import router as roadmap_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.copilot import router as copilot_router
from app.api.v1.skills import router as skills_router
from app.api.v1.resume import router as resume_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.ums import router as ums_router
from app.api.v1.curriculum import router as curriculum_router
from app.api.v1.tpo import router as tpo_router
from app.api.v1.system import router as system_router
from app.api.v1.admin import router as admin_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.websocket import router as ws_router

from app.middleware.rls import RowLevelSecurityMiddleware
from app.middleware.timing import TimingMiddleware
from app.middleware.rate_limit import limiter

# Import all models so SQLAlchemy registers them with Base.metadata
import app.models.user  # noqa: F401
import app.models.academic  # noqa: F401
import app.models.skill  # noqa: F401
import app.models.portfolio  # noqa: F401
import app.models.industry  # noqa: F401
import app.models.placement  # noqa: F401
import app.models.roadmap  # noqa: F401
import app.models.system  # noqa: F401
import app.models.cohort  # noqa: F401
import app.models.notification # noqa: F401

settings = get_settings()

APP_START_TIME = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — create tables for SQLite, ensure vector ext for PostgreSQL."""
from fastapi import Response
@app.get("/health/ready", tags=["System"])
async def health_ready(response: Response):
    # For a service to be ready both db and redis must answer fast
    db_ok = False
    redis_ok = False
    try:
        t0 = time.perf_counter()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        if (time.perf_counter() - t0) * 1000 < 200:
            db_ok = True
    except Exception:
        pass
        
    try:
        t0 = time.perf_counter()
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=1)
        await r.ping()
        if (time.perf_counter() - t0) * 1000 < 200:
            redis_ok = True
        await r.aclose()
    except Exception:
        pass

    if db_ok and redis_ok:
        return {"status": "ready"}
    else:
        response.status_code = 503
        return {"status": "not ready"}


# ─── API v1 Routers ─────────────────────────────────────────────

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(students_router, prefix=settings.API_V1_PREFIX)
app.include_router(drives_router, prefix=settings.API_V1_PREFIX)
app.include_router(applications_router, prefix=settings.API_V1_PREFIX)
app.include_router(matching_router, prefix=settings.API_V1_PREFIX)
app.include_router(roadmap_router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(copilot_router, prefix=settings.API_V1_PREFIX)
app.include_router(skills_router, prefix=settings.API_V1_PREFIX)
app.include_router(resume_router, prefix=settings.API_V1_PREFIX)
app.include_router(assessments_router, prefix=settings.API_V1_PREFIX)
app.include_router(ums_router, prefix=settings.API_V1_PREFIX)
app.include_router(curriculum_router, prefix=settings.API_V1_PREFIX)
app.include_router(tpo_router, prefix=settings.API_V1_PREFIX)
app.include_router(system_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications_router, prefix=settings.API_V1_PREFIX)
app.include_router(ws_router) # ROOT LEVEL route for /ws/{user_id}

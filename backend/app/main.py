"""
CCIP — Campus Career & Curriculum Intelligence Platform

Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from app.api.v1.tpo import router as tpo_router

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

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — create tables for SQLite, ensure vector ext for PostgreSQL."""
    if IS_SQLITE:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered intelligence platform that connects industry skill demand "
        "to college curriculum and student readiness."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "service": "ccip-backend",
    }


# ─── API v1 Routers ─────────────────────────────────────────────

from app.api.v1.questions import router as questions_router

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
app.include_router(tpo_router, prefix=settings.API_V1_PREFIX)
app.include_router(questions_router, prefix=settings.API_V1_PREFIX)


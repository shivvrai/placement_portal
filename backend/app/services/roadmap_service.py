"""
Roadmap service — generate and manage learning roadmaps.
Uses template-based generation while Phase 4 ML pipeline matures.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.roadmap import Roadmap, RoadmapTask
from app.models.user import Student
from app.schemas.roadmap import RoadmapGenerateRequest, TaskStatusUpdateRequest


# ─── Template Roadmaps ─────────────────────────────────────────────────────────

ROLE_ROADMAPS: dict[str, list[dict]] = {
    "Data Analyst": [
        {"week": 1, "title": "SQL Fundamentals", "hours": 6, "desc": "SELECT, JOINs, GROUP BY, subqueries"},
        {"week": 1, "title": "Excel / Sheets for Data", "hours": 3, "desc": "Pivot tables, VLOOKUP, charting"},
        {"week": 2, "title": "SQL Advanced — Window Functions", "hours": 5, "desc": "RANK, ROW_NUMBER, LAG, LEAD, CTEs"},
        {"week": 2, "title": "Statistics Basics", "hours": 4, "desc": "Mean, median, std dev, distributions"},
        {"week": 3, "title": "Python — pandas core", "hours": 8, "desc": "DataFrames, merge, groupby, pivot_table"},
        {"week": 4, "title": "Data Visualization — matplotlib/seaborn", "hours": 5, "desc": "Line, bar, scatter, heatmaps"},
        {"week": 5, "title": "Tableau / Power BI Basics", "hours": 6, "desc": "Connect to DB, build dashboard, publish"},
        {"week": 6, "title": "End-to-End Project: Retail Sales Analysis", "hours": 10, "desc": "SQL + Python + Tableau. Upload to GitHub."},
        {"week": 7, "title": "Python — numpy & scipy", "hours": 4, "desc": "Array ops, statistical tests"},
        {"week": 8, "title": "Probability & Hypothesis Testing", "hours": 5, "desc": "t-test, chi-square, p-values"},
        {"week": 9, "title": "Intro to Machine Learning (sklearn)", "hours": 6, "desc": "Linear Regression, Decision Tree"},
        {"week": 10, "title": "Mock Interview Practice", "hours": 4, "desc": "Pramp + StrataScratch 20 SQL problems"},
        {"week": 11, "title": "Resume & LinkedIn Update", "hours": 3, "desc": "Add projects, quantify impact"},
        {"week": 12, "title": "Capstone: Customer Churn Dashboard", "hours": 12, "desc": "Python + SQL + Tableau. Full pipeline."},
    ],
    "Software Engineer": [
        {"week": 1, "title": "DSA: Arrays & Strings", "hours": 8, "desc": "LeetCode Easy/Medium — 20 problems"},
        {"week": 2, "title": "DSA: Linked Lists & Stacks", "hours": 7, "desc": "LeetCode 15 problems"},
        {"week": 3, "title": "DSA: Trees & Graphs", "hours": 8, "desc": "BFS, DFS, recursion — 20 problems"},
        {"week": 4, "title": "DSA: Dynamic Programming", "hours": 8, "desc": "DP patterns — 15 problems"},
        {"week": 5, "title": "System Design Basics", "hours": 6, "desc": "URL shortener, rate limiter, caching"},
        {"week": 6, "title": "Backend: FastAPI / Django REST", "hours": 8, "desc": "Build a REST API with auth"},
        {"week": 7, "title": "Databases: SQL + PostgreSQL", "hours": 5, "desc": "Indexes, transactions, query tuning"},
        {"week": 8, "title": "Docker + Git workflow", "hours": 4, "desc": "Containerise your API, PR workflow"},
        {"week": 9, "title": "Project: Todo API with Auth", "hours": 8, "desc": "FastAPI + Postgres + Docker on GitHub"},
        {"week": 10, "title": "Mock Interviews (Pramp)", "hours": 6, "desc": "2 sessions + debrief"},
        {"week": 11, "title": "OS & Networks Revision", "hours": 4, "desc": "Processes, TCP/IP, HTTP for interviews"},
        {"week": 12, "title": "Apply & STAR Story prep", "hours": 5, "desc": "Apply to 10 companies, prep 5 STAR stories"},
    ],
    "ML Engineer": [
        {"week": 1, "title": "Python for ML: numpy, pandas", "hours": 6, "desc": "Core numeric computing and data wrangling"},
        {"week": 2, "title": "Statistics for ML", "hours": 6, "desc": "Probability, distributions, Bayes"},
        {"week": 3, "title": "Supervised Learning (sklearn)", "hours": 7, "desc": "Regression, Classification, evaluation metrics"},
        {"week": 4, "title": "Unsupervised Learning", "hours": 5, "desc": "K-Means, PCA, DBSCAN"},
        {"week": 5, "title": "Feature Engineering", "hours": 5, "desc": "Encoding, scaling, selection"},
        {"week": 6, "title": "Project: Kaggle competition", "hours": 10, "desc": "End-to-end ML pipeline, score in top 30%"},
        {"week": 7, "title": "Deep Learning — PyTorch basics", "hours": 8, "desc": "Tensors, autograd, simple NN"},
        {"week": 8, "title": "CNNs for Image Classification", "hours": 6, "desc": "ResNet fine-tuning on CIFAR-10"},
        {"week": 9, "title": "NLP: Transformers & HuggingFace", "hours": 6, "desc": "BERT fine-tuning, sentiment"},
        {"week": 10, "title": "Model Deployment (FastAPI + Docker)", "hours": 6, "desc": "REST endpoint for ML model"},
        {"week": 11, "title": "MLflow & experiment tracking", "hours": 4, "desc": "Log params, metrics, artifacts"},
        {"week": 12, "title": "Portfolio project + interviews", "hours": 8, "desc": "End-to-end deployed ML project"},
    ],
}


async def get_student_roadmap(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> Optional[Roadmap]:
    result = await db.execute(
        select(Roadmap)
        .where(Roadmap.student_id == student_id, Roadmap.status == "active")
        .options(selectinload(Roadmap.tasks))
        .order_by(Roadmap.generated_at.desc())
    )
    return result.scalars().first()


async def generate_roadmap(
    db: AsyncSession,
    student_id: uuid.UUID,
    data: RoadmapGenerateRequest,
) -> Roadmap:
    """Generate a template-based roadmap, archive any existing one."""

    # Archive old active roadmaps
    old = await db.execute(
        select(Roadmap)
        .where(Roadmap.student_id == student_id, Roadmap.status == "active")
    )
    for old_roadmap in old.scalars().all():
        old_roadmap.status = "archived"

    # Create roadmap
    roadmap = Roadmap(
        student_id=student_id,
        target_role=data.target_role,
        total_weeks=data.weeks,
        status="active",
        progress_pct=0.0,
    )
    db.add(roadmap)
    await db.flush()

    # Create tasks from template
    template = ROLE_ROADMAPS.get(data.target_role, ROLE_ROADMAPS["Software Engineer"])
    for i, task_data in enumerate(template):
        if task_data["week"] > data.weeks:
            break
        task = RoadmapTask(
            roadmap_id=roadmap.id,
            title=task_data["title"],
            description=task_data["desc"],
            week_number=task_data["week"],
            order_in_week=i + 1,
            estimated_hours=task_data.get("hours"),
            status="pending",
        )
        db.add(task)

    await db.commit()
    await db.refresh(roadmap)

    # Re-fetch with tasks
    result = await db.execute(
        select(Roadmap)
        .where(Roadmap.id == roadmap.id)
        .options(selectinload(Roadmap.tasks))
    )
    return result.scalar_one()


async def update_task_status(
    db: AsyncSession,
    task_id: uuid.UUID,
    data: TaskStatusUpdateRequest,
    student_id: uuid.UUID,
) -> RoadmapTask:
    result = await db.execute(
        select(RoadmapTask)
        .where(RoadmapTask.id == task_id)
        .options(selectinload(RoadmapTask.roadmap))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.roadmap.student_id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your roadmap")

    task.status = data.status
    if data.status == "completed":
        task.completed_at = datetime.now(timezone.utc)

    # Recalculate roadmap progress
    roadmap = task.roadmap
    all_tasks = await db.execute(
        select(RoadmapTask).where(RoadmapTask.roadmap_id == roadmap.id)
    )
    all_tasks_list = all_tasks.scalars().all()
    completed = sum(1 for t in all_tasks_list if t.status == "completed" or t.id == task_id and data.status == "completed")
    roadmap.progress_pct = round(completed / len(all_tasks_list) * 100, 1) if all_tasks_list else 0.0

    await db.commit()
    await db.refresh(task)
    return task

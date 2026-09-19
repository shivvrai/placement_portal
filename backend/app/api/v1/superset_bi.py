"""
BI Studio API — Apache Superset Guest Tokens, OData v4 Feed, Data Export.

Provides a unified BI integration layer:
  1. Superset embedding via Guest Token API
  2. OData v4 REST feed for Power BI / Tableau / Excel
  3. CSV/JSON bulk export for offline BI analysis

All endpoints require TPO/admin role.
"""

import csv
import io
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import RoleChecker
from app.models.user import User, Student, Department
from app.models.placement import PlacementDrive, PlacementOutcome, Application
from app.models.industry import Company
from app.models.skill import Skill, StudentSkill

router = APIRouter(prefix="/bi", tags=["BI Studio"])

settings = get_settings()
_tpo_or_admin = RoleChecker(["tpo", "admin", "faculty", "hod"])


# ═══════════════════════════════════════════════════════════════════════════════
#  SUPERSET INTEGRATION — Guest Token & Dashboard Discovery
# ═══════════════════════════════════════════════════════════════════════════════

async def _get_superset_access_token() -> Optional[str]:
    """Authenticate with Superset API and return an access token."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.SUPERSET_URL}/api/v1/security/login",
                json={
                    "username": settings.SUPERSET_ADMIN_USERNAME,
                    "password": settings.SUPERSET_ADMIN_PASSWORD,
                    "provider": "db",
                    "refresh": True,
                },
            )
            if resp.status_code == 200:
                return resp.json().get("access_token")
    except Exception:
        pass
    return None


@router.get("/embed-token", summary="Get Superset Guest Token for iframe embedding")
async def get_embed_token(
    dashboard_id: str = Query("", description="Superset dashboard ID to embed"),
    current_user: User = Depends(_tpo_or_admin),
):
    """
    Generates a Superset Guest Token for embedding dashboards in the React frontend.
    Uses Superset's /api/v1/security/guest_token/ endpoint.
    """
    access_token = await _get_superset_access_token()
    if not access_token:
        return {
            "guest_token": None,
            "superset_url": settings.SUPERSET_PUBLIC_URL,
            "status": "superset_unavailable",
            "message": "Superset is not running or credentials are invalid. Start it with: docker compose up superset",
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "user": {
                    "username": current_user.email,
                    "first_name": current_user.first_name,
                    "last_name": current_user.last_name,
                },
                "resources": [
                    {"type": "dashboard", "id": dashboard_id}
                ] if dashboard_id else [],
                "rls": [],  # Row-level security rules
            }
            resp = await client.post(
                f"{settings.SUPERSET_URL}/api/v1/security/guest_token/",
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code == 200:
                return {
                    "guest_token": resp.json().get("token"),
                    "superset_url": settings.SUPERSET_PUBLIC_URL,
                    "status": "ok",
                }
    except Exception:
        pass

    return {
        "guest_token": None,
        "superset_url": settings.SUPERSET_PUBLIC_URL,
        "status": "token_error",
        "message": "Failed to generate guest token. Check Superset configuration.",
    }


@router.get("/dashboards", summary="List available Superset dashboards")
async def list_dashboards(
    current_user: User = Depends(_tpo_or_admin),
):
    """Fetch the list of dashboards from Superset's REST API."""
    access_token = await _get_superset_access_token()
    if not access_token:
        return {
            "dashboards": [],
            "superset_url": settings.SUPERSET_PUBLIC_URL,
            "status": "superset_unavailable",
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.SUPERSET_URL}/api/v1/dashboard/",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"q": '(page_size:50)'},
            )
            if resp.status_code == 200:
                data = resp.json()
                dashboards = [
                    {
                        "id": d.get("id"),
                        "title": d.get("dashboard_title"),
                        "url": f"{settings.SUPERSET_PUBLIC_URL}/superset/dashboard/{d.get('id')}/",
                        "status": d.get("status", "published"),
                        "changed_on": d.get("changed_on_utc"),
                    }
                    for d in data.get("result", [])
                ]
                return {"dashboards": dashboards, "status": "ok"}
    except Exception:
        pass

    return {"dashboards": [], "status": "fetch_error"}


@router.get("/config", summary="BI Studio configuration")
async def get_bi_config(
    current_user: User = Depends(_tpo_or_admin),
):
    """Returns BI tool URLs and feature flags for the frontend."""
    # Check if Superset is reachable
    superset_online = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.SUPERSET_URL}/health")
            superset_online = resp.status_code == 200
    except Exception:
        pass

    base_url = str(settings.SUPERSET_PUBLIC_URL).rstrip("/")
    api_base = "/api/v1"  # This app's API prefix

    return {
        "superset": {
            "url": base_url,
            "sql_lab_url": f"{base_url}/sqllab/",
            "online": superset_online,
        },
        "powerbi": {
            "embed_url": settings.POWERBI_EMBED_URL or None,
            "configured": bool(settings.POWERBI_EMBED_URL),
        },
        "odata": {
            "base_url": f"{api_base}/bi/odata",
            "metadata_url": f"{api_base}/bi/odata/$metadata",
            "entities": [
                "Students", "Placements", "Drives",
                "Departments", "Skills", "StudentSkills",
            ],
        },
        "export_entities": ["students", "placements", "drives", "skills", "departments"],
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  OData v4 FEED — Power BI / Tableau / Excel Connector
# ═══════════════════════════════════════════════════════════════════════════════

ODATA_METADATA_XML = """<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx Version="4.0" xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
  <edmx:DataServices>
    <Schema Namespace="CCIP" xmlns="http://docs.oasis-open.org/odata/ns/edm">
      <EntityType Name="Student">
        <Key><PropertyRef Name="id"/></Key>
        <Property Name="id" Type="Edm.String" Nullable="false"/>
        <Property Name="roll_number" Type="Edm.String"/>
        <Property Name="full_name" Type="Edm.String"/>
        <Property Name="email" Type="Edm.String"/>
        <Property Name="department_code" Type="Edm.String"/>
        <Property Name="department_name" Type="Edm.String"/>
        <Property Name="current_semester" Type="Edm.Int32"/>
        <Property Name="admission_year" Type="Edm.Int32"/>
        <Property Name="cgpa" Type="Edm.Decimal"/>
        <Property Name="skill_count" Type="Edm.Int32"/>
        <Property Name="is_placed" Type="Edm.Boolean"/>
      </EntityType>

      <EntityType Name="Placement">
        <Key><PropertyRef Name="id"/></Key>
        <Property Name="id" Type="Edm.String" Nullable="false"/>
        <Property Name="student_roll" Type="Edm.String"/>
        <Property Name="student_name" Type="Edm.String"/>
        <Property Name="department_code" Type="Edm.String"/>
        <Property Name="company_name" Type="Edm.String"/>
        <Property Name="role" Type="Edm.String"/>
        <Property Name="salary_ctc_lpa" Type="Edm.Decimal"/>
        <Property Name="placement_type" Type="Edm.String"/>
        <Property Name="academic_year" Type="Edm.String"/>
        <Property Name="recorded_at" Type="Edm.DateTimeOffset"/>
      </EntityType>

      <EntityType Name="Drive">
        <Key><PropertyRef Name="id"/></Key>
        <Property Name="id" Type="Edm.String" Nullable="false"/>
        <Property Name="title" Type="Edm.String"/>
        <Property Name="company_name" Type="Edm.String"/>
        <Property Name="company_industry" Type="Edm.String"/>
        <Property Name="drive_date" Type="Edm.Date"/>
        <Property Name="salary_ctc_lpa" Type="Edm.Decimal"/>
        <Property Name="status" Type="Edm.String"/>
        <Property Name="academic_year" Type="Edm.String"/>
        <Property Name="min_cgpa" Type="Edm.Decimal"/>
        <Property Name="applications_count" Type="Edm.Int32"/>
      </EntityType>

      <EntityType Name="Department">
        <Key><PropertyRef Name="id"/></Key>
        <Property Name="id" Type="Edm.String" Nullable="false"/>
        <Property Name="code" Type="Edm.String"/>
        <Property Name="name" Type="Edm.String"/>
        <Property Name="student_count" Type="Edm.Int32"/>
      </EntityType>

      <EntityType Name="Skill">
        <Key><PropertyRef Name="id"/></Key>
        <Property Name="id" Type="Edm.String" Nullable="false"/>
        <Property Name="name" Type="Edm.String"/>
        <Property Name="category" Type="Edm.String"/>
        <Property Name="domain" Type="Edm.String"/>
      </EntityType>

      <EntityType Name="StudentSkill">
        <Key><PropertyRef Name="id"/></Key>
        <Property Name="id" Type="Edm.String" Nullable="false"/>
        <Property Name="student_roll" Type="Edm.String"/>
        <Property Name="student_name" Type="Edm.String"/>
        <Property Name="skill_name" Type="Edm.String"/>
        <Property Name="skill_category" Type="Edm.String"/>
        <Property Name="confidence" Type="Edm.Decimal"/>
        <Property Name="proficiency_level" Type="Edm.String"/>
        <Property Name="source" Type="Edm.String"/>
      </EntityType>

      <EntityContainer Name="CCIPService">
        <EntitySet Name="Students" EntityType="CCIP.Student"/>
        <EntitySet Name="Placements" EntityType="CCIP.Placement"/>
        <EntitySet Name="Drives" EntityType="CCIP.Drive"/>
        <EntitySet Name="Departments" EntityType="CCIP.Department"/>
        <EntitySet Name="Skills" EntityType="CCIP.Skill"/>
        <EntitySet Name="StudentSkills" EntityType="CCIP.StudentSkill"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>"""


@router.get("/odata/$metadata", summary="OData v4 metadata document (EDMX)")
async def odata_metadata():
    """
    Returns the OData v4 metadata document in EDMX XML format.
    Power BI Desktop reads this first when connecting via 'Get Data → OData Feed'.
    """
    return Response(
        content=ODATA_METADATA_XML,
        media_type="application/xml",
        headers={"OData-Version": "4.0"},
    )


def _odata_response(entity_set: str, values: list, count: Optional[int] = None) -> dict:
    """Wrap data in OData v4 JSON format."""
    result = {
        "@odata.context": f"/api/v1/bi/odata/$metadata#{entity_set}",
        "value": values,
    }
    if count is not None:
        result["@odata.count"] = count
    return result


@router.get("/odata/Students", summary="OData: Student records")
async def odata_students(
    top: int = Query(100, alias="$top", ge=1, le=5000),
    skip: int = Query(0, alias="$skip", ge=0),
    orderby: Optional[str] = Query(None, alias="$orderby"),
    current_user: User = Depends(_tpo_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Student entity set for Power BI / Tableau."""
    from sqlalchemy.orm import joinedload

    query = (
        select(Student)
        .options(joinedload(Student.user), joinedload(Student.department))
        .offset(skip)
        .limit(top)
    )
    result = await db.execute(query)
    students = result.unique().scalars().all()

    total = (await db.execute(select(func.count(Student.id)))).scalar_one()

    values = []
    for s in students:
        skill_count = (await db.execute(
            select(func.count(StudentSkill.id)).where(StudentSkill.student_id == s.id)
        )).scalar_one()
        placed = (await db.execute(
            select(func.count(PlacementOutcome.id)).where(PlacementOutcome.student_id == s.id)
        )).scalar_one()

        values.append({
            "id": str(s.id),
            "roll_number": s.roll_number,
            "full_name": f"{s.user.first_name} {s.user.last_name}" if s.user else "",
            "email": s.user.email if s.user else "",
            "department_code": s.department.code if s.department else "",
            "department_name": s.department.name if s.department else "",
            "current_semester": s.current_semester,
            "admission_year": s.admission_year,
            "cgpa": float(s.cgpa) if s.cgpa else None,
            "skill_count": skill_count,
            "is_placed": placed > 0,
        })

    return _odata_response("Students", values, total)


@router.get("/odata/Placements", summary="OData: Placement outcomes")
async def odata_placements(
    top: int = Query(100, alias="$top", ge=1, le=5000),
    skip: int = Query(0, alias="$skip", ge=0),
    current_user: User = Depends(_tpo_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Placement outcome entity set."""
    from sqlalchemy.orm import joinedload

    query = (
        select(PlacementOutcome)
        .options(joinedload(PlacementOutcome.student).joinedload(Student.user))
        .options(joinedload(PlacementOutcome.student).joinedload(Student.department))
        .offset(skip)
        .limit(top)
    )
    result = await db.execute(query)
    outcomes = result.unique().scalars().all()

    total = (await db.execute(select(func.count(PlacementOutcome.id)))).scalar_one()

    values = []
    for po in outcomes:
        values.append({
            "id": str(po.id),
            "student_roll": po.student.roll_number if po.student else "",
            "student_name": (
                f"{po.student.user.first_name} {po.student.user.last_name}"
                if po.student and po.student.user else ""
            ),
            "department_code": (
                po.student.department.code if po.student and po.student.department else ""
            ),
            "company_name": po.company_name,
            "role": po.role,
            "salary_ctc_lpa": float(po.salary_ctc) if po.salary_ctc else None,
            "placement_type": po.placement_type,
            "academic_year": po.academic_year,
            "recorded_at": po.recorded_at.isoformat() if po.recorded_at else None,
        })

    return _odata_response("Placements", values, total)


@router.get("/odata/Drives", summary="OData: Placement drives")
async def odata_drives(
    top: int = Query(100, alias="$top", ge=1, le=5000),
    skip: int = Query(0, alias="$skip", ge=0),
    current_user: User = Depends(_tpo_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Placement drive entity set."""
    from sqlalchemy.orm import joinedload

    query = (
        select(PlacementDrive)
        .options(joinedload(PlacementDrive.company))
        .offset(skip)
        .limit(top)
    )
    result = await db.execute(query)
    drives = result.unique().scalars().all()

    total = (await db.execute(select(func.count(PlacementDrive.id)))).scalar_one()

    values = []
    for d in drives:
        app_count = (await db.execute(
            select(func.count(Application.id)).where(Application.drive_id == d.id)
        )).scalar_one()

        values.append({
            "id": str(d.id),
            "title": d.title,
            "company_name": d.company.name if d.company else "",
            "company_industry": d.company.industry if d.company else "",
            "drive_date": d.drive_date.isoformat() if d.drive_date else None,
            "salary_ctc_lpa": float(d.salary_ctc) if d.salary_ctc else None,
            "status": d.status,
            "academic_year": d.academic_year,
            "min_cgpa": float(d.min_cgpa) if d.min_cgpa else None,
            "applications_count": app_count,
        })

    return _odata_response("Drives", values, total)


@router.get("/odata/Departments", summary="OData: Department master data")
async def odata_departments(
    current_user: User = Depends(_tpo_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Department entity set."""
    result = await db.execute(select(Department))
    depts = result.scalars().all()

    values = []
    for d in depts:
        count = (await db.execute(
            select(func.count(Student.id)).where(Student.department_id == d.id)
        )).scalar_one()
        values.append({
            "id": str(d.id),
            "code": d.code,
            "name": d.name,
            "student_count": count,
        })

    return _odata_response("Departments", values, len(values))


@router.get("/odata/Skills", summary="OData: Skills taxonomy")
async def odata_skills(
    top: int = Query(200, alias="$top", ge=1, le=5000),
    skip: int = Query(0, alias="$skip", ge=0),
    current_user: User = Depends(_tpo_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Skills entity set."""
    result = await db.execute(select(Skill).offset(skip).limit(top))
    skills = result.scalars().all()

    total = (await db.execute(select(func.count(Skill.id)))).scalar_one()

    values = [
        {
            "id": str(s.id),
            "name": s.name,
            "category": s.category,
            "domain": s.domain,
        }
        for s in skills
    ]

    return _odata_response("Skills", values, total)


@router.get("/odata/StudentSkills", summary="OData: Student-skill junction")
async def odata_student_skills(
    top: int = Query(500, alias="$top", ge=1, le=10000),
    skip: int = Query(0, alias="$skip", ge=0),
    current_user: User = Depends(_tpo_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Student-skill junction entity set with confidence scores."""
    from sqlalchemy.orm import joinedload

    query = (
        select(StudentSkill)
        .options(
            joinedload(StudentSkill.student).joinedload(Student.user),
            joinedload(StudentSkill.skill),
        )
        .offset(skip)
        .limit(top)
    )
    result = await db.execute(query)
    records = result.unique().scalars().all()

    total = (await db.execute(select(func.count(StudentSkill.id)))).scalar_one()

    values = []
    for ss in records:
        values.append({
            "id": str(ss.id),
            "student_roll": ss.student.roll_number if ss.student else "",
            "student_name": (
                f"{ss.student.user.first_name} {ss.student.user.last_name}"
                if ss.student and ss.student.user else ""
            ),
            "skill_name": ss.skill.name if ss.skill else "",
            "skill_category": ss.skill.category if ss.skill else "",
            "confidence": float(ss.confidence) if ss.confidence else 0,
            "proficiency_level": ss.proficiency_level,
            "source": ss.source,
        })

    return _odata_response("StudentSkills", values, total)


# ═══════════════════════════════════════════════════════════════════════════════
#  DATA EXPORT — CSV Downloads for Offline BI
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/export/{entity}", summary="Export entity data as CSV")
async def export_entity(
    entity: str,
    current_user: User = Depends(_tpo_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Exports placement data as CSV for offline analysis in Power BI, Superset, or Excel.
    Supported entities: students, placements, drives, skills, departments
    """
    entity = entity.lower()

    if entity == "students":
        return await _export_students_csv(db)
    elif entity == "placements":
        return await _export_placements_csv(db)
    elif entity == "drives":
        return await _export_drives_csv(db)
    elif entity == "skills":
        return await _export_skills_csv(db)
    elif entity == "departments":
        return await _export_departments_csv(db)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown entity '{entity}'. Supported: students, placements, drives, skills, departments",
        )


def _make_csv_response(rows: list[dict], filename: str) -> Response:
    """Convert list of dicts to CSV response."""
    if not rows:
        return Response(content="", media_type="text/csv")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _export_students_csv(db: AsyncSession) -> Response:
    from sqlalchemy.orm import joinedload

    result = await db.execute(
        select(Student).options(joinedload(Student.user), joinedload(Student.department))
    )
    students = result.unique().scalars().all()

    rows = []
    for s in students:
        rows.append({
            "roll_number": s.roll_number,
            "first_name": s.user.first_name if s.user else "",
            "last_name": s.user.last_name if s.user else "",
            "email": s.user.email if s.user else "",
            "department_code": s.department.code if s.department else "",
            "department_name": s.department.name if s.department else "",
            "semester": s.current_semester,
            "admission_year": s.admission_year,
            "cgpa": float(s.cgpa) if s.cgpa else "",
        })

    return _make_csv_response(rows, f"ccip_students_{datetime.now().strftime('%Y%m%d')}.csv")


async def _export_placements_csv(db: AsyncSession) -> Response:
    from sqlalchemy.orm import joinedload

    result = await db.execute(
        select(PlacementOutcome)
        .options(
            joinedload(PlacementOutcome.student).joinedload(Student.user),
            joinedload(PlacementOutcome.student).joinedload(Student.department),
        )
    )
    outcomes = result.unique().scalars().all()

    rows = []
    for po in outcomes:
        rows.append({
            "student_roll": po.student.roll_number if po.student else "",
            "student_name": (
                f"{po.student.user.first_name} {po.student.user.last_name}"
                if po.student and po.student.user else ""
            ),
            "department": po.student.department.code if po.student and po.student.department else "",
            "company_name": po.company_name,
            "role": po.role,
            "salary_ctc_lpa": float(po.salary_ctc) if po.salary_ctc else "",
            "placement_type": po.placement_type,
            "academic_year": po.academic_year or "",
            "recorded_at": po.recorded_at.isoformat() if po.recorded_at else "",
        })

    return _make_csv_response(rows, f"ccip_placements_{datetime.now().strftime('%Y%m%d')}.csv")


async def _export_drives_csv(db: AsyncSession) -> Response:
    from sqlalchemy.orm import joinedload

    result = await db.execute(
        select(PlacementDrive).options(joinedload(PlacementDrive.company))
    )
    drives = result.unique().scalars().all()

    rows = []
    for d in drives:
        rows.append({
            "title": d.title,
            "company": d.company.name if d.company else "",
            "industry": d.company.industry if d.company else "",
            "drive_date": d.drive_date.isoformat() if d.drive_date else "",
            "salary_ctc_lpa": float(d.salary_ctc) if d.salary_ctc else "",
            "status": d.status,
            "academic_year": d.academic_year or "",
            "min_cgpa": float(d.min_cgpa) if d.min_cgpa else "",
        })

    return _make_csv_response(rows, f"ccip_drives_{datetime.now().strftime('%Y%m%d')}.csv")


async def _export_skills_csv(db: AsyncSession) -> Response:
    result = await db.execute(select(Skill))
    skills = result.scalars().all()

    rows = [
        {
            "name": s.name,
            "category": s.category,
            "domain": s.domain or "",
            "description": s.description or "",
        }
        for s in skills
    ]

    return _make_csv_response(rows, f"ccip_skills_{datetime.now().strftime('%Y%m%d')}.csv")


async def _export_departments_csv(db: AsyncSession) -> Response:
    result = await db.execute(select(Department))
    depts = result.scalars().all()

    rows = [{"code": d.code, "name": d.name} for d in depts]

    return _make_csv_response(rows, f"ccip_departments_{datetime.now().strftime('%Y%m%d')}.csv")


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTITY COUNTS — for BI Studio dashboard cards
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/counts", summary="Entity record counts for BI Studio UI")
async def get_entity_counts(
    current_user: User = Depends(_tpo_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Returns record counts for each entity — shown on the Data Export cards."""
    students = (await db.execute(select(func.count(Student.id)))).scalar_one()
    placements = (await db.execute(select(func.count(PlacementOutcome.id)))).scalar_one()
    drives = (await db.execute(select(func.count(PlacementDrive.id)))).scalar_one()
    skills = (await db.execute(select(func.count(Skill.id)))).scalar_one()
    departments = (await db.execute(select(func.count(Department.id)))).scalar_one()

    return {
        "students": students,
        "placements": placements,
        "drives": drives,
        "skills": skills,
        "departments": departments,
        "total_records": students + placements + drives + skills,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }

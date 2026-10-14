# 🧑‍💻 Yash's Task Sheet (Sprint 2) — Institutional Audit Trail, Accreditation Reports & Production Docker

> **Role:** Lead Architect & Platform Reliability Engineer
> **Priority:** 🔴 P0 — Blocks production readiness and university compliance sign-off
> **Reference Standard:** QS Campus Intelligence, Ellucian Banner, NAAC/NIRF Institutional Portals
> **Estimated Effort:** ~3–4 days

---

## 📋 Industrial Context — Why This Matters

This sprint converts CCIP from a **working demo** into an **enterprise-grade institutional governance system** that a Vice-Chancellor or IQAC Coordinator can actually use during an accreditation audit. Three things are completely missing right now:

1. **Statutory Compliance Reporting:** Universities submitting to NIRF (National Institutional Ranking Framework) must provide exact placement rates, CTC medians, sector diversity, and gender parity metrics in a prescribed format. There is currently zero ability to export these.
2. **Silent Audit Trail:** Every action a TPO takes (shortlisting a candidate, overriding marks, triggering UMS sync) must be traceable to a person, timestamp, and IP address. The DB table `SystemLog` exists in `backend/app/models/system.py` but is never written to.
3. **Deployment is Dev-Only:** `docker compose up` currently starts everything in hot-reload development mode. Production needs Gunicorn + UvicornWorker, Nginx reverse proxy, PostgreSQL (not SQLite), and automatic DB migration + seed on first boot.

---

## TASK 1: NIRF / NAAC Accreditation Report Generator

### Files to Create / Modify

- **CREATE:** `backend/app/services/accreditation_service.py`
- **MODIFY:** `backend/app/api/v1/analytics.py` — add 2 new routes
- **MODIFY:** `frontend/src/pages/tpo/Analytics.jsx` — add export UI
- **MODIFY:** `frontend/src/api/endpoints.js` — add `analyticsApi.getAccreditationReport()`

### Backend: `accreditation_service.py`

Create a service class `AccreditationService` with these exact methods:

```python
class AccreditationService:
    def __init__(self, db: AsyncSession): ...

    async def compute_nirf_1a(self, academic_year: str) -> dict:
        """
        NIRF Metric 1A - Placement and Higher Studies.
        Returns: {
            "total_graduating": int,
            "placed_count": int,
            "higher_studies_count": int,
            "placement_pct": float,
            "median_ctc_lpa": float,
            "top10_ctc_lpa": float,
            "avg_ctc_lpa": float,
            "gender_breakdown": {"male": int, "female": int, "other": int},
        }
        Calculation: query Application table where status='selected',
        join Student for gender, aggregate CTC from offer_ctc field.
        """

    async def compute_sector_diversity(self, academic_year: str) -> list:
        """
        NIRF Metric 1C - Top Recruiter Diversity.
        Group PlacementDrive by company_industry, count selected applications per industry.
        Returns: [{"sector": "IT", "count": 45, "pct": 62.5}, ...]
        """

    async def compute_curriculum_remediation_rate(self) -> dict:
        """
        NAAC Criteria 1.1.3 - pct students completing remediation roadmaps.
        Count students who have at least one RoadmapTask with status='completed'
        that was auto-generated (has 'remedial' in task title or description).
        Returns: {"remediation_enrolled": int, "completed_remediation": int, "rate_pct": float}
        """

    async def build_full_report(self, academic_year: str, format: str) -> dict:
        """Assembles all metrics into one structured object or CSV string."""
```

### Backend API Routes (add to `analytics.py`)

```python
@router.get("/accreditation/report")
async def get_accreditation_report(
    academic_year: str = Query("2026-27"),
    format: str = Query("json"),   # 'json' or 'csv'
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """Returns full NIRF/NAAC placement metrics. Set format=csv to download spreadsheet."""
    svc = AccreditationService(db)
    report = await svc.build_full_report(academic_year, format)
    if format == "csv":
        return Response(content=report, media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="nirf_report_{academic_year}.csv"'})
    return report

@router.get("/accreditation/preview")
async def preview_accreditation_metrics(
    academic_year: str = Query("2026-27"),
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """Returns quick summary card for the Analytics dashboard preview panel."""
    svc = AccreditationService(db)
    return await svc.compute_nirf_1a(academic_year)
```

### Frontend: `Analytics.jsx` — New Section

Add a **"Accreditation and NIRF Dossier"** section at the bottom of the Analytics page. It should show:

- A year-selector dropdown (2024-25, 2025-26, 2026-27)
- Four stat cards: Placement Rate, Median CTC, Top 10% CTC, Remediation Rate
- A horizontal sector bar: IT | Core Engineering | BFSI | Consulting
- Two action buttons: "Export Dossier (JSON)" and "Download NIRF CSV"

**Behavior rules:**

- Changing the year dropdown triggers a re-fetch from `/accreditation/preview`.
- "Export JSON" serializes the API response and triggers `<a download>` from a Blob URL.
- "Download CSV" calls `/accreditation/report?format=csv` and uses the browser's native download via response headers.
- Show animated skeleton placeholders while fetching.

---

## TASK 2: Institutional Audit Trail & Activity Log

### Files to Create / Modify

- **CREATE:** `backend/app/core/audit.py`
- **MODIFY:** `backend/app/api/v1/drives.py` — inject audit calls on POST/PATCH
- **MODIFY:** `backend/app/api/v1/applications.py` — inject audit call on PATCH
- **MODIFY:** `backend/app/api/v1/ums.py` — inject audit call on POST /sync
- **CREATE:** `backend/app/api/v1/system.py` — new router for audit log viewing
- **MODIFY:** `backend/app/main.py` — register the new `/api/v1/system` router
- **MODIFY:** `frontend/src/pages/tpo/Dashboard.jsx` — add Audit Log drawer

### Backend: `core/audit.py`

```python
import uuid, sys
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system import SystemLog

AUDIT_EVENTS = [
    "DRIVE_CREATE", "DRIVE_UPDATE", "DRIVE_CANCEL",
    "APPLICATION_STATUS_CHANGE", "OFFER_RECORDED",
    "UMS_SYNC_TRIGGERED", "SKILL_VERIFIED",
    "STUDENT_PROFILE_UPDATE", "SHORTLIST_GENERATED",
    "ACCREDITATION_REPORT_EXPORTED",
]

async def record_audit_event(
    db: AsyncSession,
    actor_id: uuid.UUID,
    event_type: str,
    resource_type: str,
    resource_id: str,
    details: dict,
    ip_address: Optional[str] = None,
) -> None:
    """
    Writes one immutable audit row to SystemLog.
    Call this INSIDE any endpoint that mutates sensitive state.
    IMPORTANT: Use db.flush() NOT db.commit() — let the endpoint's own commit handle it.
    Never raises — silently logs errors to stderr if DB write fails.
    """
    try:
        log = SystemLog(
            actor_id=str(actor_id),
            event_type=event_type,
            resource_type=resource_type,
            resource_id=str(resource_id),
            details=details,
            ip_address=ip_address,
        )
        db.add(log)
        await db.flush()
    except Exception as exc:
        print(f"[AUDIT] Failed to write audit log: {exc}", file=sys.stderr)
```

**Where to call `record_audit_event` (exact injection points):**

| Endpoint                                   | File                             | Event Type                      | Details Example                                          |
| ------------------------------------------ | -------------------------------- | ------------------------------- | -------------------------------------------------------- |
| `POST /drives`                             | `drives.py`                      | `DRIVE_CREATE`                  | `{"company": name, "title": title, "drive_id": str(id)}` |
| `PATCH /drives/{id}`                       | `drives.py`                      | `DRIVE_UPDATE`                  | `{"drive_id": id, "changed_fields": list(data.keys())}`  |
| `PATCH /drives/{id}/applications/{app_id}` | `drives.py` or `applications.py` | `APPLICATION_STATUS_CHANGE`     | `{"app_id": aid, "old_status": prev, "new_status": new}` |
| `POST /ums/sync`                           | `ums.py`                         | `UMS_SYNC_TRIGGERED`            | `{"roll_number": rn}`                                    |
| `GET /accreditation/report`                | `analytics.py`                   | `ACCREDITATION_REPORT_EXPORTED` | `{"year": yr, "format": fmt}`                            |

### Backend: `api/v1/system.py`

```python
router = APIRouter(prefix="/system", tags=["System & Audit"])

@router.get("/audit-logs")
async def get_audit_logs(
    event_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns paginated SystemLog entries. Newest first.
    Filter by event_type (exact match), actor_id (partial match ok), date range.
    """
```

### Frontend: Audit Log Drawer in `tpo/Dashboard.jsx`

Add a **"Activity and Audit Trail"** button (top-right, next to or below the existing KPI cards).

Drawer design requirements:

- Slides in from the RIGHT side, full viewport height, 480px wide, scrollable
- Dark overlay behind it (semi-transparent, clickable to close)
- Filter bar at top: Event Type dropdown, Date From/To pickers, Actor search input
- Each log entry displayed as a timeline item with:
  - Color-coded left border (green=CREATE, yellow=UPDATE, red=STATUS_CHANGE, blue=SYNC)
  - Event type badge (e.g. `DRIVE_CREATE`)
  - Actor name/email
  - Time ago (write a simple helper: `function timeAgo(isoDate)` — returns "2 minutes ago", "3 hours ago", "Yesterday", etc.)
  - Expandable details: click to see the `details` JSON payload
- Infinite scroll OR "Load More" button for pagination

---

## TASK 3: Production Docker Orchestration

### Files to Modify / Create

- **MODIFY:** `docker-compose.yml` — full production rewrite
- **MODIFY:** `backend/Dockerfile` — switch to Gunicorn
- **MODIFY:** `frontend/Dockerfile` — multi-stage Nginx build
- **CREATE:** `backend/scripts/entrypoint.sh`
- **CREATE/MODIFY:** `backend/scripts/seed.py`

### `docker-compose.yml` Target Architecture

```
postgres (pgvector/pgvector:pg16) + Redis 7
    |
backend (Gunicorn + 4x UvicornWorker) <-- runs entrypoint.sh on start
    |
worker (Celery + same backend image)
    |
frontend (Nginx serving Vite production build)
```

All services must have `healthcheck` and `depends_on` with `condition: service_healthy` to ensure boot order.

All secrets (`POSTGRES_PASSWORD`, `JWT_SECRET_KEY`, `GEMINI_API_KEY`) must be loaded from environment variables (not hardcoded). Create a `.env.example` file at the repo root with placeholder values.

### `backend/scripts/entrypoint.sh`

```bash
#!/bin/bash
set -e
echo "Running Alembic migrations..."
python -m alembic upgrade head

echo "Seeding initial data..."
python -m scripts.seed

echo "Starting Gunicorn..."
exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile -
```

### `backend/scripts/seed.py` Requirements

Must be **idempotent** — safe to run multiple times without creating duplicates.
Use `SELECT ... WHERE email = ?` before inserting, and only insert if not found.

Seed data to create:

- 1 TPO user: `tpo@ccip.edu` / `tpo@1234`
- 1 Faculty user: `faculty@ccip.edu` / `fac@1234`
- 5 Students: `student1@ccip.edu` through `student5@ccip.edu`, password `stud@1234`, with realistic profiles (CGPA 7.5-9.2, departments CS/IT/ECE)
- 3 PlacementDrives: Amazon SDE (CTC: 24 LPA, min CGPA 7.5), Google SWE (CTC: 42 LPA, min CGPA 8.5), TCS Digital (CTC: 7 LPA, min CGPA 6.0)
- Skills: Python, React, Docker, SQL, FastAPI, Machine Learning

---

## Checklist — What "Done" Looks Like

- [ ] TPO can select any academic year and download a NIRF-formatted placement CSV in one click
- [ ] Analytics page shows a live accreditation preview card with placement %, median CTC, sector breakdown
- [ ] Every drive creation, application status change, UMS sync, and report export writes a row to `SystemLog`
- [ ] TPO Dashboard shows an "Activity and Audit Trail" drawer with searchable, paginated audit events
- [ ] `docker compose up --build` (with a `.env` file) brings up all 5 services cleanly
- [ ] On first boot, Alembic migrations run, then seed data is created, then Gunicorn starts
- [ ] Backend runs under Gunicorn with 4 UvicornWorkers in production
- [ ] Frontend is served by Nginx from a Vite production build

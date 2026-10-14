# 🧑‍💻 Yash's Task Sheet (Sprint 2) — Institutional Audit Logs, Accreditation Reporting & System Health

> **Role:** Lead Architect & Platform Reliability. Transform the platform from a demo into an enterprise institutional governance system.
> **Priority:** 🔴 P0 (Required for university compliance, accreditation audits, and production ops)
> **Reference Standard:** QS Campus Intelligence, Ellucian, Superset Institutional Admin

---

## 📋 Industrial Context & The Core Problem

In commercial campus management software, institutional stakeholders (Dean of Academic Affairs, Vice-Chancellor, IQAC coordinators) must generate formal accreditation reports (**NIRF / NAAC / NBA**). Currently:
1. **Accreditation Reporting is Missing:** There is no way for the administration to export structured placement statistics, gender parity metrics, median CTC, and department-wise placement percentages required for statutory ranking submissions.
2. **Audit Logging is Silent:** The database defines a `SystemLog` table in `models/system.py`, but sensitive actions (mark overrides, TPO shortlists, status overrides, UMS sync runs) are not systematically tracked with actor ID, IP address, and payload history.
3. **Production Deployment Orchestration:** The backend and frontend run separately in dev mode, but need full multi-container production readiness (Postgres with pgvector, Redis, Celery worker, and Nginx reverse proxy).

---

## TASK 1: Build the Institutional Accreditation Report Generator (NIRF / NAAC / NBA)

### What you need to do
Create a dedicated backend service and export endpoint that calculates official institutional ranking metrics:

**File to Create:** `backend/app/services/accreditation_service.py`
- **Metric 1: Placement & Higher Studies Ratio (NIRF Metric 1A):**
  - $\text{Placement \%} = \frac{\text{Students Placed with CTC} \ge \text{Threshold}}{\text{Total Graduating Batch}} \times 100$
- **Metric 2: Median Salary Package (NIRF Metric 1B):**
  - Calculation of 50th percentile CTC, top 10th percentile, and lowest package per department.
- **Metric 3: Top Recruiter Diversity Index:**
  - Distribution of offers across sectors (IT, Core Engineering, Product, BFSI, Consulting).
- **Metric 4: Curriculum Gap Remediation Rate (NAAC Criteria 1.1.3 & 1.2.1):**
  - Average percentage of students completing remedial roadmaps before final year drives.

**API Route to Add:** in `backend/app/api/v1/analytics.py`
```python
@router.get("/accreditation/report", summary="Download official institutional accreditation metrics")
async def get_accreditation_report(
    academic_year: str = "2026-27",
    format: str = "json", # 'json' or 'csv'
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    ...
```

**Frontend Integration:**
In `frontend/src/pages/tpo/Analytics.jsx`, add an **"Export Accreditation Dossier (NIRF / NAAC)"** button that triggers a download of the report with a breakdown modal.

---

## TASK 2: Institutional Audit & Security Activity Trail

### What exists now
`backend/app/models/system.py` has a `SystemLog` ORM model, but it is rarely invoked.

### What you need to do
1. **Middleware / Service Logger:** Create `backend/app/core/audit.py` with an async helper:
   ```python
   async def record_audit_event(
       db: AsyncSession,
       actor_id: uuid.UUID,
       event_type: str, # "DRIVE_CREATE", "APPLICANT_STATUS_OVERRIDE", "UMS_SYNC", "SKILL_VERIFY"
       resource_type: str,
       resource_id: str,
       details: dict,
       ip_address: Optional[str] = None,
   ):
       ...
   ```
2. **Expose Audit Log API:** `GET /api/v1/system/audit-logs` (filterable by date range, actor, event type, paginated).
3. **Audit Viewer UI:** Add an **"Activity & Audit Trail"** tab/drawer in `frontend/src/pages/tpo/Dashboard.jsx` so TPOs can see who approved which shortlist, changed candidate statuses, or triggered UMS syncs.

---

## TASK 3: Full Containerization & Health Orchestration

### What you need to do
1. Update `docker-compose.yml` so that a single `docker compose up --build` launches:
   - `postgres`: PostgreSQL 16 with `pgvector` extension enabled.
   - `redis`: Task queue broker.
   - `backend`: FastAPI running under `gunicorn` with `uvicorn.workers.UvicornWorker`.
   - `worker`: Celery worker running UMS sync and periodic assessment grading.
   - `frontend`: Vite production build served through an Nginx alpine container.
2. Verify automated DB migrations and seeding run automatically on initial startup.

---

## ✅ Checklist — What "Done" Looks Like
- [ ] TPO can download a comprehensive NIRF/NAAC placement audit report in JSON/CSV
- [ ] Every drive creation, application status update, and UMS sync creates an immutable audit row in `SystemLog`
- [ ] TPO portal features an interactive "Audit Log" drawer with searchable activity records
- [ ] `docker compose up --build` boots up clean and healthy with all services communicating

# 🧑‍💻 Purushottam's Final Task Sheet — TPO Operations Command Centre: Drives Lifecycle, Bulk Shortlisting, Drive Calendar & Institutional Accreditation

> **Role:** TPO Operations & Enterprise Recruiter CRM Engineer  
> **Priority:** 🔴 P0 — Core Placement Operations & Accreditation  
> **Reference Standard:** Superset BI, Handshake University Portal, Yello Campus Recruiting, NIRF / NAAC Standards  

---

## 📋 Industrial Context — Why This Final Submission Matters

The Training & Placement Office (TPO) is the nerve center of university placements. When 80+ companies visit campus to recruit across 1,000+ candidates:
1. **Spreadsheets Collapse:** Managing student eligibility, backlog criteria, multi-round interview shortlists, and offer letters via Excel leads to data corruption, duplicate offers, and student disputes.
2. **Scheduling Conflicts:** Multiple companies conducting rounds on the same day cause room shortages and interview overlap.
3. **Accreditation Chaos:** When government accreditation bodies (NIRF, NAAC, NBA) request official graduating cohort statistics, manual aggregation takes weeks and frequently contains discrepancies.

In CCIP, you built the enterprise operations engine:
- **Placement Drive End-to-End Lifecycle:** From job posting to final offer letter release.
- **Automated Bulk Shortlisting Engine:** Filter hundreds of candidates in milliseconds based on CGPA floors, department eligibility, backlog thresholds, and verified skills.
- **Placement Calendar Scheduler:** Conflict-free interview scheduling with automated student calendar invitations.
- **Institutional Accreditation Engine:** Automated NIRF Metric 1A (placement % and CTC metrics), Metric 1C (sector diversity), and NAAC 1.1.3 dossier exports in structured JSON and CSV formats.
- **Enterprise Recruiter Portal:** Dedicated company portal for reviewing candidates and submitting interview round feedback.

---

## TASK 1: Placement Drive End-to-End Lifecycle

### Drive Management Endpoints (`/drives`)
In `backend/app/api/v1/drives.py` and `backend/app/models/placement.py`:
- `POST /drives`: Create new placement drives with company ID, job title, job description, CTC packages (Base, Bonus, Total LPA), job location, application deadlines, and eligibility criteria.
- **Eligibility Engine:** Enforces multi-criteria rules before allowing applications:
  - Minimum CGPA floor
  - Allowed department codes (e.g., `["CS", "IT", "ECE"]`)
  - Maximum active backlogs allowed (0 for most Tier-1 recruiters)
  - Graduation cohort year
- Application status progression state machine:
  `applied` -> `shortlisted` -> `in_progress` -> `selected` / `rejected` / `withdrawn`.
- Enforces database uniqueness constraint `uq_student_drive_application` to prevent double-applying.

### Frontend UI (`frontend/src/pages/tpo/Drives.jsx`)
- Visual card grid displaying active drives, applicant count, seat-fill progress bars, and countdown timer to application deadline.
- Create Drive Modal with dynamic department multiselect and CTC package sliders.

---

## TASK 2: Automated Bulk Shortlisting Engine

### Shortlist Filter Endpoint (`POST /drives/{drive_id}/bulk-shortlist`)
In `backend/app/api/v1/drives.py`:
- Accepts multi-parameter filter payload:
  ```json
  {
    "min_cgpa": 7.5,
    "max_backlogs": 0,
    "required_skills": ["Python", "SQL"],
    "allowed_departments": ["CS", "IT"],
    "target_stage": "Technical Interview Round 1"
  }
  ```
- Executes single atomic database query selecting eligible applicants and automatically promotes their status to `shortlisted`.
- Records shortlisting decision in `applications.extra_metadata` with audit explanation.

### Applicant Reviewer UI (`frontend/src/pages/tpo/Students.jsx`)
- Filterable student roster with live CGPA range sliders, department filters, and placement status toggles.
- Batch actions: "Export Selected Candidates (CSV)", "Promote to Next Round", "Send WhatsApp/Email Broadcast".

---

## TASK 3: Placement Calendar & Logistics Scheduler

### Calendar Service (`backend/app/api/v1/calendar.py`)
- `GET /calendar/events`: Returns all upcoming campus placement milestones across active drives:
  - Pre-Placement Talks (PPTs)
  - Online Assessment Windows
  - Technical Interview Slots
  - HR Interview Rounds
- Checks for room/slot scheduling conflicts: Flags warnings if two Tier-1 companies schedule technical interviews for the same department cohort simultaneously.
- Generates standard iCal / calendar payloads for integration into student dashboards.

---

## TASK 4: Digital Offer Letter Pipeline & Recruiter CRM

### Offer Release Engine (`backend/app/api/v1/offer_letters.py`)
- `POST /offer-letters/release`: TPO releases formal digital offer letter to selected student:
  - Role title, company name, offered CTC (LPA), joining date, and acceptance deadline.
- Student workflow:
  - Students review offer letter in `/student/applications`.
  - Actions: **Accept Offer** (confirms placement and updates NIRF statistics) or **Decline Offer** (captures mandatory reason for decline).
- Automatically updates student placement status to "Placed" and updates company hiring analytics.

### Recruiter Portal (`/recruiter/*`)
- Dedicated portal for corporate HR partners (`recruiter@ccip.edu` / `recruiter123`).
- **Dashboard (`/recruiter/dashboard`):** Company's active drives, applicant volume, and pipeline breakdown.
- **Applicant Evaluation (`/recruiter/drives/{id}/applicants`):** Download resumes, view verified skill badges, enter interview round scores (1–10), and release offers directly.

---

## TASK 5: Institutional Accreditation Engine (NIRF & NAAC)

### NIRF 1A & 1C Calculation Service (`backend/app/services/accreditation_service.py`)
- **Metric 1A — Overall Placement & Higher Studies:**
  ```python
  async def compute_nirf_1a(self, academic_year: str) -> dict:
      # Placed count from selected applications
      # Higher studies count queried from placement_outcomes where placement_type in ('higher_studies', 'higher_education')
      # Median CTC, Mean CTC, Top-10% CTC calculated using statistics module
      # Gender breakdown aggregated from linked users table
      return {
          "academic_year": academic_year,
          "total_graduating": total_graduating,
          "placed_count": placed_count,
          "higher_studies_count": higher_studies_count,
          "placement_pct": placement_pct,
          "median_ctc_lpa": median_ctc,
          "top10_ctc_lpa": top10_ctc,
          "avg_ctc_lpa": avg_ctc,
          "gender_breakdown": gender_breakdown,
      }
  ```
- **Metric 1C — Sector Diversity:** Aggregates hires across Product, IT Services, Finance/Fintech, Core Engineering, and Consulting sectors.
- **Dossier Exporters:**
  - `GET /analytics/accreditation/preview`: Instant metrics preview on TPO Dashboard.
  - `GET /analytics/accreditation/report?format=csv`: Downloadable, official CSV file structured for direct submission to government accreditation portals.
  - Audit: Every export event is permanently logged in `audit_logs`.

---

## 🛠️ Verification & Test Runbook

```powershell
# 1. Run drive, application, and accreditation test suites
cd d:\Projects\p1\backend
.\.venv\Scripts\pytest.exe tests/test_drives_and_applications.py tests/test_audit_and_accreditation.py -v

# 2. Test accreditation report export
python -c "
import asyncio, sys
sys.path.insert(0, '.')
from app.core.database import AsyncSessionLocal
from app.services.accreditation_service import AccreditationService
async def test():
    async with AsyncSessionLocal() as db:
        svc = AccreditationService(db)
        res = await svc.compute_nirf_1a('2026-27')
        print('NIRF 1A Computed Successfully:', res['placement_pct'], '% placed')
asyncio.run(test())
"

# 3. Verify frontend build
cd d:\Projects\p1\frontend
npm run build
```

---

## 🎓 Viva Defense Talking Points (For External Examiners)

1. **How Does the Portal Prevent Double Job Offers?**  
   *"Universities enforce 'One Student, One Job' or 'Dream Company' policies. In our database, once a student accepts an offer in the offer letter pipeline, the eligibility engine automatically flags them as placed, preventing them from applying to standard drives while allowing applications only to designated dream/super-dream drives."*
2. **How Does CCIP Help in NIRF and NAAC Accreditation?**  
   *"Accreditation committees require verifiable proof of graduating student placement percentages, median salaries, and gender ratios. Our Accreditation Engine generates compliance dossiers in 1-click directly from cryptographically signed database records, eliminating manual data tampering."*
3. **What is the Architecture of the Recruiter Portal?**  
   *"Recruiters have a scoped security perimeter. Using role-based authorization (`RoleChecker(['recruiter'])`) and company foreign key binding, a recruiter can only see students who applied to their specific company's drives."*

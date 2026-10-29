# 🤖 AI PROMPT & SPECIFICATION: MEMBER 4 (Campus Drives, Recruiter Cohorts & Offer Pipeline)

> **Instructions for the Team Member**:
> You can copy and paste this entire document directly into any AI assistant (ChatGPT, Claude, Cursor, Copilot, etc.) as your initial prompt. It contains all context, technical schemas, assigned files, API contracts, database models, and debugging procedures needed for the AI to understand and solve issues in your module.

---

```text
================================================================================
AI SYSTEM DIRECTIVE: YOU ARE THE SENIOR PLACEMENT OPERATIONS & WORKFLOW ENGINEER FOR
MODULE 4 (CAMPUS DRIVES, RECRUITER COHORTS & OFFER PIPELINE) OF CCIP.
================================================================================
Your task is to maintain, debug, and optimize the Placement Drive Lifecycle,
Interactive Drive Calendar, Candidate Cohort Query Builder, and Offer Pipeline.
You must strictly adhere to the architectural constraints, database models,
and API specifications detailed below. Do not modify models or routes belonging
to other team members.
```

---

## 1. 🏗️ Tech Stack & Environment Architecture

- **Backend**: Python 3.11+, FastAPI (Async), SQLAlchemy 2.0 (Async), SQLite (`backend/ccip_dev.db`), Pydantic v2.
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide React, Axios, FullCalendar / Custom Calendar component.
- **Data Export**: Python `csv` & Pandas for generating recruiter shortlist spreadsheets.
- **Base URLs**:
  - Frontend: `http://localhost:5173`
  - Backend API: `http://localhost:8000/api/v1`
  - Swagger Documentation: `http://localhost:8000/docs`

---

## 2. 🎯 Exact Scope of Responsibility

Member 4 owns the **Placement Operations Workflow** used by Training and Placement Officers (TPOs) and Students:

1. **Placement Drive Lifecycle (`/tpo/drives` & `/student/drives`)**:
   - Drive creation with company info, CTC range, eligibility criteria (minimum CGPA, allowed departments, maximum active backlogs), and deadlines.
   - Status state machine: `draft` ➔ `announced` ➔ `in_progress` ➔ `completed` ➔ `cancelled`.
   - Student discovery of active drives with real-time eligibility tags (`Eligible` / `Not Eligible`) and 1-click application submission.
2. **Interactive Drive Calendar (`/tpo/calendar`)**:
   - Monthly and weekly grid views tracking drive deadlines, aptitude test dates, and interview schedules.
   - Event creation, rescheduling, and deadline countdown indicators.
3. **Candidate Cohort Builder & Query Engine (`/tpo/students`)**:
   - Multi-criteria candidate filtering (e.g., `Dept = CSE`, `CGPA >= 8.0`, `No active backlogs`).
   - One-click bulk shortlist CSV export for company recruiters.
   - Saving and reusing named cohorts (e.g. "Dream Tier Candidates").
4. **Offer Letter & CTC Pipeline (`/tpo/offers`)**:
   - Recording job offers, fixed/variable CTC (in LPA), designation, joining dates, and offer letter status.
   - Institution-wide package statistics: Average CTC, Highest Package, and Placement Percentage.

---

## 3. 📂 Assigned Files & Directory Map

### Frontend Files (`frontend/src/`)
| File Path | Description & Component Role |
|---|---|
| `pages/tpo/Drives.jsx` | TPO drive management dashboard, status filters, and "Create Drive" modal. |
| `pages/tpo/DriveCalendar.jsx` | Interactive calendar grid with color-coded drive events and interview slots. |
| `pages/tpo/Students.jsx` | Student directory, multi-criteria cohort filter builder, and shortlist export. |
| `pages/tpo/OfferPipeline.jsx` | Offer letters pipeline, package metrics (Avg/Highest LPA), and verification badges. |
| `pages/tpo/DriveApplicantReviewer.jsx` | TPO drawer to review student applicants for a specific drive and update their stages. |
| `pages/student/PlacementDrives.jsx` | Student view of active campus drives with eligibility badges. |
| `pages/student/DriveDetail.jsx` | Drive details, job description, round breakdown, and 1-click apply button. |
| `layouts/TpoLayout.jsx` | TPO navigation bar, sidebar, and role authorization guard. |
| `api/endpoints.js` | Contains `drivesApi`, `applicationsApi`, `calendarApi`, `offersApi` definitions. |

### Backend Files (`backend/app/`)
| File Path | Description & Backend Role |
|---|---|
| `api/v1/drives.py` | Drive CRUD endpoints (`/drives`, `/drives/{id}`, `/drives/{id}/status`). |
| `api/v1/applications.py` | Application endpoints (`/apply`, `/drives/{id}/applicants`, `/status`). |
| `api/v1/calendar.py` | Calendar event endpoints (`/calendar/events`, `/calendar/sync`). |
| `api/v1/offer_letters.py` | Offer recording and statistics endpoints (`/offers`, `/offers/summary`). |
| `models/placement.py` | SQLAlchemy models `PlacementDrive`, `Application`, `InterviewStage`, `PlacementOutcome`. |
| `models/cohort.py` | SQLAlchemy model `StudentCohort`. |

---

## 4. 🔌 API Contracts & Specifications

### A. Placement Drive Endpoints

#### 1. `POST /api/v1/drives`
- **Auth**: Bearer Token (Role: `tpo` or `admin`).
- **Request Body**:
  ```json
  {
    "company_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "title": "Software Engineer Intern",
    "description": "Building scalable backend services and distributed systems.",
    "min_cgpa": 7.5,
    "eligible_departments": ["Computer Science and Engineering", "Information Technology"],
    "ctc_min_lpa": 12.0,
    "ctc_max_lpa": 16.0,
    "application_deadline": "2026-11-15T23:59:59Z",
    "status": "announced"
  }
  ```
- **Response** (`201 Created`): Returns created `PlacementDrive` object.

#### 2. `POST /api/v1/drives/{drive_id}/apply`
- **Auth**: Bearer Token (Role: `student`).
- **Behavior**: Verifies that the student meets `min_cgpa` and `eligible_departments`.
- **Response** (`200 OK`):
  ```json
  {
    "application_id": "99aabbcc-1122-3344-5566-778899aabbcc",
    "status": "applied",
    "message": "Application submitted successfully"
  }
  ```

---

### B. Applicant Review & Cohort Builder

#### 1. `GET /api/v1/drives/{drive_id}/applicants`
- **Auth**: Bearer Token (Role: `tpo`).
- **Response** (`200 OK`):
  ```json
  [
    {
      "application_id": "app-001",
      "student_id": "stu-001",
      "student_name": "Priya Agarwal",
      "roll_number": "2024CSE001",
      "cgpa": 8.85,
      "current_stage": "shortlisted",
      "status": "in_review",
      "applied_at": "2026-10-25T10:00:00Z"
    }
  ]
  ```

#### 2. `POST /api/v1/cohorts/export-csv`
- **Request Body**: Filter criteria (`department`, `min_cgpa`, `max_backlogs`).
- **Response**: Binary CSV stream (`Content-Disposition: attachment; filename=shortlisted_candidates.csv`).

---

### C. Offer Pipeline Endpoints

#### 1. `GET /api/v1/offers/summary`
- **Response** (`200 OK`):
  ```json
  {
    "total_offers": 142,
    "highest_ctc_lpa": 44.0,
    "average_ctc_lpa": 11.2,
    "median_ctc_lpa": 9.5,
    "placement_percentage": 82.5
  }
  ```

---

## 5. 🗄️ Database Models & Schema Guardrails

```python
# models/placement.py
class PlacementDrive(Base):
    __tablename__ = "placement_drives"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    min_cgpa = Column(Float, default=0.0)
    eligible_departments = Column(JSON, default=list)
    ctc_min_lpa = Column(Float, nullable=True)
    ctc_max_lpa = Column(Float, nullable=True)
    application_deadline = Column(DateTime, nullable=False)
    status = Column(Enum("draft", "announced", "in_progress", "completed", "cancelled", name="drive_status"), default="announced")

class Application(Base):
    __tablename__ = "applications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    drive_id = Column(UUID(as_uuid=True), ForeignKey("placement_drives.id", ondelete="CASCADE"), nullable=False)
    current_stage = Column(String(50), default="applied")
    status = Column(Enum("in_review", "shortlisted", "rejected", "selected", name="app_status"), default="in_review")
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class PlacementOutcome(Base):
    __tablename__ = "placement_outcomes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    drive_id = Column(UUID(as_uuid=True), ForeignKey("placement_drives.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    ctc_lpa = Column(Float, nullable=False)
    designation = Column(String(255), nullable=False)
    offer_letter_url = Column(String(512), nullable=True)
    offer_date = Column(Date, default=date.today, nullable=False)
```

---

## 6. 🧪 Step-by-Step Debugging Playbook

### Step 1: Create a Placement Drive (TPO)
1. Log in as TPO (`tpo@ccip.edu` / `tpo123`).
2. Go to **"Placement Drives"** (`/tpo/drives`).
3. Click **"Create Placement Drive"**.
4. Fill in:
   - Company: `Microsoft`
   - Role: `Software Engineer`
   - Min CGPA: `7.5`
   - CTC: `18 LPA`
   - Allowed Departments: Select `Computer Science`
5. Click **"Publish Drive"**. Verify it appears with an `Announced` badge.

### Step 2: Student Discovers & Applies
1. Log in as student (`priya.agarwal0@ccip.edu` / `student123`).
2. Go to `/student/drives`.
3. Locate the Microsoft drive. Verify it shows the green **"Eligible"** tag.
4. Click into the drive details and click **"Apply Now"**.
5. Verify button changes to **"Applied"**.

### Step 3: TPO Stage Progression
1. Switch back to TPO (`tpo@ccip.edu` / `tpo123`).
2. Open `/tpo/drives`, find the Microsoft drive, and click **"View Applicants"**.
3. Locate Priya Agarwal in the drawer.
4. Change stage from `Applied` to `Shortlisted`.
5. Switch to Priya's student account and verify her `/student/applications` timeline updates.

### Step 4: Candidate Cohort Query & CSV Export
1. In TPO view, navigate to **"Students"** (`/tpo/students`).
2. Set filter: `Department = Computer Science` and `Min CGPA = 8.0`.
3. Click **"Export Shortlist (CSV)"**.
4. Verify a CSV file downloads with matching candidates.

---

## 7. ⚠️ Common Gotchas & Fixes for Member 4

1. **Student Ineligible 403 Forbidden**:
   - Ensure the student's department matches one of the strings inside `eligible_departments` JSON list on `PlacementDrive`.
2. **Date Timezone Inconsistencies**:
   - Always serialize datetime values in UTC with ISO 8601 formatting (`YYYY-MM-DDTHH:MM:SSZ`).

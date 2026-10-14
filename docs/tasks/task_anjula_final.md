# 🧑‍💻 Anjula's Final Task Sheet — Student Experience Hub: Anonymous Company Reviews, Application Tracker Timeline, Secure Document Vault & Faculty Analytics

> **Role:** Student Experience & Social Features Systems Engineer  
> **Priority:** 🔴 P0 — Student Placement Journey, Peer Intelligence & Faculty Decision Support  
> **Reference Standard:** Glassdoor Interview Insights, Internshala Progress Tracker, Google Drive Vault, PowerBI Academic Analytics  

---

## 📋 Industrial Context — Why This Final Submission Matters

In traditional university placement drives, students navigate the hiring season completely blind:
1. **Zero Pre-Interview Intelligence:** Candidates appear for recruitment rounds with no prior insight into the company's technical round structure, commonly asked DSA patterns, HR culture questions, or realistic stipend/CTC compensation breakdowns.
2. **Opaque Application Status:** Students submit applications and hear nothing for weeks. They have no idea if their resume was reviewed, if they passed the coding round, or when the next technical round is scheduled.
3. **Document Disarray:** Students repeatedly email PDFs of 10th/12th marksheets, semester grade cards, and identity cards to TPO coordinators, risking file leaks and document tampering.
4. **Faculty Blind Spots:** Department HODs and faculty advisors have no real-time dashboard to identify struggling, unplaced students who need academic intervention before the placement season closes.

---

## TASK 1: Anonymous Company Reviews & Peer Interview Intelligence Hub

### Backend Endpoints (`backend/app/api/v1/company_reviews.py`)
- `POST /companies/reviews`: Students anonymously submit verified interview experiences:
  - Company name, job role applied for, and academic year.
  - Overall rating (1–5 stars) and difficulty rating (1–5 stars).
  - Interview outcome (`"Selected"`, `"Rejected"`, `"Offer Declined"`).
  - Compensation details: Offered CTC (LPA) and monthly stipend (optional/anonymous).
  - Round-by-round breakdown:
    - Round 1: Online Assessment (Topics covered, duration, platform).
    - Round 2: Technical Interview 1 (DSA topics, system architecture questions).
    - Round 3: Technical Interview 2 / Managerial Round.
    - Round 4: HR / Culture Fit Round.
  - Question tags (`["Two Pointers", "Dynamic Programming", "SQL Joins", "REST API", "Pointers in C++"]`).
  - Advice to juniors / preparation recommendations.
- `GET /companies/reviews`: Filterable directory by company name, rating, and selection outcome.
  - Enforces `PaginatedResponse` schema with metadata: `page`, `page_size`, `total_items`, `total_pages`.
- `POST /companies/reviews/{id}/upvote`: Peer upvoting mechanism to surface the most detailed reviews.
- `GET /companies/insights`: Aggregates company metrics across all peer submissions:
  - Average interview difficulty index (1.0 to 5.0).
  - Selection rate percentage ($Selected / Total Reviews \times 100$).
  - Most frequently tested topic tags cloud.
  - Average reported salary package by role.
- `GET /companies/insights/{name}`: Drill-down company intelligence profile.

### Frontend Review Portal (`frontend/src/pages/student/CompanyReviews.jsx`)
- Glassdoor-style company cards displaying aggregate star ratings, average difficulty gauge, and total reviews.
- Anonymous review submission modal with star pickers, dynamic round adding, and confidentiality disclaimer.
- Search and filter bar for finding specific companies and roles.

---

## TASK 2: Application Tracker Timeline & Milestone State Machine

### Event-Driven Tracker API (`backend/app/api/v1/tracker_vault.py`)
- `GET /tracker/applications`: Lists all placement drives the authenticated student applied for:
  - Application ID, drive title, company name, role, current status, applied date, and last update timestamp.
- `GET /tracker/timeline/{app_id}`: Returns complete chronological event history for an application.
- **Milestone State Machine Transitions:**
  - `applied` (Student submitted application)
  - `shortlisted` (TPO / Recruiter approved initial eligibility)
  - `assessment_scheduled` (Online test credentials released)
  - `interview_scheduled` (Technical round time slot confirmed)
  - `in_progress` (Active interview stages ongoing)
  - `selected` / `offered` (Formal digital offer released)
  - `rejected` / `withdrawn`
- Every status transition creates an immutable `ApplicationTimelineEvent` record capturing:
  - `from_status` and `to_status`
  - `description` (e.g., "Shortlisted for Round 2 Technical Interview")
  - `actor_name` (TPO Officer or Recruiter name)
  - `metadata_payload` (e.g., meeting links, room numbers, test URLs)

### Frontend Timeline Stepper (`frontend/src/pages/student/Applications.jsx`)
- Dual-view interface: **Kanban Board** (Applied, Shortlisted, In-Progress, Selected) and **Detail Timeline View**.
- Interactive vertical timeline showing each milestone with green checkmarks, active pulsing indicators, and recruiter notes.
- Quick actions: "View Offer Details", "Join Virtual Interview", "Download Receipt".

---

## TASK 3: Secure Student Document Vault with TPO Sharing

### Encrypted Vault API (`backend/app/api/v1/tracker_vault.py`)
- `POST /vault/documents`: Student uploads academic documents:
  - Document categories: `marksheet_10th`, `marksheet_12th`, `semester_gradesheet`, `resume_pdf`, `id_proof`, `caste_certificate`.
  - Secure file validation: Validates file extensions (`.pdf`, `.png`, `.jpg`), enforces 10MB size ceiling, and computes SHA-256 checksum to prevent file corruption.
  - Stores document metadata with `is_verified` (default `False`).
- `GET /vault/documents`: Lists student's personal documents with verification badges.
- `GET /vault/documents/{id}`: Secure download stream with access control checks.
- `PATCH /vault/documents/{id}`: Edit document title or notes.
- `DELETE /vault/documents/{id}`: Deletes file from storage and removes database record.
- `PATCH /vault/documents/{id}/verify`: TPO/Admin privilege endpoint to formally verify document authenticity, locking the document from further modification.
- `GET /vault/shared`: TPO portal view to access all verified student documents for on-campus company drives.

### Frontend Document Vault UI (`frontend/src/pages/student/DocumentVault.jsx`)
- Grid of document folders categorized by type with preview thumbnails.
- Drag-and-drop file uploader with real-time upload progress bar and MIME type validation.
- Status badges: 🟡 "Pending Verification", 🟢 "Verified by TPO", 🔴 "Action Required".

---

## TASK 4: Faculty Department Placement & Curriculum Analytics Dashboard

### Department Analytics API (`backend/app/api/v1/faculty.py`)
- `GET /faculty/dashboard`: Comprehensive department placement summary:
  - Department placement percentage ($Placed / Eligible \times 100$).
  - Total eligible students, total job offers received, and dual-offer count.
  - Highest, Median, and Mean CTC (LPA) for the department.
  - Top recruiting companies ranked by student hire volume.
- `GET /faculty/students`: Paginated student roster for the department:
  - Filter by placement status (`"Placed"`, `"Unplaced"`, `"Opted Out"`), CGPA ranges, and active backlogs.
  - Flag **"At-Risk Students"**: Unplaced students with CGPA < 7.0 and skill readiness score < 50%, highlighting them for immediate faculty counseling.
- **Board of Studies (BoS) Integration:**
  - Direct bridge to BoS syllabus modernization proposals, allowing HODs and faculty to review industry skill gaps and vote on syllabus revisions.

### Faculty Dashboard UI (`frontend/src/pages/faculty/Dashboard.jsx`)
- Visual metric cards for Department Placement Rate, Average Package, and Active Recruiters.
- Student performance scatter plot (CGPA vs. Placement CTC).
- "At-Risk Students" alert table with direct "Assign Mentor" action button.
- Clean design strictly adhering to `src/index.css` without external UI framework dependencies.

---

## 🛠️ Verification Runbook & Commands

Execute in terminal to confirm complete system integrity:

```powershell
# 1. Verify all backend models, schemas, and endpoints
cd d:\Projects\p1\backend
.\.venv\Scripts\pytest.exe tests/ -k "tracker or vault or review or faculty" -v

# 2. Verify all 179 platform tests pass
.\.venv\Scripts\pytest.exe -q

# 3. Validate frontend production build
cd d:\Projects\p1\frontend
npm run build
```

---

## 🎓 Viva Defense Talking Points for External Examiners

1. **Anonymous Review Authenticity:** Explain how CCIP guarantees anonymity while preventing spam: reviews require an authenticated student token verifying they belong to the university, but the database separates the user identity from public display using anonymous hashes.
2. **Application State Machine Integrity:** Describe how the event-driven timeline model prevents invalid state transitions (e.g., a candidate cannot jump from `applied` to `selected` without passing intermediate assessment stages).
3. **Document Vault Security & Compliance:** Explain how document verification protects against fraudulent academic credentials during high-stakes corporate hiring rounds.

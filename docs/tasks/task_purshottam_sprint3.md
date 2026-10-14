# 🧑‍💻 Purushottam's Task Sheet (Sprint 3) — Full TPO Operations Command Centre: Bulk Shortlisting Engine, Calendar-Based Drive Scheduler, Offer Letter Pipeline & Recruiter CRM

> **Role:** TPO Workflow & Operations Engineer
> **Priority:** 🟠 P1 — Core TPO power-user features
> **Reference Standard:** iCIMS Recruit, Greenhouse ATS, Lever, Taleo Enterprise

---

## 📋 Industrial Context — Why This Sprint Matters

The TPO currently manages placement drives one student at a time. In a real placement season, a single drive gets 200+ applicants. Moving through them one by one is not viable. Industrial ATS (Applicant Tracking Systems) like Greenhouse and iCIMS have:

- **Bulk shortlisting with configurable criteria** (CGPA + skills + backlogs)
- **Visual drag-and-drop Kanban boards** to move candidates through stages
- **Calendar view** of all drives with conflict detection
- **Offer letter generation** from templates with digital signature fields
- **Recruiter portal** where company HR representatives can log in and view only their shortlisted candidates

None of these exist in CCIP. This sprint builds them all.

---

## TASK 1: Intelligent Bulk Shortlisting Engine

### Backend

#### CREATE: `backend/app/services/shortlisting_service.py`

This is the most complex service in this sprint. It applies configurable rules to filter applicants.

```python
class ShortlistingCriteria(BaseModel):
    min_cgpa: float | None             # e.g. 7.5
    max_backlogs: int | None           # e.g. 0
    required_skills: list[str]         # student must have ALL of these
    preferred_skills: list[str]        # bonus if student has these
    min_skill_match_pct: float | None  # e.g. 60.0 — must match 60% of drive's required skills
    eligible_departments: list[str]    # codes
    min_projects: int | None           # min portfolio projects
    has_resume: bool | None            # must have uploaded resume
    min_match_score: float | None      # ML match score threshold (uses matcher.py)

class ShortlistingService:
    async def run_auto_shortlist(self, drive_id: UUID, criteria: ShortlistingCriteria, tpo_user_id: UUID) -> dict:
        """
        1. Fetch all applications for drive with status="applied"
        2. For each applicant, load student profile (CGPA, skills, dept, projects, resume)
        3. Apply criteria filters:
           - CGPA check
           - Backlog check
           - Department eligibility check
           - Required skills check (all must match)
           - Skill match percentage check
           - Resume uploaded check
           - ML match score check (call predict_match_score from ml/matcher.py)
        4. Passed → update application.status = "shortlisted"
        5. Failed → keep as "applied" (do NOT reject automatically)
        6. Record reason for pass/fail per applicant in application.metadata JSONB
        7. Write SHORTLIST_GENERATED audit event with criteria + counts
        8. Publish notifications to shortlisted students (use NotificationService)
        9. Return: {total_evaluated, shortlisted, skipped, criteria_used, dry_run_result}
        """

    async def dry_run(self, drive_id: UUID, criteria: ShortlistingCriteria) -> dict:
        """
        Same logic as run_auto_shortlist but does NOT write to DB.
        Returns preview: who would be shortlisted and why.
        """

    async def manual_override(self, application_id: UUID, new_status: str, reason: str, tpo_user_id: UUID):
        """TPO can override automated decision for any individual application."""
```

#### MODIFY: `backend/app/api/v1/drives.py` — Add shortlisting routes

```
POST /drives/{drive_id}/shortlist/dry-run    → preview (no DB write)
POST /drives/{drive_id}/shortlist/execute    → run and persist
POST /drives/{drive_id}/applicants/{app_id}/override  → manual override with reason
GET  /drives/{drive_id}/shortlist/summary    → {shortlisted_N, rejected_N, pending_N, criteria_used}
```

### Frontend: `frontend/src/pages/tpo/DriveApplicantReviewer.jsx` — Enhance with Bulk Operations

**Current state:** Individual applicant cards. 

**Add:**

**Bulk Action Toolbar (appears when applicants are selected):**
- Checkbox select-all / deselect-all
- Bulk actions: "Shortlist Selected" / "Move to Next Round" / "Reject Selected" (with confirmation modal)
- Count badge: "47 selected"

**Auto-Shortlist Wizard (modal):**
Triggered by "⚡ Auto-Shortlist" button.

Step 1 — Configure Criteria:
- CGPA minimum slider (5.0–10.0, step 0.1)
- Max backlogs allowed (0, 1, 2, unlimited)
- Required skills multi-select (from drive's required skills list)
- Min skill match % slider (0–100%)
- Department filter (auto-populated from drive's eligible departments, can narrow)
- Min projects (0, 1, 2, 3+)
- Resume required toggle
- ML match score minimum slider (0–100)

Step 2 — Dry Run Preview:
- Shows: "Would shortlist N of M applicants"
- Table preview: top 20 who pass, with columns: Name, CGPA, Skill Match %, ML Score, Status
- Bottom N who fail: show why each failed (e.g. "CGPA 6.8 < 7.5" or "Missing: Python, DSA")

Step 3 — Execute:
- "Apply to N students" confirmation button
- Progress bar while processing
- Result: "Shortlisted 47. Notifications sent. 23 remain as Applied."

**Kanban View (new view mode toggle: List | Kanban):**
Drag-and-drop board with columns: Applied → Shortlisted → Technical Round → HR Round → Selected → Offer Released
- Each applicant is a card: name, dept, CGPA, match score
- Drag card between columns → updates application status
- Use `@dnd-kit/core` or `react-beautiful-dnd` library

---

## TASK 2: Drive Calendar & Conflict Manager

### Backend

#### CREATE: `backend/app/api/v1/calendar.py`

```
GET  /calendar/drives                 → all drives with date, company, status, conflict flags
GET  /calendar/drives/month           → drives for a specific month (query: year, month)
POST /calendar/drives/{id}/reschedule → update drive_date + registration_deadline + notify applicants
GET  /calendar/conflicts              → detect overlapping drives (same dept, same date range, conflicting deadlines)
```

Conflict detection logic:
```python
def detect_conflicts(drives: list[PlacementDrive]) -> list[dict]:
    # Two drives conflict if:
    # 1. They share at least one eligible department AND
    # 2. Their drive_date is within 2 days of each other
    # Return: [{drive_a, drive_b, conflict_type: "SAME_DAY" | "DEADLINE_OVERLAP", severity: "warning"|"critical"}]
```

### Frontend: `frontend/src/pages/tpo/DriveCalendar.jsx`

Route: `/tpo/calendar`

Full calendar page:

**Calendar View (month grid):**
- Standard month calendar grid
- Drives appear as colored pills on their drive_date
  - Color by status: upcoming=blue, open=green, in_progress=orange, completed=grey
  - Hover → tooltip: company name, role, N applicants
  - Click → side drawer with drive mini-summary + "View Drive" button

**Week View toggle:**
- 7-column week view with time slots (morning/afternoon)
- Drive events as blocks

**Conflict Alerts Panel (right sidebar):**
- List of detected conflicts
- Each: "⚠️ Amazon Drive and TCS Drive both target CS dept on Nov 15"
- Severity badge: Warning or Critical
- "Reschedule" quick-action button

**Reschedule Modal:**
- Date picker for new drive_date
- Date picker for new registration_deadline
- Preview: "This will notify N registered students"
- Confirm → API call → success toast

**Add to Drive from Calendar:**
- Click empty date → "Create Drive on this date" shortcut
- Opens existing drive creation modal pre-filled with that date

---

## TASK 3: Offer Letter Pipeline

### Backend

#### ADD to Application model (`backend/app/models/placement.py`):

```python
# Already have: offer_ctc_lpa, offer_designation, etc.
# ADD:
offer_letter_url: str | None              # path to uploaded PDF
offer_letter_uploaded_at: datetime | None
offer_letter_status: str default="pending"  # "pending" | "uploaded" | "accepted" | "declined"
offer_accepted_at: datetime | None
offer_declined_reason: str | None
offer_joining_confirmed: bool default=False
offer_joining_date_confirmed: date | None
```

#### CREATE: `backend/app/api/v1/offer_letters.py`

```
POST /offer-letters/{application_id}/upload      → TPO uploads PDF (multipart/form-data)
GET  /offer-letters/{application_id}/download    → student downloads their offer letter (JWT auth — only own)
POST /offer-letters/{application_id}/accept      → student accepts offer
POST /offer-letters/{application_id}/decline     → student declines with optional reason
GET  /offer-letters/tpo/pending                  → list all applications with status=selected but no letter uploaded
GET  /offer-letters/tpo/accepted                 → all accepted offers (for reporting)
PATCH /offer-letters/{application_id}/joining    → confirm joining date (student action)
```

File upload: save to `/uploads/offer_letters/{application_id}.pdf`, store path in DB.

#### CREATE: `backend/app/services/offer_service.py`

```python
class OfferService:
    async def upload_letter(self, application_id, file, tpo_id) -> str:
        # Validate: file must be PDF, max 5MB
        # Save to uploads/offer_letters/
        # Update application: offer_letter_url, offer_letter_uploaded_at, offer_letter_status="uploaded"
        # Publish OFFER_RECEIVED notification to student
        # Return download URL

    async def accept_offer(self, application_id, student_id) -> None:
        # Verify application.student_id == student_id
        # Update offer_letter_status = "accepted", offer_accepted_at = now()
        # Publish notification to TPO user

    async def decline_offer(self, application_id, student_id, reason) -> None:
        # Update status = "declined", offer_declined_reason = reason
        # Audit log OFFER_DECLINED

    async def generate_pending_summary(self, academic_year) -> dict:
        # Count selected applications with no offer letter vs with letter
        # Useful for TPO dashboard "Pending Actions" widget
```

### Frontend Changes

#### MODIFY: `frontend/src/pages/tpo/OfferModal.jsx`
Current state: basic offer recording. Enhance to:
- Add PDF upload section: drag-drop file upload, shows file name + size after selection
- Upload button → POST to `/offer-letters/{app_id}/upload`
- Progress bar during upload
- After upload: "✅ Offer letter uploaded. Student notified."

#### CREATE: `frontend/src/pages/tpo/OfferPipeline.jsx`

Route: `/tpo/offers`

Full offer management page:

**Summary row:** Selected N | Pending Upload N | Uploaded N | Accepted N | Declined N | Joining Confirmed N

**Tabs:**
- "Pending Upload" — list of selected students with no offer letter yet
  - Per row: student name, company, drive, CTC, days since selection
  - "Upload Offer Letter" button
- "Uploaded — Awaiting Student Response" — uploaded but not yet accepted/declined
  - Per row: upload date, time awaiting
  - "Send Reminder" button → publishes DRIVE_REMINDER notification
- "Accepted" — final accepted offers
  - Per row: accepted date, joining date (if confirmed)
  - Export to CSV button
- "Declined" — declined offers + reason

#### MODIFY: `frontend/src/pages/student/PlacementDrives.jsx` (or DriveDetail.jsx)
- In application detail: if offer_letter_url exists, show "📄 Download Offer Letter" button
- If offer_letter_status == "uploaded" and not yet accepted: show "✅ Accept Offer" and "❌ Decline" buttons
- Decline → modal with "Reason for declining" textarea (optional)
- Joining date confirmation: date picker input, "Confirm Joining Date" button

---

## TASK 4: Recruiter CRM Portal (Company HR Access)

### Backend

#### ADD to User model: `role = "recruiter"` (update CheckConstraint)

#### CREATE: `backend/app/api/v1/recruiter.py`

A recruiter is a company HR user. They can only see data for their own company's drives.

```
GET  /recruiter/drives                 → drives linked to recruiter's company_id
GET  /recruiter/drives/{id}/applicants → shortlisted + selected applicants for their drive
GET  /recruiter/applicants/{app_id}    → applicant profile (anonymized: no personal contact until TPO approves)
POST /recruiter/applicants/{app_id}/feedback → submit interview feedback per stage
GET  /recruiter/dashboard              → {active_drives, shortlisted_total, selected_total, pending_interviews}
```

Recruiter authentication: same JWT system, just `role="recruiter"` + `company_id` field on User.

#### ADD to User model:
```python
company_id: UUID | None  FK→companies.id   # set for recruiter users
```

#### MODIFY: `backend/app/api/v1/auth.py`
- `POST /auth/register` — allow role="recruiter" only if invited (simple: check invite_code matches RECRUITER_INVITE_CODE env var)

### Frontend: `frontend/src/pages/recruiter/RecruiterDashboard.jsx`

New portal at `/recruiter/*` with its own minimal layout.

**Dashboard:**
- Active drives count, shortlisted candidates, pending interview schedules
- Drive cards: company logo, drive title, N shortlisted / N selected

**Applicants View** (`/recruiter/drives/:driveId/applicants`):
- Table: student name, department, CGPA, skills match, stage, status
- Each row expand → student's skills list, education, projects (anonymized: no email/phone until TPO releases contact)
- "Submit Feedback" button per applicant → modal with:
  - Stage selector (Aptitude/Technical/HR)
  - Rating (1–5)
  - Comments textarea
  - Outcome: Pass / Fail / On Hold
- Feedback saved to InterviewStage table

---

## Verification Checklist

- [ ] Auto-shortlist dry run shows correct preview without changing DB
- [ ] Auto-shortlist execute → shortlisted count matches dry run, notifications sent
- [ ] Kanban board drag-and-drop updates application status via API
- [ ] Calendar month view shows drives as colored pills on correct dates
- [ ] Conflict alert shows when two drives target same dept on same day
- [ ] Offer letter PDF upload saves file and notifies student
- [ ] Student can download offer letter only for their own applications
- [ ] Student accept/decline offer works + TPO sees status update
- [ ] Recruiter login only sees drives for their company
- [ ] Recruiter feedback saves to InterviewStage table correctly

# 🧑‍💻 Purushottam's Task Sheet (Sprint 2) — Applicant Stage Workflow, Offer Letter Management & Drive Announcements

> **Role:** Placement Operations & Applicant Pipeline Lead
> **Priority:** 🟠 P1 — Core placement day-to-day TPO workflow
> **Reference Standard:** Superset Placement Management, HirePro ATS, CoCubes Drive Operations, iCIMS Campus Recruiting
> **Estimated Effort:** ~3–4 days

---

## 📋 Industrial Context — Why This Matters

Right now, the CCIP system has a critical gap in the core placement workflow: students apply, and then nothing happens. The TPO has no interface to:
1. Move candidates through interview rounds (OA → Tech 1 → Tech 2 → HR → Selected/Rejected)
2. Record formal offer letters with CTC details when companies select candidates
3. Communicate with students about last-minute schedule changes (venue shifts, document requirements)

In every real campus placement management system (Superset, HirePro, CoCubes), these three workflows are the backbone of the TPO's daily operations. Without them, CCIP is unusable in production.

---

## TASK 1: Interactive Drive Applicant Reviewer & Stage Transition Workflow

### The User Journey
TPO opens the Drives page → clicks "Review Applicants" on a drive card → a full-width drawer opens showing all applicants → TPO advances candidates through rounds, schedules interviews, adds feedback, rejects candidates → student's "My Applications" tab updates in real-time.

### Files to Create / Modify
- **MODIFY:** `backend/app/api/v1/drives.py` — add `PATCH /drives/{drive_id}/applications/{app_id}`
- **MODIFY:** `backend/app/services/drive_service.py` — add `update_application_stage()` method
- **MODIFY:** `backend/app/schemas/drive.py` — add `ApplicationStageUpdate` schema
- **CREATE:** `frontend/src/pages/tpo/DriveApplicantReviewer.jsx` — the drawer component
- **MODIFY:** `frontend/src/pages/tpo/Drives.jsx` — add "Review Applicants" button + embed drawer
- **MODIFY:** `frontend/src/api/endpoints.js` — add `placementApi.updateApplicationStage()`
- **MODIFY:** `frontend/src/pages/student/PlacementDrives.jsx` — display updated stage info from API

### Backend: `ApplicationStageUpdate` schema (add to `schemas/drive.py`)

```python
class ApplicationStageUpdate(BaseModel):
    status: Optional[Literal["applied", "shortlisted", "in_progress", "selected", "rejected", "withdrawn"]] = None
    current_stage: Optional[str] = None   # "OA", "Technical Interview 1", "Technical Interview 2", "HR", "Final"
    stage_status: Optional[Literal["scheduled", "passed", "failed"]] = None
    feedback: Optional[str] = None        # Internal TPO notes (not shown to student)
    scheduled_at: Optional[datetime] = None  # Interview scheduled datetime
    meeting_link: Optional[str] = None    # Virtual meeting URL
    venue: Optional[str] = None           # Physical venue if in-person
```

### Backend: `update_application_stage()` in `drive_service.py`

```python
async def update_application_stage(
    self,
    drive_id: uuid.UUID,
    application_id: uuid.UUID,
    update: ApplicationStageUpdate,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> Application:
    """
    1. Fetch the Application by (drive_id, application_id) — raise 404 if not found.
    2. Record the previous status for audit log.
    3. Apply all non-None fields from update to the Application ORM object.
    4. If update.status == 'selected': set student.placement_status = 'placed' on the related Student.
    5. Flush and return the updated Application.
    IMPORTANT: Do NOT commit here — the router handles the commit.
    """
```

### Backend Route (add to `drives.py`)

```python
@router.patch("/{drive_id}/applications/{application_id}")
async def update_application_stage(
    drive_id: uuid.UUID,
    application_id: uuid.UUID,
    update: ApplicationStageUpdate,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    TPO advances or updates an applicant's stage in a drive.
    Must call record_audit_event with event_type='APPLICATION_STATUS_CHANGE'.
    Must call create_notification() for the student if status changes.
    """
```

### Frontend: `DriveApplicantReviewer.jsx`

This is a FULL-WIDTH DRAWER (not a modal) that slides in from the right or bottom. It is embedded inside `Drives.jsx` and controlled by state `[reviewingDrive, setReviewingDrive]`.

**Trigger:** "📋 Review Applicants" button appears on each drive card in `Drives.jsx`.

**Drawer Architecture:**
```
┌──── Applicant Review: Amazon SDE Drive 2026 ──────────────────────────────────────── [✕] ─┐
│  Total: 47 Applied   |  12 Shortlisted  |  5 In Progress  |  2 Selected  |  8 Rejected     │
│                                                                                              │
│  Filters: [All Stages ▾] [Branch ▾] [CGPA ▾] [🔍 Search by name or roll no]               │
│──────────────────────────────────────────────────────────────────────────────────────────── │
│  Roll No     Name            Branch  CGPA   Status            Stage           Actions       │
│  R2024CS001  Riya Sharma     CS      8.7    Applied           —               [⏩ Actions]  │
│  R2024CS002  Arjun Mehta     CS      9.1    Shortlisted ●    OA Completed    [⏩ Actions]  │
│  R2024IT003  Priya Nair      IT      7.9    In Progress ●    Tech Round 1    [⏩ Actions]  │
│  R2024CS004  Karan Joshi     CS      8.2    Selected ✓       Final           [📝 Offer]    │
│  R2024ECE05  Ananya Singh    ECE     7.5    Rejected ✗       Tech Round 2    [—]           │
└──────────────────────────────────────────────────────────────────────────────────────────── ┘
```

**"Actions" dropdown per applicant (rendered as a popover menu):**
```
⏩ Advance to Next Stage  →  [Stage Dropdown: OA | Tech 1 | Tech 2 | HR | Final]
📅 Schedule Interview      →  Opens mini date/time picker + meeting link input
💬 Add Internal Feedback   →  Text area for TPO notes (not student-visible)
❌ Reject Candidate        →  Confirmation dialog with optional rejection note
📝 Record Offer            →  (Only visible when status is Selected) → Opens Offer Modal
```

**Stage Advance Flow:**
1. TPO clicks "Advance to Next Stage"
2. Inline popover shows stage dropdown + optional scheduled_at + meeting_link
3. TPO selects stage, optionally sets date/link, clicks "✓ Confirm"
4. Frontend calls `PATCH /drives/:driveId/applications/:appId` with the payload
5. Row updates in place with new status and stage (no full page reload)

**Stats Summary Bar:**
At the top of the drawer, show a live stats bar: "X Applied | Y Shortlisted | Z In Progress | W Selected | V Rejected". These numbers update whenever any action is taken.

---

## TASK 2: Offer Letter Recording & CTC Verification

### When This Is Triggered
When TPO changes an applicant's status to `"selected"`, a **"Record Official Offer"** modal automatically appears (or can be triggered via the "📝 Record Offer" action button).

### Files to Modify
- **MODIFY:** `backend/app/models/placement.py` — add offer fields to `Application` model
- **MODIFY:** `backend/app/schemas/drive.py` — add `OfferCreate` schema
- **MODIFY:** `backend/app/services/drive_service.py` — add `record_offer()` method
- **MODIFY:** `backend/app/api/v1/drives.py` — add `POST /drives/{id}/applications/{app_id}/offer`
- **CREATE:** `frontend/src/pages/tpo/OfferModal.jsx` — offer recording form
- **MODIFY:** `frontend/src/pages/tpo/DriveApplicantReviewer.jsx` — embed OfferModal
- **MODIFY:** `frontend/src/api/endpoints.js` — add `placementApi.recordOffer()`

### Backend: Add Offer Fields to `Application` model

Add these columns to the existing `Application` ORM model in `models/placement.py`:
```python
offer_ctc_lpa = Column(Float, nullable=True)         # Total CTC in LPA
offer_fixed_lpa = Column(Float, nullable=True)        # Fixed component
offer_variable_lpa = Column(Float, nullable=True)     # Variable component
offer_designation = Column(String(200), nullable=True) # e.g. "Associate Software Engineer"
offer_joining_date = Column(Date, nullable=True)
offer_reference_number = Column(String(100), nullable=True)
offer_recorded_at = Column(DateTime(timezone=True), nullable=True)
```

### Backend: `OfferCreate` schema

```python
class OfferCreate(BaseModel):
    offer_ctc_lpa: float = Field(..., gt=0, le=200, description="Total CTC in Lakhs Per Annum")
    offer_fixed_lpa: float = Field(..., gt=0)
    offer_variable_lpa: float = Field(default=0.0, ge=0)
    offer_designation: str = Field(..., min_length=3, max_length=200)
    offer_joining_date: Optional[date] = None
    offer_reference_number: Optional[str] = None

    @validator("offer_ctc_lpa")
    def ctc_must_match_components(cls, v, values):
        # Warn if fixed + variable don't roughly match total CTC (tolerance ±10%)
        ...
```

### Backend: API Route

```python
@router.post("/{drive_id}/applications/{application_id}/offer")
async def record_offer(
    drive_id: uuid.UUID,
    application_id: uuid.UUID,
    offer: OfferCreate,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Records an official offer for a selected candidate.
    1. Validates applicant status is 'selected'.
    2. Updates Application with offer fields.
    3. Updates Student.placement_status = 'placed'.
    4. Calls record_audit_event with event_type='OFFER_RECORDED'.
    5. Calls create_notification() for the student with the offer details.
    """
```

### Frontend: `OfferModal.jsx`

A rich glassmorphism modal with these fields:

```
┌──────────── Record Official Offer — Riya Sharma @ Amazon ──────────────────┐
│                                                                              │
│  Designation:    [ Associate Software Engineer                     ]         │
│  Total CTC:      [ 24        ] LPA    Fixed: [ 20  ] LPA  Variable: [ 4  ] LPA │
│  Joining Date:   [ 2027-07-01 📅 ]   Reference #: [ AMZ/2026/OFFER/423 ]   │
│                                                                              │
│  CTC Breakdown: ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░  Fixed 83% | Variable 17%              │
│                                                                              │
│  [Cancel]                              [✓ Confirm & Record Offer]            │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Behavior:**
- The CTC breakdown bar updates in real-time as the TPO types.
- Validation: total CTC must be > 0, designation must be non-empty.
- On submit: POST to `/drives/{driveId}/applications/{appId}/offer`.
- On success: close modal, update the applicant row to show CTC badge (e.g., "₹24 LPA ✓").

---

## TASK 3: Real-Time Drive Announcements & Broadcasts

### Files to Create / Modify
- **CREATE:** `backend/app/models/announcements.py` — `DriveAnnouncement` model
- **MODIFY:** `backend/app/models/__init__.py` — import
- **MODIFY:** `backend/app/api/v1/drives.py` — add 2 new sub-routes for announcements
- **MODIFY:** `frontend/src/pages/tpo/Drives.jsx` — add "Post Announcement" button per drive
- **MODIFY:** `frontend/src/pages/student/PlacementDrives.jsx` — show announcements banner on applied drives

### Backend: `models/announcements.py`

```python
class DriveAnnouncement(Base):
    __tablename__ = "drive_announcements"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    drive_id = Column(UUIDType, ForeignKey("placement_drives.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(UUIDType, ForeignKey("users.id"), nullable=False)
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    urgency = Column(Enum("normal", "important", "urgent", name="announcement_urgency"), default="normal")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Backend: Routes (add to `drives.py`)

```python
@router.post("/{drive_id}/announcements")
async def post_announcement(
    drive_id: uuid.UUID,
    data: AnnouncementCreate,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    TPO posts an announcement for a specific drive.
    After saving to DB, creates a Notification for all students who have applied to this drive.
    """

@router.get("/{drive_id}/announcements")
async def get_announcements(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns all announcements for a drive, newest first."""
```

### Frontend: TPO Drives Page — Post Announcement

On each drive card in `tpo/Drives.jsx`, add a **"📢 Post Announcement"** button. Clicking opens a small modal:

```
┌─────── Post Announcement — Amazon SDE Drive 2026 ──────────────────┐
│  Title:    [ Venue changed for Tech Round 2                        ] │
│  Message:  [ Interview venue has been shifted to CS Seminar Hall 2. │
│              All candidates must be seated by 9:30 AM with Aadhar  │
│              and Resume hard copies.                               ] │
│  Urgency:  ( ) Normal  (●) Important  ( ) Urgent 🔴                 │
│                                                                      │
│  [Cancel]               [📢 Post Announcement]                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Frontend: Student Drives Page — Announcement Banners

In `student/PlacementDrives.jsx`, on each drive in the "My Applications" tab that the student has applied to, add an **Announcements section** below the application status card:

```
📢 Announcements (2)
─────────────────────────────────────────────────────────────────────
  [!IMPORTANT] Venue changed for Tech Round 2        2 hours ago
  Interview venue shifted to CS Seminar Hall 2. Bring Aadhar + Resume.

  [NORMAL] OA Results Declared                       1 day ago
  Students who cleared OA: Check shortlisted candidates list.
```

**Urgency color coding:**
- `normal` → grey/muted left border
- `important` → yellow/amber left border + icon `⚠️`
- `urgent` → red left border + icon `🔴` + animated pulse on the border

**Loading behavior:** When expanding a drive's "My Applications" card, call `GET /drives/{id}/announcements` to fetch and display them. Cache the response for 5 minutes to avoid redundant API calls.

---

## Checklist — What "Done" Looks Like

- [ ] TPO can open a "Review Applicants" drawer for any drive showing all applicants in a sortable table
- [ ] TPO can advance a candidate through stages (OA → Tech 1 → Tech 2 → HR → Selected)
- [ ] TPO can schedule an interview with date, time, and meeting link; student sees updated schedule in My Applications
- [ ] TPO can reject a candidate with optional notes
- [ ] When a candidate is marked "Selected", a "Record Offer" modal appears with CTC fields
- [ ] Offer details (total CTC, fixed, variable, designation) are saved and reflected in placement statistics
- [ ] Student profile is automatically marked as "placed" when offer is recorded
- [ ] TPO can post drive announcements with urgency levels
- [ ] Students see announcements prominently on their applied drives with urgency color coding
- [ ] New announcement creates in-app notifications for all registered applicants

---

## File Touch Summary

| Action | File |
|--------|------|
| MODIFY | `backend/app/api/v1/drives.py` |
| MODIFY | `backend/app/services/drive_service.py` |
| MODIFY | `backend/app/schemas/drive.py` |
| CREATE | `frontend/src/pages/tpo/DriveApplicantReviewer.jsx` |
| MODIFY | `frontend/src/pages/tpo/Drives.jsx` |
| MODIFY | `backend/app/models/placement.py` |
| CREATE | `frontend/src/pages/tpo/OfferModal.jsx` |
| CREATE | `backend/app/models/announcements.py` |
| MODIFY | `frontend/src/pages/student/PlacementDrives.jsx` |
| MODIFY | `frontend/src/api/endpoints.js` |

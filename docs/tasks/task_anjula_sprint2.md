# 🧑‍💻 Anjula's Task Sheet (Sprint 2) — Drive Detail Page, Interview Experience Hub & Notification Bell

> **Role:** Placement Logistics & Campus Community Lead
> **Priority:** 🟠 P1 — Core Student Placement Experience & Campus Communication
> **Reference Standard:** LeetCode Discuss, Glassdoor College Hub, Superset Drive Detail, LinkedIn Job Page
> **Estimated Effort:** ~3–4 days

---

## 📋 Industrial Context — Why This Matters

Right now, clicking any drive card on the student placement page shows NO detail. The student must apply blindly without knowing interview rounds, dress code, or eligibility clarification. In real campus placement software:

1. **Every drive has a rich detail page** showing the company's full profile, round-by-round interview schedule, venue/meeting links, required documents, and the student's exact eligibility status with a clear Apply CTA.
2. **Interview experiences from seniors are institutional knowledge.** Real portals (LeetCode Discuss, Superset) let placed students share their exact interview questions, difficulty, and tips so juniors prepare for the same companies next year.
3. **Students miss critical deadlines** because notifications only appear inside specific pages. A top-bar notification bell is a standard on every commercial campus portal (Handshake, Internshala, Superset).

---

## TASK 1: Full Drive Detail Page with Multi-Round Interview Logistics

### The User Journey
Student clicks a drive card on `/student/drives` → navigates to `/student/drives/:driveId` → sees a complete company + logistics page → clicks "Apply Now" if eligible.

### Files to Create / Modify
- **CREATE:** `frontend/src/pages/student/DriveDetail.jsx`
- **CREATE:** `frontend/src/pages/tpo/DriveDetail.jsx` (or reuse with role detection)
- **MODIFY:** `frontend/src/router/AppRouter.jsx` — add routes `/student/drives/:id` and `/tpo/drives/:id`
- **MODIFY:** `frontend/src/pages/student/PlacementDrives.jsx` — make drive cards clickable (add `<Link>` wrapper or `onClick` → navigate)
- **MODIFY:** `frontend/src/pages/tpo/Drives.jsx` — same, add "View Details" link
- **MODIFY:** `frontend/src/api/endpoints.js` — `placementApi.getDrive(id)` is already defined, ensure it works

### `DriveDetail.jsx` — Full Component Layout

The page must have these exact sections:

**Section 1: Company Hero Header**
```
┌──────────────────────────────────────────────────────────────────────┐
│ [← Back to Drives]                                                    │
│                                                                       │
│  🏢 Amazon                          [OPEN]  12 days left             │
│  Technology · Seattle, WA            🌐 amazon.jobs                  │
│  "Earth's most customer-centric company..."                          │
│                                                                       │
│  ₹24 LPA Fixed + ₹4 LPA Variable    Roles: SDE-I, SDE-II           │
│  Bond: None   Probation: 6 months                                    │
└──────────────────────────────────────────────────────────────────────┘
```

**Section 2: Interview Round Timeline**

Display each round as a vertical timeline. Rounds should come from `drive.rounds` array if present in API response, otherwise use a hardcoded template based on company_industry.

```
Round 1: Online Assessment
  Platform: HackerRank  |  Duration: 90 mins  |  Date: Oct 5, 2026
  Topics: DSA (Arrays, DP, Graphs), Aptitude

Round 2: Technical Interview I
  Format: Video Call  |  Link: [Join Google Meet]  |  Date: Oct 12, 2026
  Required docs: Resume, Aadhar copy

Round 3: Technical Interview II
  Format: In-Person  |  Venue: CS Seminar Hall 2

Round 4: HR Interview
  Format: Video Call  |  Duration: 45 mins
```

Each round card has:
- Round number badge (colored: 1=blue, 2=purple, 3=orange, 4=green)
- Platform / venue detail
- Date and time (formatted as "October 12, 2026 at 2:30 PM")
- A clickable meeting link button if `meeting_link` is provided

**Section 3: Eligibility Status Box**

```
┌─────────────────── Your Eligibility Status ─────────────────────────┐
│                                                                       │
│  ✅ CGPA: 8.4 ≥ 7.5 required                                        │
│  ✅ Branch: CS — Eligible (CS, IT, ECE allowed)                      │
│  ✅ Backlogs: 0 ≤ 0 allowed                                          │
│                                                                       │
│  [🚀 Apply Now — Registration Deadline: Oct 3, 2026]                 │
│  or  [✓ Application Submitted — View Status]  (if already applied)   │
└──────────────────────────────────────────────────────────────────────┘
```

Eligibility logic (reuse the `checkEligibility()` function from `PlacementDrives.jsx`):
- If ineligible, show the specific reason and grey out the Apply button.
- If already applied, show "Application Submitted" with the current status badge.

**Section 4: TPO Attendance Sheet Download (TPO view only)**

At the bottom of the page, when the logged-in user is a TPO:
- Show a "📋 Download Attendance Roster (CSV)" button.
- This calls `placementApi.shortlistStudents(driveId)` and exports the result as CSV.
- The CSV columns: Roll Number, Name, Branch, CGPA, Email, Phone, Application Date.

### API Data Handling

The `placementApi.getDrive(id)` endpoint hits `GET /api/v1/drives/:id`. If that response does not yet include a `rounds` array, render a generic 4-round template:
```javascript
const DEFAULT_ROUNDS = [
  { round: 1, name: "Online Assessment", format: "Online", platform: "HackerRank" },
  { round: 2, name: "Technical Interview I", format: "Video Call" },
  { round: 3, name: "Technical Interview II", format: "In-Person / Video Call" },
  { round: 4, name: "HR Interview", format: "Video Call" },
];
```

---

## TASK 2: Student Company Interview Experience Hub

### What It Is
A page where:
- **Placed/interviewd students** submit their interview experience for a company (questions asked, difficulty, verdict, tips)
- **All students** browse these experiences searchable by company, role, or difficulty

### Files to Create / Modify
- **CREATE:** `backend/app/models/experiences.py` — `InterviewExperience` ORM model
- **MODIFY:** `backend/app/models/__init__.py` — import new model
- **CREATE:** `backend/app/api/v1/experiences.py` — 3 endpoints
- **MODIFY:** `backend/app/main.py` — register new router
- **CREATE:** `frontend/src/pages/student/InterviewExperiences.jsx`
- **MODIFY:** `frontend/src/router/AppRouter.jsx` — add route `/student/experiences`
- **MODIFY:** `frontend/src/components/AppSidebar.jsx` — add "Interview Experiences" nav item
- **MODIFY:** `frontend/src/api/endpoints.js` — add `experiencesApi`

### Backend: `models/experiences.py`

```python
class InterviewExperience(Base):
    __tablename__ = "interview_experiences"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id = Column(UUIDType, ForeignKey("students.id"), nullable=False)
    company_name = Column(String(200), nullable=False, index=True)
    role = Column(String(200), nullable=False)
    placement_drive_id = Column(UUIDType, ForeignKey("placement_drives.id"), nullable=True)
    difficulty = Column(Enum("Easy", "Medium", "Hard", name="experience_difficulty"), nullable=False)
    verdict = Column(Enum("Selected", "Rejected", "In Progress", name="experience_verdict"), nullable=False)
    overall_experience = Column(Text, nullable=False)   # narrative description, min 100 chars
    questions_asked = Column(ARRAY, nullable=True)       # list of strings (use JSONB compat field)
    tips_for_juniors = Column(Text, nullable=True)
    upvotes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", lazy="selectin")
    drive = relationship("PlacementDrive", lazy="selectin")
```

### Backend: `api/v1/experiences.py`

```python
router = APIRouter(prefix="/experiences", tags=["Interview Experiences"])

@router.get("")
async def list_experiences(
    company: Optional[str] = None,    # partial match search
    role: Optional[str] = None,
    difficulty: Optional[str] = None, # Easy | Medium | Hard
    verdict: Optional[str] = None,    # Selected | Rejected | In Progress
    page: int = 1,
    page_size: int = 12,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint - any authenticated user can browse experiences.
    Returns list of experiences with student first name (last name hidden for privacy).
    Sorted by created_at DESC.
    """

@router.post("")
async def submit_experience(
    data: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Student submits their interview experience.
    Rate-limited: max 3 submissions per student per company.
    """

@router.post("/{experience_id}/upvote")
async def upvote_experience(
    experience_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Increments upvote count. Idempotent per user (each user can only upvote once)."""
```

### Frontend: `InterviewExperiences.jsx` — Full Page Layout

**Top Bar:**
- Page title: "💡 Interview Experiences & Question Bank"
- Subtitle: "Real experiences from your seniors. Learn what to expect."
- Filter row: Company search input | Difficulty dropdown | Verdict dropdown
- "+ Share Your Experience" button (opens submission modal, only if current user has applied to any drive)

**Experience Card Grid (3 columns on desktop, 1 on mobile):**

```
┌─────────────────────────────────────────────────────────┐
│  🏢 Amazon                   [Hard] [🎉 Selected]        │
│  SDE-I                       ⬆ 47 upvotes               │
│  Batch 2026 · CS Dept · 3 months ago                    │
│                                                          │
│  "The OA had 3 coding questions (DP, Graph BFS, String  │
│   manipulation). All medium-hard difficulty on Hacker..." │
│                                                          │
│  Questions Asked:                                        │
│  • "Design a URL shortener (LLD)"                        │
│  • "Implement LRU Cache from scratch"                    │
│  • "Explain your most complex project"                   │
│                                                          │
│  Tips: "Focus on system design — they asked about        │
│  scalability at every round. Practice blind 75 + STAR..." │
│                                                          │
│  [Read Full Experience ▼]   [⬆ Helpful (47)]            │
└─────────────────────────────────────────────────────────┘
```

**Submit Experience Modal:**
- Fields: Company Name (or select from Drive dropdown), Role, Difficulty, Verdict, Overall Experience (textarea, 100 char min), Questions Asked (dynamic add-row input), Tips for Juniors.
- Character counter on the Overall Experience textarea.
- Validation: all required fields highlighted on submit.

**Mock Data for Development (`frontend/public/mocks/experiences.json`):**
Create a file with at least 6 realistic mock experiences for companies: Amazon, Google, TCS, Infosys, Deloitte, Wipro.

---

## TASK 3: Global In-App Notification Center (Bell Dropdown)

### Files to Create / Modify
- **CREATE:** `backend/app/models/notifications.py` — `Notification` ORM model
- **MODIFY:** `backend/app/models/__init__.py` — import
- **CREATE:** `backend/app/api/v1/notifications.py` — 3 endpoints
- **MODIFY:** `backend/app/main.py` — register router
- **CREATE/MODIFY:** `frontend/src/components/NotificationBell.jsx` — full component
- **MODIFY:** `frontend/src/layouts/StudentLayout.jsx` — embed NotificationBell in top bar
- **MODIFY:** `frontend/src/layouts/TPOLayout.jsx` — same
- **MODIFY:** `frontend/src/api/endpoints.js` — add `notificationsApi`

### Backend: `models/notifications.py`

```python
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    recipient_id = Column(UUIDType, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    # Types: "APPLICATION_SHORTLISTED", "APPLICATION_SELECTED", "APPLICATION_REJECTED",
    #        "NEW_DRIVE_POSTED", "DRIVE_DEADLINE_WARNING", "INTERVIEW_SCHEDULED"
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(500), nullable=True)   # Frontend route to navigate to on click
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
```

### Backend: `api/v1/notifications.py`

```python
router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/mine")
async def get_my_notifications(
    unread_only: bool = False,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns most recent notifications for current user, newest first.
    Also returns: { "items": [...], "unread_count": int }
    """

@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marks a single notification as read."""

@router.patch("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marks ALL unread notifications for current user as read."""
```

**Notification Trigger Points (where to call `create_notification()`):**
- In `drives.py` `POST /drives` → create "NEW_DRIVE_POSTED" notification for ALL eligible students
- In `applications.py` or `drives.py` when status changes to `shortlisted` → "APPLICATION_SHORTLISTED" to student
- When status changes to `selected` → "APPLICATION_SELECTED" to student
- When status changes to `rejected` → "APPLICATION_REJECTED" to student
- A background Celery task should check drives whose `registration_deadline` is 24 hours away and send "DRIVE_DEADLINE_WARNING" to registered-but-not-applied eligible students

Create a helper `async def create_notification(db, recipient_id, type, title, message, link=None)` in `notifications.py`.

### Frontend: `NotificationBell.jsx`

**Bell button in top bar:**
- A 🔔 icon button in the layout header (top-right corner of StudentLayout and TPOLayout)
- Shows a red badge with unread count (e.g., `3`) if unread > 0. If ≥ 10, show `9+`.
- Polls every 60 seconds OR on page focus for new notifications (use `useEffect` + `setInterval`)

**Dropdown panel (opens on bell click):**
```
┌────────────────── Notifications ──────────────── [Mark all read] ┐
│                                                                    │
│ 🔵 [unread] APPLICATION_SHORTLISTED        2 hours ago            │
│   "Your application for Amazon SDE-I has been Shortlisted!"       │
│   → /student/drives                                               │
│                                                                    │
│ 🔵 [unread] NEW_DRIVE_POSTED               5 hours ago            │
│   "Google SWE 2026 Campus Drive is now open. Apply before Oct 5." │
│   → /student/drives                                               │
│                                                                    │
│ ○  [read] DRIVE_DEADLINE_WARNING           1 day ago              │
│   "TCS Digital Drive closes in 24 hours. Don't miss out!"         │
│                                                                    │
│                          [View All Notifications]                 │
└────────────────────────────────────────────────────────────────────┘
```

**Dropdown behavior rules:**
- Max 5 notifications in dropdown. "View All" can go to a `/student/notifications` page (stretch goal).
- Clicking a notification marks it as read (call `PATCH /notifications/{id}/read`) AND navigates to `notification.link`.
- "Mark all read" calls `PATCH /notifications/read-all`.
- Unread notifications have a blue-tinted background and bold text.
- Read notifications are normal background, slightly muted text.
- Panel closes when clicking outside (use a `useClickOutside` hook or `useRef` + `document.addEventListener`).
- Smooth CSS transition for open/close (max-height animation or fade + slide down).

**Mock Data:** Create `frontend/public/mocks/notifications.json` with 5 sample notifications (mix of read and unread).

---

## Checklist — What "Done" Looks Like

- [ ] Clicking any drive card navigates to a detail page with company profile, round-by-round timeline, and eligibility box
- [ ] Apply Now button on detail page submits application correctly
- [ ] TPO view of drive detail shows "Download Attendance Roster (CSV)" button
- [ ] Students can browse company interview experiences searchable by company / difficulty / verdict
- [ ] Students who were interviewed can submit their own experience with questions and tips
- [ ] Notification bell in header shows unread count badge
- [ ] Bell dropdown shows last 5 notifications with correct styling for read/unread state
- [ ] Clicking a notification marks it read and navigates to the relevant page
- [ ] "Mark all read" clears the badge counter

---

## File Touch Summary

| Action | File |
|--------|------|
| CREATE | `frontend/src/pages/student/DriveDetail.jsx` |
| CREATE | `frontend/src/pages/tpo/DriveDetail.jsx` |
| MODIFY | `frontend/src/router/AppRouter.jsx` |
| MODIFY | `frontend/src/pages/student/PlacementDrives.jsx` |
| MODIFY | `frontend/src/pages/tpo/Drives.jsx` |
| CREATE | `backend/app/models/experiences.py` |
| CREATE | `backend/app/api/v1/experiences.py` |
| CREATE | `frontend/src/pages/student/InterviewExperiences.jsx` |
| MODIFY | `frontend/src/components/AppSidebar.jsx` |
| CREATE | `backend/app/models/notifications.py` |
| CREATE | `backend/app/api/v1/notifications.py` |
| CREATE | `frontend/src/components/NotificationBell.jsx` |
| MODIFY | `frontend/src/layouts/StudentLayout.jsx` |
| MODIFY | `frontend/src/layouts/TPOLayout.jsx` |
| MODIFY | `frontend/src/api/endpoints.js` |
| CREATE | `frontend/public/mocks/experiences.json` |
| CREATE | `frontend/public/mocks/notifications.json` |

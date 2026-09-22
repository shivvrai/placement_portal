# 🧑‍💻 Anjula's Task Sheet (Sprint 3) — Student Experience Hub: Interview War Room, Company Intelligence, Placement Journey Timeline & Peer Networking

> **Role:** Student Experience & Social Features Engineer
> **Priority:** 🟠 P1 — Highest-impact student-facing features
> **Reference Standard:** Glassdoor Interview Insights, LinkedIn Company Pages, Internshala Progress Tracker

---

## 📋 Industrial Context — Why This Sprint Matters

Right now a student on CCIP knows almost nothing about a company before applying. They have no idea what the interview process looks like, what questions were asked in previous batches, what the culture is, or what other students scored on assessments. Industrial platforms like Glassdoor, AmbitionBox, and LinkedIn give candidates this intelligence — CCIP must too.

Three major gaps this sprint closes:

1. **Company Intelligence Gap:** Students apply blind. There's no company profile page with employee count, funding stage, office locations, past hiring patterns, or Glassdoor-style ratings.
2. **Interview Preparation Gap:** The interview experience hub from Sprint 2 shows experiences but has no structure — no round-wise breakdown, no question tagging, no difficulty rating, no upvote system.
3. **Placement Journey Gap:** A student has no visual timeline of where they stand across all their applications. Every application is an isolated card with no narrative.

---

## TASK 1: Full Company Intelligence Page

### Backend Files

#### MODIFY: `backend/app/models/industry.py`
Add fields to the `Company` model:

```python
class Company(Base):
    # existing: id, name, industry, location
    # ADD:
    website: str | None
    linkedin_url: str | None
    description: str | None            # company overview, 500 chars
    employee_count_range: str | None   # "50-200", "200-500", "500-2000", "2000+"
    founded_year: int | None
    funding_stage: str | None          # "Bootstrapped", "Seed", "Series A/B/C", "Public", "MNC"
    hq_city: str | None
    logo_url: str | None               # stored in /uploads/company_logos/
    glassdoor_rating: float | None     # 1.0–5.0
    avg_interview_difficulty: float | None  # 1.0–5.0 computed from experiences
    total_hires_from_campus: int default=0   # computed
    tags: ARRAY(String)                # ["Product", "Top Payer", "Fast Growth", "Remote Friendly"]
```

#### CREATE: `backend/app/api/v1/companies.py`

```
GET  /companies                        → list all companies (paginated, search, filter by industry/tag)
GET  /companies/{id}                   → full company profile
GET  /companies/{id}/drives            → placement drives from this company (all years)
GET  /companies/{id}/interview-stats   → avg rounds, difficulty, selection rate, common question tags
GET  /companies/{id}/placement-history → year-wise: offers, avg CTC, departments hired from
PATCH /companies/{id}                  → TPO can update company info (logo upload via multipart)
```

#### CREATE: `backend/app/services/company_intelligence_service.py`

```python
class CompanyIntelligenceService:
    async def get_interview_stats(self, company_id) -> dict:
        # Query InterviewExperience table filtered to this company
        # Compute: avg_rounds, avg_difficulty, selection_rate, top_question_tags
        # Return structured dict

    async def get_placement_history(self, company_id) -> list[dict]:
        # Group PlacementOutcomes by academic_year
        # Return [{year, offers, avg_ctc, median_ctc, departments: []}]

    async def compute_avg_difficulty(self, company_id) -> float:
        # Average of all InterviewExperience.difficulty_rating for this company
```

### Frontend Files

#### CREATE: `frontend/src/pages/student/CompanyProfile.jsx`

Route: `/student/companies/:companyId`

Full company intelligence page with sections:

**Hero Section:**
- Company logo (or generated initials avatar if no logo)
- Company name, industry badge, funding stage badge, founded year
- Location chips (HQ city + "N offices")
- Glassdoor rating stars (if available)
- Website + LinkedIn external links
- "View Open Drives" button (scrolls to drives section)

**About Section:**
- Company description
- Employee count range
- Tags: clickable filter chips

**Placement Intelligence Section (most important):**
- Year-wise placement history table: AY | Offers | Avg CTC | Median CTC | Depts
- Interview stats: Avg rounds, Avg difficulty (star rating), Selection rate gauge
- Most asked question tags: horizontal tag cloud with frequency counts

**Interview Experiences Section:**
- Latest 5 interview experiences from this company
- Each card: role, batch year, result badge (Selected/Rejected), difficulty stars, short excerpt
- "View all experiences →" link to filtered InterviewExperiences page

**Open Drives Section:**
- Cards for all currently open/upcoming drives from this company
- "Apply Now" button on each if eligible

#### CREATE: `frontend/src/pages/student/Companies.jsx`

Route: `/student/companies`

Company discovery page:
- Search bar (by name)
- Filter sidebar: Industry, Funding Stage, Employee Size, Tags, Min Glassdoor Rating
- Grid of company cards: logo, name, industry, top tags, "N drives | Avg ₹XL" stats
- Sort: Most Hires, Highest CTC, Most Interviews, A-Z

---

## TASK 2: Structured Interview Experience Hub (Full Rebuild)

The existing `InterviewExperiences.jsx` is basic. Rebuild it properly.

### Backend Changes

#### MODIFY: `backend/app/models/` — add `InterviewExperience` model if not exists

```python
class InterviewExperience(Base):
    __tablename__ = "interview_experiences"
    id: UUID PK
    student_id: UUID FK→students.id
    company_id: UUID FK→companies.id  (nullable for non-campus)
    role: str(200)
    batch_year: str(10)            # "2025-26"
    result: str                    # "selected" | "rejected" | "on_hold"
    overall_difficulty: float      # 1.0–5.0
    offer_ctc: float | None
    rounds: JSONB                  # list of round objects (see below)
    question_tags: ARRAY(String)   # ["DSA", "System Design", "SQL", "HR", "Case Study"]
    written_review: str | None     # full narrative (max 5000 chars)
    tips: str | None               # "Tips for future applicants" (500 chars)
    is_anonymous: bool default=False
    upvotes: int default=0
    created_at: datetime
    # rounds JSONB structure:
    # [{"round_name": "Aptitude", "mode": "Online", "duration_min": 60,
    #   "questions": ["Q1 text", "Q2 text"], "outcome": "passed", "tips": "..."}]
```

#### MODIFY: `backend/app/api/v1/experiences.py`

Add/fix endpoints:
```
GET  /experiences                     → paginated list (filters: company_id, role, result, year, tags)
POST /experiences                     → student submits experience (with rounds array)
GET  /experiences/{id}                → full experience detail
PATCH /experiences/{id}               → student edits own experience
DELETE /experiences/{id}              → student deletes own
POST /experiences/{id}/upvote         → toggle upvote (only once per user)
GET  /experiences/company/{company_id}→ all experiences for a company (used by company profile)
GET  /experiences/tags/trending       → top 20 tags by frequency in last 3 months
```

### Frontend: Complete Rebuild of `frontend/src/pages/student/InterviewExperiences.jsx`

**Browse Mode (list view):**
- Search by company name or role
- Filter panel: Company, Role keywords, Result, Year, Difficulty range, Tags (multi-select checkboxes)
- Sort: Most Upvoted, Most Recent, Hardest, Easiest
- Experience cards: company logo + name, role, batch year, result badge (green/red/orange), difficulty stars, tag chips, excerpt of written review, upvote button with count, "Read more →"
- Trending tags widget (top 8 tags with pill counts)

**Detail Mode (single experience drawer/modal):**
- Slide-in right drawer (no page navigation)
- Company + role header
- Result badge + CTC (if selected)
- Difficulty rating (star display)
- **Round-by-round breakdown** (the key differentiator):
  - Each round: numbered card, round name, mode (Online/F2F/Phone), duration, questions asked (bullet list), outcome badge, round-specific tips
- Written narrative section
- General tips for future applicants
- Upvote button
- "Report" link

**Submit Experience Form (full modal or page `/student/experiences/submit`):**
- Company selector (autocomplete against companies list)
- Role input, batch year dropdown, result radio buttons
- CTC field (only shown if result = selected)
- Overall difficulty slider (1–5 with emoji labels: 1=Very Easy → 5=Very Hard)
- **Dynamic rounds builder:**
  - "Add Round" button → opens round form card
  - Round name dropdown (Aptitude/Coding/Technical/HR/Case Study/Group Discussion/Manager/Custom)
  - Mode dropdown (Online/F2F/Phone/Video Call)
  - Duration (minutes, numeric)
  - Questions: dynamic textarea list (add/remove question)
  - Outcome (Passed/Failed/On Hold)
  - Round tips textarea
  - Reorder rounds by drag handle
- Tags multi-select (pre-defined taxonomy + custom)
- Written review (rich text area, 5000 char limit with counter)
- Tips section (500 char)
- Anonymous toggle
- Preview → Submit

---

## TASK 3: Application Journey Timeline

### Backend

#### CREATE: `backend/app/api/v1/journey.py`

```
GET /journey/my                    → full placement journey for current student
```

Returns a structured response:
```json
{
  "student": {...},
  "summary": {"total_applied": 5, "shortlisted": 2, "selected": 1, "rejected": 2},
  "timeline": [
    {
      "drive_id": "...",
      "company": "Amazon",
      "role": "SDE-I",
      "applied_at": "2026-10-01",
      "status": "selected",
      "offer_ctc": 24.0,
      "stages": [
        {"stage": "Aptitude", "status": "passed", "date": "2026-10-05"},
        {"stage": "Technical Round 1", "status": "passed", "date": "2026-10-10"},
        {"stage": "HR", "status": "passed", "date": "2026-10-15"},
        {"stage": "Offer", "status": "completed", "date": "2026-10-18"}
      ]
    }
  ]
}
```

### Frontend: `frontend/src/pages/student/PlacementJourney.jsx`

Route: `/student/journey`

Visual placement journey page:

**Header:**
- "My Placement Journey" title
- Summary row: N Applied | N Shortlisted | N Offers | Best Package ₹XL
- Academic year badge

**Journey Timeline (main section):**
- Vertical timeline, one entry per application
- Each entry:
  - Left: Date of application
  - Center: Status circle (color: grey=applied, yellow=shortlisted, blue=in_progress, green=selected, red=rejected)
  - Right: Card with company logo + name, role, salary (if offer received)
  - Expand card → shows interview stages as a horizontal pipeline:
    `[Aptitude ✓] → [Technical ✓] → [HR ✓] → [Offer 🎉]`
    Each stage: green=passed, red=failed, grey=pending, blue=scheduled
  - If selected: "Offer Letter" download button (if uploaded by TPO)
  - If rejected: soft message + "View similar drives →" link

**Sidebar:**
- Application stats doughnut (Applied/Shortlisted/Selected/Rejected)
- "Companies I've Applied To" logo strip
- Next action items: "2 drives open — apply before deadline"

---

## TASK 4: Peer Network & Study Groups (Micro Social Feature)

### Backend

#### CREATE: `backend/app/models/social.py`

```python
class StudyGroup(Base):
    __tablename__ = "study_groups"
    id: UUID PK
    name: str(200)
    description: str | None
    created_by: UUID FK→students.id
    department: str | None
    tags: ARRAY(String)   # ["DSA", "System Design", "Aptitude"]
    max_members: int default=20
    is_open: bool default=True
    created_at: datetime

class StudyGroupMember(Base):
    __tablename__ = "study_group_members"
    group_id: UUID FK→study_groups.id
    student_id: UUID FK→students.id
    role: str default="member"  # "admin" | "member"
    joined_at: datetime
    PK: (group_id, student_id)
```

#### CREATE: `backend/app/api/v1/social.py`

```
GET  /social/groups                    → list groups (filter by dept, tags, open)
POST /social/groups                    → create group
GET  /social/groups/{id}               → group detail + members list
POST /social/groups/{id}/join          → join group
DELETE /social/groups/{id}/leave       → leave group
GET  /social/groups/my                 → groups I'm in
POST /social/groups/{id}/announce      → post a text announcement (text only, no chat)
GET  /social/groups/{id}/announcements → list announcements (paginated, newest first)
```

### Frontend: `frontend/src/pages/student/StudyGroups.jsx`

Route: `/student/study-groups`

**Browse Groups:**
- Grid of group cards: name, description, department badge, tag chips, member count / max, "Open" or "Full" badge
- Filters: Department, Tags, Open Only
- "Create Group" button

**Create Group Modal:**
- Name, Description, Max members (5–50), Tags (multi-select), Open/Invite-only toggle
- Submit → creates group + auto-joins creator as admin

**Group Detail Page** (`/student/study-groups/:groupId`):
- Group header: name, description, tags, member count
- Member list: avatars with names, role badges (Admin/Member), CGPA shown
- Announcements feed: text posts, posted_by, time-ago, no reactions (keep it simple)
- "Post Announcement" button (only for admin)
- Join/Leave button

---

## Verification Checklist

- [ ] Company profile page loads with all sections (hero, stats, history, experiences, open drives)
- [ ] Interview experience form successfully saves rounds as JSONB and renders round-by-round in drawer
- [ ] Upvoting an experience increments count without page reload
- [ ] Journey timeline shows correct stage pipeline for each application
- [ ] Offer letter download works when TPO has uploaded one
- [ ] Study group create + join + leave + announce all work correctly
- [ ] Company list page search + filters work (no page reload, query params update URL)
- [ ] Anonymous experience does not show student name or avatar

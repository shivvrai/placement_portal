# 🧑‍💻 Sakshi's Task Sheet (Sprint 2) — Verified Student Portfolio CRUD, Resume Skill Confirmation & Public Portfolio Page

> **Role:** Student Profile & Verified Credentials Lead
> **Priority:** 🟠 P1 — Core student portfolio and hiring showcase
> **Reference Standard:** Handshake Student Portfolio, LinkedIn Verified Education, Superset Resume Parser, GitHub Portfolio
> **Estimated Effort:** ~3–4 days

---

## 📋 Industrial Context — Why This Matters

CCIP's student profile (`Profile.jsx`) is currently a beautiful read-only display. In real hiring ecosystems, a student profile is a **living, verifiable digital portfolio** evaluated by Fortune 500 recruiters:

1. **Projects, Certifications, and Experience are static shell:** The DB has `Project`, `Certification`, and `WorkExperience` tables (in `backend/app/models/portfolio.py`) fully defined, but the frontend profile page has no forms to add, edit, or delete records. Students cannot showcase their work.
2. **Resume parsing has no human-in-the-loop:** The NLP engine extracts skills from an uploaded resume, but students have no chance to review or correct the extraction before it permanently modifies their skill profile. A false positive (extracting "Java" from the phrase "in JavaScript") silently corrupts data.
3. **No way for recruiters to access student profiles:** When a recruiter wants to verify a shortlisted candidate's credentials, they need a shareable, professional, unauthenticated web view — not a login screen.

---

## TASK 1: Full Interactive CRUD for Projects, Certifications & Work Experience

### Files to Modify
- **MODIFY:** `backend/app/api/v1/students.py` — add 6 new endpoints
- **MODIFY:** `backend/app/services/student_service.py` — add portfolio CRUD methods
- **MODIFY:** `backend/app/schemas/student.py` — add Project, Certification, Experience schemas
- **MODIFY:** `frontend/src/pages/student/Profile.jsx` — add full CRUD modals
- **MODIFY:** `frontend/src/api/endpoints.js` — add portfolio API functions

### Backend: Schemas to add in `schemas/student.py`

```python
class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    tech_stack: list[str] = Field(..., min_items=1, max_items=20)  # e.g. ["React", "FastAPI", "PostgreSQL"]
    github_url: Optional[str] = Field(None, pattern=r"^https://github\.com/.+")
    live_url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_featured: bool = False

class CertificationCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=300)
    issuing_organization: str = Field(..., min_length=2, max_length=200)
    issue_date: date
    expiration_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None  # URL to verify credential

class WorkExperienceCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=200)
    role: str = Field(..., min_length=2, max_length=200)
    location: Optional[str] = None
    employment_type: Literal["Internship", "Full-Time", "Part-Time", "Contract"] = "Internship"
    start_date: date
    end_date: Optional[date] = None    # None means currently working
    is_current: bool = False
    description: Optional[str] = None  # Bullet points / responsibilities
    skills_used: Optional[list[str]] = None
```

### Backend: Endpoints to add in `students.py`

```python
# ─── Projects ───────────────────────────────────────────────────────
@router.get("/me/projects")
async def get_my_projects(current_user: User = Depends(get_current_student), db: AsyncSession = Depends(get_db)):
    """Returns all projects for the current student, sorted by start_date DESC."""

@router.post("/me/projects", status_code=201)
async def add_project(data: ProjectCreate, current_user: User = Depends(get_current_student), db: AsyncSession = Depends(get_db)):
    """Creates a new project entry for the current student."""

@router.delete("/me/projects/{project_id}", status_code=204)
async def delete_project(project_id: uuid.UUID, current_user: User = Depends(get_current_student), db: AsyncSession = Depends(get_db)):
    """Deletes a project. Returns 403 if project doesn't belong to current student."""

# ─── Certifications ─────────────────────────────────────────────────
@router.get("/me/certifications")
async def get_my_certifications(...): ...

@router.post("/me/certifications", status_code=201)
async def add_certification(...): ...

@router.delete("/me/certifications/{cert_id}", status_code=204)
async def delete_certification(...): ...

# ─── Work Experience ────────────────────────────────────────────────
@router.get("/me/experience")
async def get_my_experience(...): ...

@router.post("/me/experience", status_code=201)
async def add_experience(...): ...

@router.delete("/me/experience/{exp_id}", status_code=204)
async def delete_experience(...): ...
```

Also add `POST /students/me/skills/bulk` for the resume confirmation workflow (see Task 2):
```python
class BulkSkillConfirm(BaseModel):
    skills: list[str]           # List of confirmed skill names
    source: str = "resume_verified"

@router.post("/me/skills/bulk")
async def bulk_confirm_skills(data: BulkSkillConfirm, current_user: User = Depends(get_current_student), db: AsyncSession = Depends(get_db)):
    """
    Creates StudentSkill rows for all confirmed skills.
    For each skill name: find or create Skill record, then upsert StudentSkill.
    Sets source='resume_verified' and is_verified=True on each skill.
    """
```

### Frontend: `Profile.jsx` — Add CRUD Modals

The Profile page currently has 4 tabs: Overview, Academic, Skills, Resume. You need to make the Overview tab fully interactive.

**Projects Section (inside Overview tab):**

```
Projects                                          [+ Add Project]
─────────────────────────────────────────────────────────────────
  Real-time Chat App                              ⭐ Featured    [🗑]
  React · FastAPI · PostgreSQL · Socket.io
  github.com/riya/chat-app · chat-demo.vercel.app
  Aug 2026 – Present

  ML Price Predictor                                             [🗑]
  Python · scikit-learn · Streamlit
  Aug 2026 – Oct 2026
```

**"+ Add Project" Modal:**
- Title input
- Description textarea (with character count)
- Tech Stack: a tag-input where typing a skill name and pressing Enter/comma creates a chip. Each chip has an ✕ to remove.
- GitHub URL input (with github.com link icon and validation)
- Live URL input
- Start Date / End Date date pickers (End Date disabled if "Ongoing" checkbox checked)
- Featured checkbox (shows ⭐ badge on card)
- Submit button calls `POST /students/me/projects`

**Certifications Section:**

```
Certifications                                   [+ Add Certification]
──────────────────────────────────────────────────────────────────────
  AWS Solutions Architect – Associate             Expires: Mar 2028  [🗑]
  Amazon Web Services · Issued: Mar 2026
  Credential ID: AWS-SAA-2026-R4891   [🔗 Verify]

  Google Data Analytics Professional Certificate              [🗑]
  Google · Issued: Jan 2026
```

**Work Experience Section:**

```
Work Experience                                    [+ Add Experience]
───────────────────────────────────────────────────────────────────
  Software Engineering Intern                      Jul – Sep 2026  [🗑]
  Razorpay · Bengaluru, IN · Internship
  Skills: React, TypeScript, REST APIs
  "Built the merchant dashboard analytics module using React and..."
```

**General UI rules for all modals:**
- Dark glassmorphism modal (backdrop-filter: blur, semi-transparent dark background)
- Smooth fade-in animation on open
- Form validation with inline error messages (not toast-based for field errors)
- Loading spinner on submit button while API call is in progress
- On success: modal closes, item appears in the list with a subtle "just added" highlight animation
- On delete: confirmation dialog "Are you sure you want to delete this?" before calling DELETE endpoint

---

## TASK 2: Two-Step Resume Skill Confirmation Modal

### The Problem
Currently: Student uploads resume → NLP extracts skills → skills are directly saved to DB. There is no human review step. False positives corrupt the skill profile.

### Files to Modify
- **MODIFY:** `frontend/src/pages/student/Profile.jsx` — intercept resume upload, show confirmation modal
- **MODIFY:** `frontend/src/api/endpoints.js` — add `studentApi.bulkConfirmSkills()`

### Frontend Implementation (all in `Profile.jsx`)

**Existing flow:** "Upload Resume" button → `resumeApi.upload(file)` → skills silently saved.

**New flow:**
1. Student clicks "Upload Resume"
2. Upload happens as before → response contains `{ extracted_skills: [...] }` with each skill having a `confidence` field (0.0–1.0)
3. After upload completes, instead of showing "success", open the **"Review Extracted Skills" modal**

**Review Modal Design:**

```
┌────────────── Review Extracted Skills ──────────────────────────────────┐
│  We found 14 skills in your resume. Review and confirm before saving.   │
│                                                                          │
│  🟢 High Confidence (≥ 85%)               Check all that are correct:   │
│  ──────────────────────────────────────────────────────────────────────  │
│  [✓] Python           [✓] React           [✓] FastAPI                   │
│  [✓] PostgreSQL       [✓] Docker          [✓] REST APIs                 │
│  [✓] Git              [✓] SQL                                            │
│                                                                          │
│  🟡 Probable Match (60–84%)               Verify these carefully:        │
│  ──────────────────────────────────────────────────────────────────────  │
│  [✓] Machine Learning    (found: "ML project")                           │
│  [ ] Java                (found: "JavaScript" — UNCHECK if wrong!)       │
│  [✓] Kubernetes          (found: "k8s")                                  │
│                                                                          │
│  ➕ Add a skill we missed:  [________________] [+ Add]                   │
│                                                                          │
│  [← Back]         9 skills selected       [✓ Confirm & Sync to Profile] │
└──────────────────────────────────────────────────────────────────────────┘
```

**Implementation rules:**
- High confidence skills (≥0.85) are pre-checked but editable.
- Probable match skills (0.60–0.84) are also pre-checked but with a yellow warning icon and the raw extracted text shown in parentheses.
- Student can uncheck any skill.
- Student can add an additional skill via the "Add a skill" input (with autocomplete from `skillsApi.search()`).
- "Confirm & Sync to Profile" calls `POST /students/me/skills/bulk` with the confirmed skill list.
- On success: modal closes, Skills tab updates to show the newly confirmed skills.
- If the backend response doesn't include `confidence` per skill (legacy), use 0.85 as default and group all into high confidence.

---

## TASK 3: Shareable Public Verified Student Portfolio

### Files to Create / Modify
- **CREATE:** `frontend/src/pages/student/PublicPortfolio.jsx`
- **MODIFY:** `frontend/src/router/AppRouter.jsx` — add unauthenticated route `/portfolio/:studentId`
- **MODIFY:** `backend/app/api/v1/students.py` — add `GET /students/{id}/public-profile` (no auth)
- **MODIFY:** `frontend/src/pages/student/Profile.jsx` — add "Share Portfolio" button
- **MODIFY:** `frontend/src/api/endpoints.js` — add `studentApi.getPublicProfile(id)`

### Backend: Public Profile Endpoint

```python
@router.get("/{student_id}/public-profile")
async def get_public_profile(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    # No authentication dependency — this is a public endpoint
):
    """
    Returns a safe subset of student data for public recruiter view.
    MUST NOT include: email, phone, address, academic records, attendance.
    MUST include: name, branch, department, graduation_year,
                  verified skills (source='resume_verified' only),
                  projects, certifications, work_experience,
                  CGPA (only if student.data_sharing_consent = True).
    Returns 404 if student does not exist, 403 if student has disabled public profile.
    """
```

### Frontend: `PublicPortfolio.jsx`

A clean, professional page optimized for recruiter viewing and PDF printing.

**URL:** `/portfolio/:studentId`

**Page Layout:**

```
┌────────────────────────────────────────────────────────────────────────┐
│  [CCIP Logo]                    Verified by University Placement Cell   │
│                                                                         │
│  Riya Sharma                    🎓 B.Tech Computer Science, 2026       │
│  Roll: R2024CS001               CGPA: 8.4 / 10.0  ✓ Verified           │
│                                                                         │
│  ──────────── Verified Skills ──────────────────────────────────────── │
│  [Python] [React] [FastAPI] [PostgreSQL] [Docker] [Machine Learning]   │
│  [Kubernetes] [REST APIs] [Git] [SQL]                                  │
│                                                                         │
│  ──────────── Projects ─────────────────────────────────────────────── │
│  Real-time Chat App  · React, FastAPI, PostgreSQL, Socket.io           │
│  ⭐ Featured  |  github.com/riya/chat-app  |  Aug 2026 – Present       │
│  "A scalable real-time messaging app with WebSocket support..."        │
│                                                                         │
│  ML Price Predictor  · Python, scikit-learn, Streamlit                 │
│  github.com/riya/price-pred  |  Aug – Oct 2026                         │
│                                                                         │
│  ──────────── Certifications ────────────────────────────────────────── │
│  AWS Solutions Architect – Associate  (Amazon Web Services, Mar 2026)  │
│  [🔗 Verify Credential]                                                │
│                                                                         │
│  ──────────── Work Experience ───────────────────────────────────────── │
│  Software Engineering Intern · Razorpay · Jul–Sep 2026                 │
│  Skills: React, TypeScript, REST APIs                                  │
│                                                                         │
│  ──────────────────────────────────────────────────────────────────────│
│     🛡️ This profile is verified by [College Name] Placement Cell       │
│     Profile ID: R2024CS001 · Last updated: Sep 12, 2026                │
└────────────────────────────────────────────────────────────────────────┘
```

**Design requirements:**
- Clean, minimal, professional aesthetic (not the dark portal theme — use white/light background for print-friendliness)
- A "Verified by University Placement Cell" badge/watermark at the bottom
- The page should be print-friendly: add `@media print` CSS rules to hide navigation and show everything cleanly on A4
- No login required to access this page

**Share Portfolio Button in `Profile.jsx`:**

Add a **"🔗 Share Verified Portfolio"** button to the Profile page header area:
- Clicking copies the full URL `https://{domain}/portfolio/{studentId}` to clipboard
- Show a "Link copied! ✓" toast notification for 2 seconds after copy
- Also show a small QR code image generated from the URL (use the free `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={url}` API — no npm package needed)

**Mock JSON:** Since this is a public endpoint, also create a mock response at `frontend/public/mocks/public_profile.json` with realistic data for development.

---

## Checklist — What "Done" Looks Like

- [ ] Student can add, view, and delete Projects with GitHub URL, demo link, and tech stack chips
- [ ] Student can add and delete Professional Certifications with credential ID and verification link
- [ ] Student can add and delete Work Experience / Internships with employment type and skills used
- [ ] After resume upload, an interactive skill review modal appears grouping extractions by confidence
- [ ] Student can uncheck false-positive skills and add missed skills before confirming
- [ ] Confirmed skills are saved with source tag `resume_verified`
- [ ] Public portfolio route `/portfolio/:studentId` works without login
- [ ] Public portfolio shows verified skills, projects, certifications, and work experience
- [ ] "Share Verified Portfolio" button in Profile copies the public URL to clipboard
- [ ] QR code for the portfolio link is displayed in the share panel

---

## File Touch Summary

| Action | File |
|--------|------|
| MODIFY | `backend/app/api/v1/students.py` |
| MODIFY | `backend/app/services/student_service.py` |
| MODIFY | `backend/app/schemas/student.py` |
| MODIFY | `frontend/src/pages/student/Profile.jsx` |
| MODIFY | `frontend/src/api/endpoints.js` |
| CREATE | `frontend/src/pages/student/PublicPortfolio.jsx` |
| MODIFY | `frontend/src/router/AppRouter.jsx` |
| CREATE | `frontend/public/mocks/public_profile.json` |

# 🧑‍💻 Sakshi's Task Sheet (Sprint 3) — Complete Student Identity System: Rich Portfolio V2, Resume Builder, Skill Verification, Public Share & Alumni Network

> **Role:** Student Identity & Career Branding Engineer
> **Priority:** 🟠 P1 — Student's public-facing professional identity
> **Reference Standard:** LinkedIn Profile, GitHub Portfolio, Polywork, Notion Portfolio Pages

---

## 📋 Industrial Context — Why This Sprint Matters

A student's CCIP profile is currently a data form — fields filled in, checkboxes ticked. It does not represent a professional identity. When a recruiter (added in Purushottam's Sprint 3 task) views a candidate, they need to see a portfolio that rivals a LinkedIn profile: projects with live demos, skills with proof (assessment-backed badges), certifications with expiry dates, internship history with impact statements, and a shareable public URL they can put on their resume.

Three major gaps:

1. **No Resume Builder:** Students write resumes in Word and upload a static PDF. Industrial platforms generate resumes dynamically from structured profile data, styled with templates.
2. **No Skill Verification Badges:** Anyone can claim "Python Expert." Assessment-backed badges prove it.
3. **No Alumni Network:** Seniors who got placed have no way to mentor juniors on CCIP.

---

## TASK 1: Rich Portfolio System V2

### Backend

#### MODIFY: `backend/app/models/portfolio.py` — Add rich fields

```python
class Project(Base):
    # existing: id, student_id, title, description, tech_stack, github_url
    # ADD:
    live_url: str | None           # deployed demo URL
    thumbnail_url: str | None      # uploaded image (/uploads/project_thumbs/)
    status: str default="completed"  # "completed" | "in_progress" | "archived"
    start_date: date | None
    end_date: date | None
    role: str | None               # "Lead Developer" | "Backend Dev" | "Frontend Dev"
    team_size: int | None
    highlights: ARRAY(String)      # bullet points of achievements (max 5)
    featured: bool default=False   # pinned to top of portfolio

class Internship(Base):
    # existing: id, student_id, company, role, start_date, end_date, description
    # ADD:
    location: str | None           # "Bengaluru, IN" or "Remote"
    stipend_monthly: float | None
    offer_letter_url: str | None
    completion_certificate_url: str | None
    skills_used: ARRAY(String)
    highlights: ARRAY(String)      # impact statements (max 4)
    verified: bool default=False   # TPO/Faculty can mark as verified
    linkedin_post_url: str | None

class Certification(Base):
    # existing: id, student_id, name, issuer, issued_date
    # ADD:
    expiry_date: date | None
    credential_url: str | None     # verify link (Credly, Coursera, etc.)
    credential_id: str | None
    certificate_image_url: str | None
    skills_covered: ARRAY(String)
    verified: bool default=False
```

#### MODIFY: `backend/app/api/v1/students.py` — Project CRUD fully functional

Ensure all CRUD operations work for:

- Projects: `POST/GET/PATCH/DELETE /students/me/projects`
  - POST: accept `thumbnail` as optional multipart file upload
  - PATCH: same + `featured` toggle
- Internships: `POST/GET/PATCH/DELETE /students/me/internships`
  - Accept `offer_letter` and `certificate` file uploads (PDF, max 5MB)
- Certifications: `POST/GET/PATCH/DELETE /students/me/certifications`
  - Accept `certificate_image` upload (image, max 2MB)
- CareerGoals: `GET/PATCH /students/me/career-goals`

#### CREATE: `backend/app/api/v1/portfolio.py` (public-facing, no auth required for GET)

```
GET  /portfolio/{student_id}                 → public portfolio (returns limited data)
GET  /portfolio/me                           → full portfolio (authenticated student, all data)
PATCH /portfolio/me/settings                 → toggle is_public, custom_slug
GET  /portfolio/slug/{custom_slug}           → resolve custom slug → student portfolio
POST /portfolio/me/projects/{id}/feature     → toggle featured flag
GET  /portfolio/me/completeness              → portfolio completeness score with suggestions
```

Portfolio completeness score (0–100):

- Basic info (name, bio, photo): 15 pts
- Skills (≥5 skills): 10 pts
- Projects (≥2 projects): 20 pts
- Internships (≥1): 15 pts
- Certifications (≥1): 10 pts
- Resume uploaded: 15 pts
- LinkedIn URL: 5 pts
- GitHub URL: 5 pts
- Career goal set: 5 pts

### Frontend

#### MODIFY: `frontend/src/pages/student/Profile.jsx` — Complete rewrite into tabbed editor

Current state: a huge 163KB file. Restructure into clean tabs:

Tab 1: **Personal Info** — name, bio, photo upload, phone, links (LinkedIn, GitHub, Portfolio URL)
Tab 2: **Skills** — existing skill tag editor (already works)
Tab 3: **Projects** — CRUD cards with enhanced fields

- Each project card: thumbnail preview (if uploaded), title, role, team size, dates, status badge, highlights bullets
- Edit modal: all fields, thumbnail upload, tech stack multi-input, highlights dynamic list
- "Pin to top" toggle (featured)
- "Add GitHub" + "Add Live Demo" URL fields
  Tab 4: **Internships** — CRUD with enhanced fields
- Each internship: company logo (auto-fetched from clearbit?), role, dates, location, stipend, highlights
- File upload: offer letter PDF, certificate PDF
- Impact statement builder: "Increased X by Y% by doing Z" template
  Tab 5: **Certifications** — CRUD with expiry tracking
- Color-coded expiry: green=valid, yellow=expiring in 3 months, red=expired
- "Verify" link to credential URL
  Tab 6: **Academic Records** — read-only UMS-synced data
  Tab 7: **Career Goals** — target roles, target companies, expected graduation, preferred locations

#### CREATE: `frontend/src/pages/student/PublicPortfolioV2.jsx`

Route: `/p/:slug` (short URL like `/p/riya-sharma-cs`) or `/portfolio/:studentId`

Premium portfolio display page designed to impress recruiters:

**Hero Section:**

- Full-width gradient background (uses institution's primary color from settings)
- Student photo (circle, 120px), name (large), role headline from career goals
- Skills badges row (top 6 skills with proficiency indicators)
- Contact/Social links row: LinkedIn, GitHub, Email (mailto:), portfolio site
- "Download Resume" button (if resume_url set)
- Assessment badges row: earned badges from high assessment scores

**Featured Projects (large cards):**

- Project thumbnail (or gradient placeholder with initials)
- Title, role, team size, status pill
- Tech stack chips
- Highlights as bullet points
- Live Demo + GitHub buttons
- Non-featured projects in smaller grid below

**Work Experience:**

- Timeline style: internships sorted newest first
- Company name, role, dates, location, highlights
- "Verified" green badge if TPO/faculty verified

**Certifications:**

- Grid of certification cards with logo, name, issuer, date, credential link

**Skill Verified Badges:**

- Earned via assessment: "Python — Assessed 85% | CCIP Verified ✓"
- Displayed as small badge chips in a "Verified Skills" section

**Footer:**

- "Profile on CCIP — {college name}" branding
- Share buttons: copy link, WhatsApp share, LinkedIn share

---

## TASK 2: Dynamic Resume Builder

### Backend

#### CREATE: `backend/app/services/resume_builder_service.py`

```python
class ResumeBuilderService:
    async def generate_latex(self, student_id: UUID, template: str = "modern") -> str:
        """
        1. Load student's full profile: personal, skills, projects, internships, certs, academic
        2. Render Jinja2 LaTeX template (templates/resume_{template}.tex.j2)
        3. Return LaTeX string
        Templates: "modern" | "minimal" | "academic" | "tech"
        """

    async def generate_pdf(self, student_id: UUID, template: str = "modern") -> bytes:
        """
        1. Generate LaTeX string
        2. Compile with pdflatex subprocess (or use reportlab as fallback)
        3. Return PDF bytes
        Fallback: generate HTML → use weasyprint to convert to PDF
        """

    async def generate_html_preview(self, student_id, template) -> str:
        """Quick HTML preview for frontend before PDF export"""
```

**LaTeX/HTML Template Structure (implement all 4 templates):**

`modern`: Two-column layout, colored header bar with name and contact, skills as pill badges, projects with horizontal rule separators

`minimal`: Clean single-column, minimal fonts, classic academic style, no colors

`academic`: Emphasizes CGPA, coursework, publications section (even if empty), traditional format

`tech`: Dark accent, monospace section headers, GitHub-style skill indicators, project repo links prominent

#### MODIFY: `backend/app/api/v1/resume.py`

```
GET  /resume/preview/{template}              → HTML preview (returns HTML string)
GET  /resume/download/{template}             → PDF download (Content-Type: application/pdf)
GET  /resume/templates                       → list available templates with thumbnails
POST /resume/upload                          → upload custom PDF (existing endpoint, keep)
GET  /resume/ats-score                       → analyze uploaded resume for ATS compatibility
```

#### CREATE: `backend/app/services/ats_analyzer.py`

```python
class ATSAnalyzer:
    async def analyze(self, student_id: UUID) -> dict:
        """
        Analyze student's uploaded resume (or generated one) for ATS friendliness.
        Use Gemini to review:
        1. Keyword density: does resume contain high-demand skill keywords?
        2. Format compliance: no tables, no headers/footers, parseable sections
        3. Quantified achievements: count impact statements with numbers
        4. Length: optimal 1–2 pages

        Returns:
        {
          "ats_score": 73,  # 0-100
          "keyword_coverage": 0.65,  # 65% of top skills present
          "missing_keywords": ["Docker", "CI/CD", "System Design"],
          "feedback": [
            "Add quantified achievements (e.g. 'Improved latency by 40%')",
            "Missing key skill: Docker — add if you have experience"
          ],
          "gemini_suggestions": "... 3 sentences of Gemini advice ..."
        }
        """
```

### Frontend

#### CREATE: `frontend/src/pages/student/ResumeBuilder.jsx`

Route: `/student/resume-builder`

**Template Gallery:**

- 4 template cards with preview thumbnails
- Currently selected: highlighted with blue ring
- "Preview" button → opens preview modal

**Live Preview Panel (2-panel layout):**

- Left: Form editor (sections: Personal, Skills, Projects, Internships, Certs)
  - Each section: checklist of items to include/exclude from resume (checkboxes)
  - Reorder sections by drag-handle
- Right: Real-time HTML preview iframe (updates on checkbox changes)
  - Zoom: 50% / 75% / 100%

**Actions:**

- "Download PDF" → GET /resume/download/{template} → browser download
- "Check ATS Score" → GET /resume/ats-score → opens results drawer

**ATS Score Drawer:**

- Big score gauge (0–100)
- Keyword coverage progress bar
- Missing keywords chips (click to go to skills tab)
- Feedback bullet list
- Gemini suggestions card

---

## TASK 3: Skill Verification Badge System

### Backend

#### CREATE: `backend/app/services/skill_badge_service.py`

```python
BADGE_THRESHOLDS = {
    "beginner": 60,    # assessed 60–74%
    "proficient": 75,  # assessed 75–84%
    "expert": 85,      # assessed 85–94%
    "master": 95,      # assessed 95–100%
}

class SkillBadgeService:
    async def award_badge_if_earned(self, student_id: UUID, skill_name: str, score: float, db) -> SkillBadge | None:
        """
        Called by assessment engine after each session completion.
        1. Check if student scored >= 60% on a skill-specific assessment
        2. If yes, and they don't already have this badge at this level:
           - Create/update SkillBadge record
           - Award higher badge if score improved
           - Publish SKILL_BADGE_EARNED notification
        3. Return badge if awarded, None if not qualifying
        """

    async def get_student_badges(self, student_id: UUID) -> list[SkillBadge]:
        """All badges for a student, sorted by earned_at desc"""

    async def get_leaderboard_by_skill(self, skill_name: str, dept: str | None) -> list[dict]:
        """Top 10 students with highest badge level for this skill (anonymized)"""
```

#### CREATE: `backend/app/models/badge.py`

```python
class SkillBadge(Base):
    __tablename__ = "skill_badges"
    id: UUID PK
    student_id: UUID FK→students.id
    skill_id: UUID FK→skills.id
    skill_name: str     # denormalized for speed
    level: str          # "beginner" | "proficient" | "expert" | "master"
    score: float        # highest assessment score that earned this badge
    assessment_session_id: UUID FK→assessment_sessions.id
    earned_at: datetime
    UNIQUE(student_id, skill_id)  # one badge per skill, level upgrades in place
```

#### MODIFY: `backend/app/api/v1/assessments.py`

After submitting and scoring a session → call `SkillBadgeService.award_badge_if_earned()`

```
GET /badges/my                        → current student's all badges
GET /badges/my/{skill}                → badge for specific skill
GET /badges/leaderboard/{skill}       → top earners for this skill
```

### Frontend

#### MODIFY: `frontend/src/pages/student/AssessmentsList.jsx`

- Show existing badges next to each skill topic
  - "Python 🥇 Expert (91%)" badge chip if student has Python expert badge
  - "Take to Earn Badge →" CTA if no badge yet for this skill
  - "Improve Your Badge →" if badge exists but can be upgraded

#### CREATE: `frontend/src/pages/student/Badges.jsx`

Route: `/student/badges`

Badge showcase page:

- "Your Verified Skills" hero section
- Badge grid: each badge = skill icon, skill name, level label, score, earned date
- Badge levels displayed as: 🥉 Beginner / 🥈 Proficient / 🥇 Expert / 🏆 Master
- "Share your badges" → generates a shareable badge card image (canvas API or backend-generated)
- Skill leaderboard tab: "Top students in your dept for each skill" (anonymized)

---

## TASK 4: Alumni Mentorship Network

### Backend

#### CREATE: `backend/app/models/alumni.py`

```python
class AlumniProfile(Base):
    __tablename__ = "alumni_profiles"
    id: UUID PK = user.id FK→users.id
    graduation_year: int
    company: str
    role: str(200)
    location: str | None
    linkedin_url: str | None
    is_mentor: bool default=False   # opted in to mentor juniors
    mentor_capacity: int default=5  # max simultaneous mentees
    expertise_areas: ARRAY(String)  # ["DSA", "System Design", "ML", "Web Dev"]
    bio: str | None
    response_time_days: int default=3

class MentorshipRequest(Base):
    __tablename__ = "mentorship_requests"
    id: UUID PK
    student_id: UUID FK→students.id
    alumni_id: UUID FK→alumni_profiles.id
    message: str       # intro message from student
    status: str default="pending"  # pending | accepted | declined | completed
    created_at: datetime
    responded_at: datetime | None
```

#### CREATE: `backend/app/api/v1/alumni.py`

```
GET  /alumni                          → list alumni mentors (filter: expertise, company, graduation_year)
GET  /alumni/{id}                     → alumni profile detail
POST /alumni/request/{alumni_id}      → student sends mentorship request with intro message
GET  /alumni/my-requests              → student's sent requests + status
GET  /alumni/my-mentees               → alumni sees pending/active mentee requests
PATCH /alumni/requests/{id}/respond   → alumni accepts or declines request
GET  /alumni/my-profile               → alumni edits their own profile
PATCH /alumni/my-profile              → update is_mentor, expertise_areas, bio, etc.
```

### Frontend

#### CREATE: `frontend/src/pages/student/AlumniNetwork.jsx`

Route: `/student/alumni`

**Browse Mentors:**

- Filter: Expertise area, Company, Graduation Year, Available (is_mentor)
- Mentor cards: alumni photo/initials, name, "Class of 20XX", company, role, expertise chips, response time badge
- "Request Mentorship" button → opens request modal

**Request Modal:**

- "Introduce yourself" textarea (300 char limit)
- "What do you want to learn?" textarea
- Submit → POST /alumni/request/{id}

**My Requests Tab:**

- Sent requests with status badges: Pending / Accepted / Declined
- Accepted: show message "Check your email/LinkedIn for their response" (mentor's LinkedIn shown)
- Declined: soft message

#### CREATE: `frontend/src/pages/alumni/AlumniDashboard.jsx`

Route: `/alumni/dashboard` (accessible when role="alumni")

- Pending mentee requests list
- Accept/Decline buttons per request
- Edit my mentor profile: expertise areas, bio, capacity, response time

---

## Verification Checklist

- [ ] Project CRUD with thumbnail upload saves image and displays in portfolio
- [ ] Internship with certificate PDF upload works, file downloadable
- [ ] Public portfolio page at `/p/:slug` loads without auth and shows all sections
- [ ] Portfolio completeness score correctly computes all 9 components
- [ ] Resume builder shows live HTML preview updating as you toggle sections
- [ ] PDF download works and contains student's actual data
- [ ] ATS score returns Gemini suggestions (or graceful fallback)
- [ ] Assessment scoring ≥ 85% → badge auto-awarded → notification sent
- [ ] Badge shows on badge page with correct level icon
- [ ] Alumni mentorship request creates DB record and changes status correctly
- [ ] Public portfolio does not expose email/phone (contact links only go via mailto)
- [ ] Certification with expired date shows red "Expired" badge

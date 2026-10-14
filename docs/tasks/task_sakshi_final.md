# 🧑‍💻 Sakshi's Final Task Sheet — Student Identity System: Rich Portfolio V2, Public Vanity URLs, Resume ATS Parser, Alumni Mentorship & Prep Hub

> **Role:** Student Identity & Career Branding Systems Engineer  
> **Priority:** 🔴 P0 — Student Professional Identity, Public Presence & Alumni Services  
> **Reference Standard:** LinkedIn Profiles, GitHub Developer Portfolios, Reactive Resume, Notion Portfolio Pages, ADPList Mentorship  

---

## 📋 Industrial Context — Why This Final Submission Matters

A student's placement profile cannot merely be a static database form with CGPA and contact numbers. When top-tier tech recruiters evaluate hundreds of applicants for high-CTC roles:
1. **Recruiters Need Proof of Competence:** Anyone can type "Python Expert" on a resume. Recruiters demand live deployed project links, GitHub source repositories, assessment-backed badges, verified internships with company credentials, and authenticated certifications (Credly/Coursera).
2. **Public Shareability:** Students need a high-converting, responsive vanity URL (`/portfolio/slug/priya-agarwal`) to embed in resumes, LinkedIn profiles, and cold emails to engineering managers.
3. **ATS Resume Optimization:** Over 75% of resumes are filtered out by automated Applicant Tracking Systems before a human recruiter sees them. Students need an integrated ATS analyzer that computes keyword compatibility against target job descriptions.
4. **Alumni Mentorship Network:** Senior alumni who secured offers at Google, Microsoft, Amazon, and top startups are the most valuable resource for campus juniors. CCIP enables 1-on-1 mentorship session booking and company-specific preparation guides.

---

## TASK 1: Rich Portfolio System V2 & Full Lifecycle CRUD

### Database Architecture (`backend/app/models/portfolio.py`)
Ensure all entity models support rich production fields:
- **`Project`**:
  - `title`, `description`, `tech_stack` (Array of Strings)
  - `github_url`, `live_url` (deployed demo URL)
  - `thumbnail_url` (project preview image)
  - `status` (`"completed"`, `"in_progress"`, `"archived"`)
  - `role` (`"Lead Developer"`, `"Full-Stack"`, `"ML Engineer"`), `team_size`
  - `highlights` (Array of impact statements)
  - `featured` (Boolean flag to pin to top of public portfolio)
- **`Internship`**:
  - `company`, `role`, `start_date`, `end_date`, `description`
  - `location`, `stipend_monthly`
  - `offer_letter_url`, `completion_certificate_url`
  - `skills_used` (Array of Strings)
  - `verified` (Boolean flag marked by TPO or Faculty)
- **`Certification`**:
  - `name`, `issuer`, `issued_date`, `expiry_date`
  - `credential_id`, `credential_url` (Credly, Coursera verification link)
  - `certificate_image_url`, `skills_covered`
  - `verified` (Boolean flag)

### Backend Endpoints (`backend/app/api/v1/students.py` & `backend/app/api/v1/portfolio.py`)
- `GET /students/me/projects`: Fetch student projects.
- `POST /students/me/projects`: Create project with rich fields and featured flag.
- `PATCH /students/me/projects/{id}`: Update project details and toggle `featured`.
- `DELETE /students/me/projects/{id}`: Atomic project deletion.
- `POST/GET/PATCH/DELETE /students/me/internships`: Full CRUD for student internships.
- `POST/GET/PATCH/DELETE /students/me/certifications`: Full CRUD for student certifications.
- `GET/PATCH /students/me/career-goals`: Manage target roles, preferred locations, and expected CTC range.

### Frontend Portfolio Manager (`frontend/src/pages/student/Profile.jsx`)
- Multi-tab identity center: **Overview**, **Projects**, **Experience & Internships**, **Certifications**, **Career Preferences**.
- Project card with live demo chip, GitHub link, tech stack badges, and one-click "Pin as Featured" star.
- Clean modal forms for adding and editing records without page reloads.

---

## TASK 2: Public Vanity Portfolio & Completeness Calculator

### Public Showcase Endpoints (`backend/app/api/v1/portfolio.py`)
- `GET /portfolio/{student_id}`: Unauthenticated endpoint returning sanitized public profile (name, bio, verified skills, featured projects, certifications, social links). Omits private details like phone numbers and backlogs.
- `GET /portfolio/slug/{custom_slug}`: Resolves human-readable vanity slug (e.g., `priya-agarwal`) to student profile.
- `PATCH /portfolio/me/settings`: Toggle `is_public` visibility and configure custom vanity slug.
- `GET /portfolio/me/completeness`: Calculates profile completeness score (0–100%) with actionable next steps:
  - Basic Profile (Avatar, bio, department, semester): 15 pts
  - Skills (at least 5 listed): 10 pts
  - Projects (at least 2 projects added): 20 pts
  - Internships (at least 1 experience): 15 pts
  - Certifications (at least 1 credential): 10 pts
  - Resume uploaded to Vault: 15 pts
  - External links (GitHub, LinkedIn): 10 pts
  - Career target role configured: 5 pts

### Public Showcase UI (`frontend/src/pages/public/PublicPortfolio.jsx`)
- Premium glassmorphism design with responsive grid layout.
- Hero card: Student name, department, graduation year, verified skill badges, social icons (GitHub, LinkedIn, Portfolio).
- Featured projects carousel/grid with direct "Live Demo" and "Source Code" action buttons.
- Experience timeline showing verified internships with company logos.
- Zero login required — fully accessible by off-campus recruiters.

---

## TASK 3: Automated Resume Parser & ATS Compatibility Analyzer

### Parser Service (`backend/app/services/resume_parser.py`)
- Extracts plain text from uploaded PDF / DOCX resumes via `pypdf` or `pdfminer`.
- Pattern matching and entity recognition:
  - Contact Information (Email, Phone, LinkedIn URL, GitHub URL)
  - Education (Degree, Branch, CGPA, Graduation Year)
  - Detected Technical Skills (Cross-referenced against platform master skill taxonomy)
  - Project highlights and work experience durations.

### ATS Score Analyzer (`POST /resume/ats-score`)
In `backend/app/api/v1/resume.py`:
- Accepts student resume text/file and optional target job description or placement drive ID.
- Computes ATS match score (0–100%):
  - Keyword density and skill coverage: 50%
  - Section structural completeness (Summary, Experience, Education, Skills): 25%
  - Action verb usage and quantifiable metrics (e.g., "increased by 20%"): 25%
- Returns diagnostic payload:
  ```json
  {
    "ats_score": 84.0,
    "grade": "Strong",
    "matched_skills": ["React", "TypeScript", "Node.js", "Docker"],
    "missing_target_skills": ["PostgreSQL", "AWS S3", "GraphQL"],
    "formatting_flags": [
      "No tables detected (ATS safe)",
      "Standard bullet formatting verified"
    ],
    "actionable_recommendations": [
      "Include quantifiable impact metrics in Project 2",
      "Add PostgreSQL explicitly to the skills section"
    ]
  }
  ```

---

## TASK 4: Placement Preparation Resource Hub & Collections

### Resource Hub API (`backend/app/api/v1/prep_resources.py`)
- `GET /prep/resources`: Paginated repository of interview guides, DSA cheat sheets, and system design roadmaps.
  - Multi-tag filtering by category (`DSA`, `System Design`, `HR`, `Behavioral`, `Aptitude`) and target company (`Google`, `Microsoft`, `TCS`, `Infosys`).
  - Strict pagination contract returning `PaginatedResponse` with `page`, `page_size`, `total_items`, and `total_pages`.
- `POST /prep/resources/{id}/upvote`: Community peer upvote mechanism incrementing resource helpfulness.
- `GET /prep/collections`: Thematic bundles (e.g., "Top 75 LeetCode Patterns", "FAANG System Design Primer").
- `POST /prep/progress/{resource_id}`: Tracks student learning progress (`not_started`, `in_progress`, `completed`).
- `GET /prep/progress/mine`: Returns student's personal completion statistics.

### Prep Hub UI (`frontend/src/pages/student/PrepHub.jsx`)
- Interactive resource library with search bar and company tag filters.
- Progress bar displaying completed guides per category.
- One-click bookmarking and community upvote button with live counter.

---

## TASK 5: Alumni Mentorship & Professional Network

### Mentorship Engine (`backend/app/api/v1/alumni.py`)
- `POST /alumni/profile`: Placed students register as alumni mentors, specifying current company, role, domains of expertise, and weekly availability slots.
- `GET /alumni`: Filterable directory of alumni mentors by company, graduation year, and technical domain.
- `POST /alumni/mentorship`: Students submit 1-on-1 mentorship connection requests with a personalized inquiry note.
- `PATCH /alumni/mentorship/{id}`: Mentor accepts or declines connection request.
- `POST /alumni/sessions`: Schedules virtual mock interview or resume review session with calendar timestamp and meeting link.
- `POST /alumni/sessions/{id}/feedback`: Student submits session rating (1–5 stars) and qualitative review.

### Alumni Portal UI (`frontend/src/pages/student/Alumni.jsx`)
- Visual mentor directory with company badges (Google, Amazon, TCS), graduation batch, and areas of expertise.
- "Book Mentorship Session" modal with date/time slot picker and session agenda topic input.
- "My Sessions" tab tracking pending, confirmed, and completed sessions.

---

## 🛠️ Verification Runbook & Commands

Execute in terminal to confirm complete system integrity:

```powershell
# 1. Verify all backend models, schemas, and endpoints
cd d:\Projects\p1\backend
.\.venv\Scripts\pytest.exe tests/ -k "portfolio or prep or alumni or resume" -v

# 2. Verify all 179 platform tests pass
.\.venv\Scripts\pytest.exe -q

# 3. Validate frontend production build
cd d:\Projects\p1\frontend
npm run build
```

---

## 🎓 Viva Defense Talking Points for External Examiners

1. **Portfolio Security vs Public Sharing:** Explain how `/portfolio/slug/{slug}` securely strips private student telemetry (backlogs, academic disciplinary records, phone numbers) using explicit Pydantic response schemas (`PublicPortfolioResponse`) while showcasing verified projects and Credly-backed credentials.
2. **ATS Compatibility Engineering:** Explain the heuristic scoring engine: why high keyword coverage alone is insufficient, and how the algorithm validates section hierarchy, parses action-oriented verbs, and penalizes non-parseable layouts.
3. **Institutional Network Effect:** Explain how the Alumni Mentorship network drives viral institutional retention — graduating students who secured offers through CCIP immediately transition to mentors, guiding the subsequent junior batch.

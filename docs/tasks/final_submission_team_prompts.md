# 🚀 CCIP Final Submission — Master Team Task Distribution & Prompts Runbook

> **Project:** Campus Placement & Career Intelligence Platform (CCIP)  
> **Status:** Production-Ready & Feature Complete  
> **Test Baseline:** 179/179 Pytest Tests Passing | 0 Frontend Build Errors  
> **Team Size:** 6 Members  
> **Artifacts Directory:** `docs/tasks/`  

---

## 👥 Master Team Assignment Matrix

| Member | Assigned Domain | Task File | Primary Tech Stack |
| :--- | :--- | :--- | :--- |
| **Yash (Lead)** | Core Platform Architecture, Multi-Role Auth, Super Admin Panel, Live Telemetry & Configuration Persistence | [`task_yash_final.md`](file:///d:/Projects/p1/docs/tasks/task_yash_final.md) | FastAPI, JWT, Bcrypt, SQLite/PostgreSQL, Redis, Admin UI |
| **Sachin** | Machine Learning Candidate Matcher, Explainable Diagnostics, Skill Gap Analyzer & Holt's Demand Forecasting | [`task_sachin_final.md`](file:///d:/Projects/p1/docs/tasks/task_sachin_final.md) | SentenceTransformers, Scikit-learn, LightGBM, Statsmodels, Vector Embeddings |
| **Deep** | Generative AI Career Services: Gemini Copilot V3 (SSE), Mock Interview Simulator V2 & BoS Proposals | [`task_deep_final.md`](file:///d:/Projects/p1/docs/tasks/task_deep_final.md) | Google Gemini 1.5 Pro, Server-Sent Events (SSE), WebSockets, Markdown Rendering |
| **Purushottam** | TPO Operations Command Centre: Placement Drives, Bulk Shortlisting, Logistics Calendar & Institutional Accreditation | [`task_purshottam_final.md`](file:///d:/Projects/p1/docs/tasks/task_purshottam_final.md) | Pydantic V2, SQLAlchemy 2.0 Async, NIRF/NAAC Metric Calculators, Recruiter CRM |
| **Sakshi** | Student Identity System: Rich Portfolio V2, Public Vanity URLs, Resume ATS Parser, Alumni Network & Prep Hub | [`task_sakshi_final.md`](file:///d:/Projects/p1/docs/tasks/task_sakshi_final.md) | PyPDF, NLP Keyword Matcher, Credly Badges, Public Slug Router, Resource Library |
| **Anjula** | Student Experience Hub: Anonymous Company Reviews, Application Tracker Timeline, Document Vault & Faculty Analytics | [`task_anjula_final.md`](file:///d:/Projects/p1/docs/tasks/task_anjula_final.md) | Event Timeline State Machine, Secure MIME File Storage, Faculty BI Dashboard |

---

## 📋 Copy-Paste Ready Prompts For Each Team Member

Below are the exact, comprehensive copy-paste prompts designed for each team member to feed directly into their AI assistant or IDE terminal:

---

### 1️⃣ Prompt for Yash (Lead Architect & Core Systems)

```markdown
You are Yash, Lead Architect and Core Systems Engineer on the Campus Placement & Career Intelligence Platform (CCIP).

Your complete project task sheet is located at:
file:///d:/Projects/p1/docs/tasks/task_yash_final.md

Your responsibilities for the final project submission are:
1. Multi-Role Authentication & Session Management:
   - Enforce 5 distinct roles: student, faculty, tpo, admin, recruiter.
   - JWT tokens signed with HMAC-SHA256, bcrypt password hashing, and role-based route guards in backend/app/api/v1/auth.py and backend/app/core/security.py.
   - Multi-role login redirection and single-click demo credential selection in frontend/src/pages/auth/LoginPage.jsx and frontend/src/context/AuthContext.jsx.
   - Session persistence restoring active tokens and mock_role across reloads without fallback resets.
2. Admin Super Panel & Live Telemetry:
   - Real-time /health endpoint in backend/app/main.py returning db.latency_ms, redis.latency_ms, and uptime_seconds.
   - Metrics summary endpoint GET /admin/metrics/summary with dynamically calculated error_rate_24h_percent from AuditLog.
   - Zero-dependency AdminDashboard.jsx adhering to src/index.css design system.
3. Enterprise User Management & Bulk Onboarding:
   - Paginated user directory with role and status toggling in backend/app/api/v1/admin.py and UserManagement.jsx.
   - Single-use password reset token generator (POST /admin/users/{user_id}/generate-reset-link).
   - Bulk CSV user onboarding engine (POST /admin/users/bulk-import) with client-side preview.
4. Global Configuration Persistence:
   - JSON-backed settings engine in backend/system_settings.json for CGPA floor, academic year, and drive limits.
   - Zero-Ant-Design SystemSettings.jsx with instant reactive updates.

Verification Commands to Run:
cd d:\Projects\p1\backend
.\.venv\Scripts\pytest.exe tests/ -k "auth or admin or health" -v
.\.venv\Scripts\pytest.exe -q
cd d:\Projects\p1\frontend
npm run build

Defend in Viva: Explain session token lifecycle, role-based access control (RBAC), and how backend/system_settings.json provides rock-solid settings persistence without database migration overhead.
```

---

### 2️⃣ Prompt for Sachin (Machine Learning & Predictive Intelligence)

```markdown
You are Sachin, Machine Learning & Predictive Intelligence Systems Engineer on the Campus Placement & Career Intelligence Platform (CCIP).

Your complete project task sheet is located at:
file:///d:/Projects/p1/docs/tasks/task_sachin_final.md

Your responsibilities for the final project submission are:
1. Semantic Embedding & Vector Pipeline:
   - Dense 384-dimensional semantic skill embeddings via SentenceTransformer ('all-MiniLM-L6-v2') in backend/app/ml/embeddings.py.
   - Cosine similarity computation matching candidate skill vectors against company job requirements.
   - 152-dimensional combined feature vectors feeding the GradientBoosting / LightGBM regressor (ml/matcher_model.pkl).
   - Deterministic heuristic fallback engine ensuring 100% uptime if ML model weights are absent.
2. Explainable Match Diagnostics:
   - Endpoint GET /matching/students/{student_id}/jobs returning compatibility score P in [0, 100].
   - Diagnostic payload containing matched skills, missing skills, academic score, and diagnostic summary text.
   - Visual MatchDiagnostics.jsx with circular score gauge, skill chip diffs, and readiness advice.
3. Skill Gap Analyzer & Learning Effort Estimator:
   - Endpoint GET /matching/skill-gap/{drive_id} identifying high-impact missing competencies.
   - Estimated study hours calculation based on student's current proficiency level.
   - Actionable learning roadmap linking directly to CCIP Prep Hub resources.
4. Holt's Double Exponential Smoothing for Skill Demand Forecasting:
   - Time-series skill demand forecasting in backend/app/services/forecast_service.py.
   - Classifies industry skills into "Surging", "Stable", or "Declining" across upcoming recruitment cycles.

Verification Commands to Run:
cd d:\Projects\p1\backend
.\.venv\Scripts\pytest.exe tests/ -k "matching or ml or forecast" -v
.\.venv\Scripts\pytest.exe -q
cd d:\Projects\p1\frontend
npm run build

Defend in Viva: Explain the mathematical formulation of Holt's DES (level alpha and trend beta parameters), why 152-dimensional semantic vectors outperform keyword matching, and how the model achieves R^2 = 0.923.
```

---

### 3️⃣ Prompt for Deep (Generative AI & Realtime Services)

```markdown
You are Deep, Generative AI, Realtime & Curriculum Intelligence Systems Engineer on the Campus Placement & Career Intelligence Platform (CCIP).

Your complete project task sheet is located at:
file:///d:/Projects/p1/docs/tasks/task_deep_final.md

Your responsibilities for the final project submission are:
1. Context-Aware AI Career Copilot V3:
   - Token streaming endpoint POST /copilot/chat/stream in backend/app/api/v1/copilot.py using Server-Sent Events (SSE).
   - Dynamic prompt injection inserting student CGPA, department, target role, verified skills, and active placement drives.
   - High-performance local fallback generator if GEMINI_API_KEY is unset or network requests fail.
   - Conversational frontend UI in frontend/src/pages/student/Copilot.jsx with markdown syntax highlighting and action pills.
2. Mock Interview Simulator V2:
   - Multi-turn state machine in backend/app/api/v1/mock_interviews.py (setup -> intro -> technical -> behavioral -> completed).
   - AI response evaluation scoring technical depth, communication clarity, and filler words.
   - Comprehensive post-interview report with actionable tips and radar chart scorecards.
3. Anti-Leakage Smart Assessment Engine:
   - Randomized question delivery engine in backend/app/api/v1/assessments.py with server-side time enforcement.
   - Auto-grading pipeline updating student skill confidence scores upon quiz submission.
4. Board of Studies (BoS) Curriculum Modernization Engine:
   - AI syllabus analyzer in backend/app/api/v1/bos_curriculum.py comparing course syllabi against industry job demand.
   - Generates formal BoS syllabus modernization proposals with proposed topics and rationales.
   - Navigation link integrated in FacultyLayout.jsx and Proposal reviewer in BoSProposals.jsx.

Verification Commands to Run:
cd d:\Projects\p1\backend
.\.venv\Scripts\pytest.exe tests/ -k "copilot or interview or assessment or bos" -v
.\.venv\Scripts\pytest.exe -q
cd d:\Projects\p1\frontend
npm run build

Defend in Viva: Explain how Server-Sent Events (SSE) stream tokens with low latency compared to WebSockets, how system prompt injection personalizes the career copilot, and how the BoS engine automates academic curriculum modernization.
```

---

### 4️⃣ Prompt for Purushottam (TPO Operations & Enterprise Recruiter CRM)

```markdown
You are Purushottam, TPO Operations & Enterprise Recruiter CRM Engineer on the Campus Placement & Career Intelligence Platform (CCIP).

Your complete project task sheet is located at:
file:///d:/Projects/p1/docs/tasks/task_purshottam_final.md

Your responsibilities for the final project submission are:
1. Placement Drive End-to-End Lifecycle:
   - Full drive management endpoints (POST/GET/PATCH /drives) in backend/app/api/v1/drives.py.
   - Multi-criteria eligibility engine enforcing CGPA floor, allowed departments, and maximum backlogs.
   - Application status progression state machine: applied -> shortlisted -> in_progress -> selected / rejected.
   - Interactive drives dashboard in frontend/src/pages/tpo/Drives.jsx.
2. Automated Bulk Shortlisting Engine:
   - Atomic bulk-filtering endpoint POST /drives/{drive_id}/bulk-shortlist in backend/app/api/v1/drives.py.
   - Filter applicants across CGPA, department, and verified skills, promoting eligible candidates in a single query.
   - Filterable student roster in frontend/src/pages/tpo/Students.jsx with batch CSV export.
3. Placement Calendar & Logistics Scheduler:
   - Calendar service in backend/app/api/v1/calendar.py for PPTs, online assessments, and interview slots.
   - Conflict detection engine warning against double-booked company interview schedules.
4. Digital Offer Letter Pipeline & Recruiter CRM:
   - Offer letter release engine (POST /offer-letters/release) in backend/app/api/v1/offer_letters.py.
   - Student accept/decline workflow automatically updating placement status.
   - Dedicated Recruiter Portal (/recruiter/*) with applicant scoring and resume downloads.
5. Institutional Accreditation Engine (NIRF & NAAC):
   - NIRF Metric 1A calculator in backend/app/services/accreditation_service.py computing real higher_studies_count, placement %, and median CTC.
   - Metric 1C sector diversity and NAAC 1.1.3 dossier export in structured JSON/CSV.

Verification Commands to Run:
cd d:\Projects\p1\backend
.\.venv\Scripts\pytest.exe tests/ -k "drives or calendar or offer or accreditation" -v
.\.venv\Scripts\pytest.exe -q
cd d:\Projects\p1\frontend
npm run build

Defend in Viva: Explain the bulk shortlisting query optimization, the database constraints preventing duplicate drive applications, and how the NIRF 1A algorithm calculates median CTC and higher education outcomes.
```

---

### 5️⃣ Prompt for Sakshi (Student Identity & Career Branding)

```markdown
You are Sakshi, Student Identity & Career Branding Systems Engineer on the Campus Placement & Career Intelligence Platform (CCIP).

Your complete project task sheet is located at:
file:///d:/Projects/p1/docs/tasks/task_sakshi_final.md

Your responsibilities for the final project submission are:
1. Rich Portfolio System V2 & Full Lifecycle CRUD:
   - Projects CRUD (POST/GET/PATCH/DELETE /students/me/projects) supporting live URLs, thumbnails, tech stack, and featured pins in backend/app/api/v1/students.py and models/portfolio.py.
   - Internships CRUD with stipend, location, and verified flags.
   - Certifications CRUD with Credly/Coursera credential IDs and verification badges.
   - Multi-tab identity center in frontend/src/pages/student/Profile.jsx.
2. Public Vanity Portfolio & Completeness Calculator:
   - Sanitized unauthenticated public portfolio endpoints (GET /portfolio/{student_id} and GET /portfolio/slug/{custom_slug}) in backend/app/api/v1/portfolio.py.
   - Completeness score engine (0-100%) returning point breakdown and suggestions.
   - Public showcase page in frontend/src/pages/public/PublicPortfolio.jsx.
3. Automated Resume Parser & ATS Compatibility Analyzer:
   - Resume parser service in backend/app/services/resume_parser.py extracting contact info, education, skills, and experience.
   - ATS score analyzer (POST /resume/ats-score) scoring keyword density, structural completeness, and action verbs.
4. Placement Prep Resource Hub:
   - Paginated resources repository in backend/app/api/v1/prep_resources.py with PaginatedResponse metadata (page, page_size, total_items, total_pages).
   - Peer upvoting and thematic collections in frontend/src/pages/student/PrepHub.jsx.
5. Alumni Mentorship Network:
   - Mentor registration, discovery, and session booking endpoints in backend/app/api/v1/alumni.py.
   - Alumni portal in frontend/src/pages/student/Alumni.jsx connecting juniors with placed seniors.

Verification Commands to Run:
cd d:\Projects\p1\backend
.\.venv\Scripts\pytest.exe tests/ -k "portfolio or prep or alumni or resume" -v
.\.venv\Scripts\pytest.exe -q
cd d:\Projects\p1\frontend
npm run build

Defend in Viva: Explain how the public portfolio sanitizer strips private academic data for unauthenticated visitors, how the ATS engine parses resumes against job requirements, and how the alumni mentorship loop fosters peer learning.
```

---

### 6️⃣ Prompt for Anjula (Student Experience & Social Features)

```markdown
You are Anjula, Student Experience & Social Features Systems Engineer on the Campus Placement & Career Intelligence Platform (CCIP).

Your complete project task sheet is located at:
file:///d:/Projects/p1/docs/tasks/task_anjula_final.md

Your responsibilities for the final project submission are:
1. Anonymous Company Reviews & Peer Interview Intelligence:
   - Review submission and insights endpoints in backend/app/api/v1/company_reviews.py.
   - Round-by-round breakdown (OA, Tech 1, Tech 2, HR), difficulty ratings, question tags, and salary transparency.
   - Enforce PaginatedResponse metadata contract (page, page_size, total_items, total_pages).
   - Peer review portal in frontend/src/pages/student/CompanyReviews.jsx with star ratings and upvoting.
2. Application Tracker Timeline & Milestone State Machine:
   - Application tracker and chronological timeline endpoints in backend/app/api/v1/tracker_vault.py.
   - Milestone state machine: applied -> shortlisted -> in_progress -> selected / rejected.
   - Dual-view Kanban board and vertical stepper in frontend/src/pages/student/Applications.jsx.
3. Secure Student Document Vault with TPO Sharing:
   - Document upload, verification, and sharing endpoints in backend/app/api/v1/tracker_vault.py.
   - Strict MIME validation, 10MB file limit, and SHA-256 integrity verification.
   - TPO verification privileges locking documents against tampering.
   - Document vault grid in frontend/src/pages/student/DocumentVault.jsx.
4. Faculty Department Placement Analytics Dashboard:
   - Department placement dashboard endpoints in backend/app/api/v1/faculty.py.
   - Real-time placement percentages, package distributions, and At-Risk student identification.
   - Native CSS dashboard in frontend/src/pages/faculty/Dashboard.jsx with BoS proposals integration.

Verification Commands to Run:
cd d:\Projects\p1\backend
.\.venv\Scripts\pytest.exe tests/ -k "tracker or vault or review or faculty" -v
.\.venv\Scripts\pytest.exe -q
cd d:\Projects\p1\frontend
npm run build

Defend in Viva: Explain how anonymous reviews protect student privacy while maintaining authenticity, how the immutable application timeline prevents illegal state transitions, and how the faculty dashboard surfaces at-risk students for timely intervention.
```

---

## 🛠️ Master Verification Runbook for the Entire Team

Before presenting to examiners, run these commands in the terminal:

```powershell
# 1. Backend Pytest Test Suite Execution (Verify all 179 tests pass)
cd d:\Projects\p1\backend
.\.venv\Scripts\pytest.exe -q

# 2. Frontend Production Bundle Build (Zero errors, ~450ms build time)
cd d:\Projects\p1\frontend
npm run build

# 3. Start Backend Development Server
cd d:\Projects\p1\backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000

# 4. Start Frontend Development Server
cd d:\Projects\p1\frontend
npm run dev
```

---

## 🎯 Final Project Submission Checklist

- [x] All 14 platform audit issues resolved and verified.
- [x] All 179 backend test cases passing with zero regressions.
- [x] Frontend builds cleanly with zero errors and no Ant Design overhead.
- [x] Multi-role login with quick-fill credentials working for all 5 roles.
- [x] Admin system settings persist across server restarts in `backend/system_settings.json`.
- [x] Live backend telemetry enabled (`/health` with DB latency, Redis status, uptime).
- [x] NIRF 1A/1C and NAAC accreditation calculation engine functional with real higher studies data.
- [x] All 6 individual task sheets created in `docs/tasks/`.
- [x] Copy-paste ready prompts prepared for every team member.

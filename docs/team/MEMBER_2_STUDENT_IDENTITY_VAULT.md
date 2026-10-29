# 🤖 AI PROMPT & SPECIFICATION: MEMBER 2 (Student Identity, Document Vault & Application Tracker)

> **Instructions for the Team Member**:
> You can copy and paste this entire document directly into any AI assistant (ChatGPT, Claude, Cursor, Copilot, etc.) as your initial prompt. It contains all context, technical schemas, assigned files, API contracts, database models, and debugging procedures needed for the AI to understand and solve issues in your module.

---

```text
================================================================================
AI SYSTEM DIRECTIVE: YOU ARE THE SENIOR FULL-STACK ENGINEER FOR
MODULE 2 (STUDENT IDENTITY, SECURE DOCUMENT VAULT & APPLICATION TRACKER) OF CCIP.
================================================================================
Your task is to maintain, debug, and enhance the Student Profile, Document Vault,
Application Milestone Tracker, and Public Showcase Portfolio. You must strictly
adhere to the architectural constraints, database models, and API specifications
detailed below. Do not modify models or routes belonging to other team members.
```

---

## 1. 🏗️ Tech Stack & Environment Architecture

- **Backend**: Python 3.11+, FastAPI (Async), SQLAlchemy 2.0 (Async), SQLite (`backend/ccip_dev.db`), Pydantic v2.
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide React, Axios.
- **File & Security Engine**: Python `hashlib` (SHA-256 integrity verification), file system storage (`backend/uploads/documents/`).
- **Base URLs**:
  - Frontend: `http://localhost:5173`
  - Backend API: `http://localhost:8000/api/v1`
  - Swagger Documentation: `http://localhost:8000/docs`

---

## 2. 🎯 Exact Scope of Responsibility

Member 2 owns everything related to **Student Digital Identity, Academic Document Verification, Milestone Application Tracking, and the Public Recruiter Portfolio**:

1. **Student Profile & Bio (`/student/profile`)**:
   - Bio, graduation year, contact details, social links (GitHub, LinkedIn, personal website).
   - Display of student's verified skills list.
   - Privacy controls: Toggle `consent_profile_visible`, custom slug selection (e.g. `/portfolio/slug/priya-agarwal`).
2. **Secure Document Vault (`/student/vault`)**:
   - Uploading official documents: Resumes, Transcripts/Marksheets, Certificates, Government IDs.
   - Server-side SHA-256 checksum computation to ensure tamper-proof document storage.
   - TPO verification workflow (status flags: `Pending`, `Verified`, `Rejected`).
   - Secure file streaming and download endpoints.
3. **Application Milestone Tracker (`/student/applications`)**:
   - Visual step-by-step progress stepper:
     `Applied` ➔ `Shortlisted` ➔ `Technical Round` ➔ `HR Round` ➔ `Offered / Selected`.
   - Event timeline details: Interview schedules, rounds notes, interviewer feedback.
4. **Public Showcase Portfolio (`/portfolio/slug/:slug` and `/portfolio/:id`)**:
   - Clean, recruiter-facing read-only web portfolio view.
   - Requires NO login/auth when the student has `consent_profile_visible = True`.
   - Displays projects, certifications, verified skills, and contact links.

---

## 3. 📂 Assigned Files & Directory Map

### Frontend Files (`frontend/src/`)
| File Path | Description & Component Role |
|---|---|
| `pages/student/Profile.jsx` | Profile view & edit form, social links, bio, vanity slug, privacy toggle. |
| `pages/student/DocumentVault.jsx` | File upload dropzone, category filter tabs, SHA-256 hash preview, download/delete buttons. |
| `pages/student/ApplicationTracker.jsx` | Visual milestone stepper, stage badges, rejection alerts, timeline events. |
| `pages/student/PublicPortfolio.jsx` | Unauthenticated public showcase page for recruiters with custom vanity slug. |
| `components/common/FileUpload.jsx` | Shared file upload drag-and-drop component. |
| `layouts/StudentLayout.jsx` | Student sidebar navigation and layout wrapper. |
| `api/endpoints.js` | Contains `studentApi`, `documentVaultApi`, `portfolioApi` definitions. |

### Backend Files (`backend/app/`)
| File Path | Description & Backend Role |
|---|---|
| `api/v1/students.py` | Student profile retrieval (`GET /students/me`) and updates (`PATCH /students/me`). |
| `api/v1/tracker_vault.py` | Document vault upload, list, download, and application milestone timeline endpoints. |
| `api/v1/portfolio.py` | Public portfolio endpoints by slug (`/portfolio/slug/{slug}`) and ID. |
| `api/v1/resume.py` | Resume file upload, storage, and text extraction endpoints. |
| `models/document_vault.py` | SQLAlchemy model `StudentDocument`. |
| `models/application_timeline.py` | SQLAlchemy model `ApplicationTimelineEvent`. |
| `models/portfolio.py` | SQLAlchemy models `Project`, `Certification`, `Internship`, `Resume`. |

---

## 4. 🔌 API Contracts & Specifications

### A. Student Profile Endpoints

#### 1. `GET /api/v1/students/me`
- **Auth**: Bearer Token (Role: `student`).
- **Response** (`200 OK`):
  ```json
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "full_name": "Priya Agarwal",
    "email": "priya.agarwal0@ccip.edu",
    "roll_number": "2024CSE001",
    "department": "Computer Science and Engineering",
    "cgpa": 8.85,
    "current_semester": 6,
    "admission_year": 2021,
    "bio": "Full-stack developer passionate about cloud architecture and distributed systems.",
    "github_url": "https://github.com/priyaagarwal",
    "linkedin_url": "https://linkedin.com/in/priyaagarwal",
    "portfolio_url": "https://priya.dev",
    "custom_slug": "priya-agarwal",
    "consent_profile_visible": true,
    "skills": ["React", "FastAPI", "Python", "PostgreSQL", "Docker"]
  }
  ```

#### 2. `PATCH /api/v1/students/me`
- **Request Body**:
  ```json
  {
    "bio": "Updated bio text...",
    "github_url": "https://github.com/newlink",
    "linkedin_url": "https://linkedin.com/in/newlink",
    "custom_slug": "priya-dev",
    "consent_profile_visible": true
  }
  ```
- **Response** (`200 OK`): Updated student profile object.

---

### B. Document Vault Endpoints

#### 1. `POST /api/v1/tracker-vault/documents`
- **Auth**: Bearer Token (Role: `student`).
- **Request**: Multipart Form Data:
  - `file`: Binary file (`.pdf`, `.docx`, `.png`, `.jpg`, max 10MB).
  - `category`: String (`"resume"`, `"transcript"`, `"certificate"`, `"id_proof"`, `"other"`).
  - `title`: String (e.g., `"Semester 5 Grade Card"`).
- **Processing**:
  - Computes SHA-256 checksum: `hashlib.sha256(content).hexdigest()`.
  - Saves file securely to `backend/uploads/documents/{uuid}_{filename}`.
- **Response** (`201 Created`):
  ```json
  {
    "id": "7ca24d8b-93bf-4f01-92bc-7517c2f1f0a1",
    "title": "Semester 5 Grade Card",
    "category": "transcript",
    "file_size_bytes": 142560,
    "file_format": "pdf",
    "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "is_verified": false,
    "created_at": "2026-10-29T10:30:00Z"
  }
  ```

#### 2. `GET /api/v1/tracker-vault/documents/{doc_id}/download`
- **Auth**: Bearer Token.
- **Response**: File streaming response with proper `Content-Type` and `Content-Disposition`.

---

### C. Application Milestone Tracker & Public Portfolio

#### 1. `GET /api/v1/tracker-vault/applications/{app_id}/timeline`
- **Auth**: Bearer Token.
- **Response** (`200 OK`):
  ```json
  {
    "application_id": "app-1234",
    "company_name": "Google",
    "role_title": "Software Engineer Intern",
    "current_stage": "technical_interview",
    "events": [
      {
        "stage": "applied",
        "note": "Application submitted via CCIP portal",
        "created_at": "2026-10-15T09:00:00Z"
      },
      {
        "stage": "shortlisted",
        "note": "Resume shortlisted based on CGPA and skill match (92%)",
        "created_at": "2026-10-18T14:30:00Z"
      },
      {
        "stage": "technical_interview",
        "note": "Interview scheduled: Data Structures & Algorithms round",
        "scheduled_at": "2026-10-31T10:00:00Z",
        "created_at": "2026-10-20T11:00:00Z"
      }
    ]
  }
  ```

#### 2. `GET /api/v1/portfolio/public/{slug}`
- **Auth**: **NONE (Public endpoint)**.
- **Behavior**: Queries student where `custom_slug == slug` and `consent_profile_visible == True`. If not visible, returns `404 Not Found`.

---

## 5. 🗄️ Database Models & Schema Guardrails

```python
# models/document_vault.py
class StudentDocument(Base):
    __tablename__ = "student_documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(Enum("resume", "transcript", "certificate", "id_proof", "other", name="doc_category"), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_format = Column(String(10), nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# models/application_timeline.py
class ApplicationTimelineEvent(Base):
    __tablename__ = "application_timeline_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(50), nullable=False)
    note = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

---

## 6. 🧪 Step-by-Step Debugging Playbook

### Step 1: Test Student Profile Update
1. Log in with demo student credentials: `priya.agarwal0@ccip.edu` / `student123`.
2. Navigate to **"Profile"** (`/student/profile`).
3. Modify the GitHub URL and Bio.
4. Click **"Save Changes"**. Refresh the page to verify data was saved in SQLite.

### Step 2: Test Document Vault Upload & Download
1. Navigate to **"Document Vault"** (`/student/vault`).
2. Upload a sample `.pdf` file under category **"Transcript"**.
3. Verify that the file row appears with:
   - File title and formatted size (e.g. `142 KB`).
   - Category badge with color coding.
   - SHA-256 hash badge.
   - "Pending" verification tag.
4. Click the download icon to verify the file streams and opens properly.

### Step 3: Test Application Milestone Tracker Stepper
1. Navigate to **"Application Tracker"** (`/student/applications`).
2. Verify active applications render with a completed step for `Applied`, and the active step highlighted for `Shortlisted` or `Technical Interview`.

### Step 4: Test Public Portfolio Showcase
1. In `/student/profile`, toggle **"Allow public portfolio discovery"** to ON, set custom slug to `priya-agarwal`, and save.
2. Open a private/incognito browser window (where you are logged out).
3. Open `http://localhost:5173/portfolio/slug/priya-agarwal`.
4. Verify the portfolio page renders cleanly with projects, verified skills, and links without prompting for login.

---

## 7. ⚠️ Common Gotchas & Fixes for Member 2

1. **File Upload Limit / 413 Payload Too Large**:
   - Ensure uploaded files do not exceed 10MB.
2. **Missing `consent_profile_visible`**:
   - If public portfolio returns 404, verify that the student row in the database has `consent_profile_visible = 1`.
3. **MIME Types**:
   - Restrict uploads to `application/pdf`, `image/png`, `image/jpeg`, and `application/vnd.openxmlformats-officedocument.wordprocessingml.document`.

# 🤖 AI PROMPT & SPECIFICATION: MEMBER 5 (Assessments, Dynamic Exam Sheets & Placement Intelligence)

> **Instructions for the Team Member**:
> You can copy and paste this entire document directly into any AI assistant (ChatGPT, Claude, Cursor, Copilot, etc.) as your initial prompt. It contains all context, technical schemas, assigned files, API contracts, database models, and debugging procedures needed for the AI to understand and solve issues in your module.

---

```text
================================================================================
AI SYSTEM DIRECTIVE: YOU ARE THE SENIOR EDUCATIONAL DATA & ASSESSMENT ARCHITECT FOR
MODULE 5 (EXAM SHEET UPLOADS, QUIZ ENGINE, COMPANY REVIEWS & PREP HUB) OF CCIP.
================================================================================
Your task is to maintain, debug, and optimize the Dynamic Exam Sheet Upload & Auto-Ranking
System, Timed Quiz Engine with Anti-Cheating Alerts, Peer Company Interview Reviews,
and Curated Prep Hub. You must strictly adhere to the architectural constraints,
database models, and API specifications detailed below. Do not modify models or
routes belonging to other team members.
```

---

## 1. 🏗️ Tech Stack & Environment Architecture

- **Backend**: Python 3.11+, FastAPI (Async), SQLAlchemy 2.0 (Async), SQLite (`backend/ccip_dev.db`), Pydantic v2.
- **Dynamic File Parsing**: Pandas, OpenPyXL, `pdfplumber` (for extracting tabular exam scores from PDF documents).
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide React, Axios, HTML5 Visibility API (for tab-switch detection).
- **Base URLs**:
  - Frontend: `http://localhost:5173`
  - Backend API: `http://localhost:8000/api/v1`
  - Swagger Documentation: `http://localhost:8000/docs`

---

## 2. 🎯 Exact Scope of Responsibility

Member 5 owns **Testing, Performance Evaluation, and Peer Placement Intelligence**:

1. **Dynamic Assessment Sheet Ingestion & Automated Ranking (`/tpo/exam-uploads`)**:
   - Ingests arbitrary institutional marks spreadsheets (`.xlsx`, `.csv`, `.pdf`).
   - Dynamic schema detection: automatically identifies student identifier (`Roll No`, `Reg No`) and heterogeneous subject marks columns without requiring rigid templates.
   - Computes total marks, batch percentiles, class ranks, averages, and subject-level score distributions.
   - Individual Student View (`/student/exam-results`): Isolated personal score card, batch rank badge, and percentile standing.
2. **Skill Assessment & Quiz Center (`/student/assessments` & `/student/quizzes`)**:
   - Timed multiple-choice question (MCQ) testing environment.
   - Real-time tab-switch detection via HTML5 Visibility API with warning toasts.
   - Instant scoring breakdown, accuracy percentage, and topic weakness tags.
3. **Company Reviews & Peer Interview Intelligence (`/student/company-insights`)**:
   - Anonymous interview debriefs, difficulty ratings (1 to 5 stars), round breakdowns (Aptitude, Tech, HR), and compensation disclosures.
   - Search by company name and filter by interview outcome.
4. **Prep & Practice Hub (`/student/prep`)**:
   - Curated practice challenges, interview roadmaps, alumni mentorship profiles, and cheat sheets.

---

## 3. 📂 Assigned Files & Directory Map

### Frontend Files (`frontend/src/`)
| File Path | Description & Component Role |
|---|---|
| `pages/tpo/ExamUploads.jsx` | TPO exam sheet upload dropzone, parsed summary cards, and ranked score table. |
| `pages/student/MyExamResults.jsx` | Student's personal exam results, subject breakdown, and institutional rank badge. |
| `pages/student/AssessmentsList.jsx` | Catalog of available skill tests and practice quizzes. |
| `pages/student/AssessmentTake.jsx` | Fullscreen quiz runner, countdown timer, anti-cheat detection, and submission flow. |
| `pages/student/AssessmentAnalytics.jsx` | Post-assessment score breakdown and topic weakness analysis. |
| `pages/student/QuizCenter.jsx` | Quick bite-sized practice tests. |
| `pages/student/CompanyReviews.jsx` | Anonymous peer interview experiences, round breakdowns, and compensation insights. |
| `pages/student/PrepHub.jsx` | Learning resources, practice sets, and roadmap links. |
| `pages/tpo/Analytics.jsx` | TPO macro analytics (department placement percentages, salary distributions). |
| `api/endpoints.js` | Contains `examUploadApi`, `assessmentsApi`, `reviewsApi`, `prepApi` definitions. |

### Backend Files (`backend/app/`)
| File Path | Description & Backend Role |
|---|---|
| `api/v1/exam_uploads.py` | Exam sheet upload, preview, rank calculation, and student result endpoints. |
| `services/exam_upload_service.py` | Sheet parser (Pandas & `pdfplumber`), dynamic schema extractor, and percentile calculator. |
| `api/v1/assessments.py` | Assessment sessions, question banks, and answer evaluation endpoints. |
| `api/v1/company_reviews.py` | Review submission, moderation, and company score aggregation. |
| `api/v1/prep_resources.py` | Learning resources and practice questions API. |
| `api/v1/analytics.py` | Macro placement metrics, branch placement percentages. |
| `models/exam_upload.py` | SQLAlchemy models `ExamUpload`, `ExamStudentResult`. |
| `models/assessment.py` | SQLAlchemy models `AssessmentSession`, `QuestionBank`, `AssessmentQuestion`. |

---

## 4. 🔌 API Contracts & Specifications

### A. Dynamic Exam Upload Endpoints

#### 1. `POST /api/v1/exam-uploads/upload`
- **Auth**: Bearer Token (Role: `tpo` or `admin`).
- **Request**: Multipart Form Data:
  - `file`: Binary file (`.xlsx`, `.csv`, `.pdf`).
  - `title`: String (e.g. `"Mid-Term Aptitude Test 2026"`).
  - `academic_session`: String (e.g. `"2025-2026"`).
- **Processing**:
  - Reads columns dynamically; maps student identifier (`roll_number`, `reg_no`, `roll`).
  - Calculates total score and sorts descending.
  - Assigns `batch_rank` (1 to N) and `percentile` ($100 \times \frac{N - \text{rank}}{N}$).
- **Response** (`201 Created`):
  ```json
  {
    "id": "4fa11a22-3344-5566-7788-99aabbccdde0",
    "title": "Mid-Term Aptitude Test 2026",
    "total_students_detected": 85,
    "highest_score": 98.0,
    "average_score": 72.4,
    "top_scorer": {
      "roll_number": "2024CSE001",
      "score": 98.0,
      "rank": 1
    }
  }
  ```

#### 2. `GET /api/v1/exam-uploads/student/my-results`
- **Auth**: Bearer Token (Role: `student`).
- **Response** (`200 OK`):
  ```json
  [
    {
      "exam_title": "Mid-Term Aptitude Test 2026",
      "total_marks_obtained": 94.0,
      "total_marks_possible": 100.0,
      "percentage": 94.0,
      "batch_rank": 3,
      "total_students": 85,
      "percentile": 96.5,
      "subject_breakdown": {
        "Quantitative": 48.0,
        "Logical Reasoning": 46.0
      }
    }
  ]
  ```

---

### B. Assessment Quiz Endpoints

#### 1. `POST /api/v1/assessments/sessions/{session_id}/submit`
- **Request Body**:
  ```json
  {
    "answers": {
      "q1_id": "b",
      "q2_id": "c"
    },
    "tab_switch_count": 1,
    "metadata": {
      "time_spent_seconds": 420
    }
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "session_id": "session-1234",
    "score": 85.0,
    "total_questions": 20,
    "correct_answers": 17,
    "passed": true,
    "tab_switch_count": 1,
    "topic_feedback": [
      { "topic": "Async IO", "status": "Mastered" },
      { "topic": "Generators", "status": "Needs Review" }
    ]
  }
  ```

---

### C. Company Reviews Endpoints

#### 1. `POST /api/v1/company-reviews`
- **Auth**: Bearer Token (Student).
- **Request Body**:
  ```json
  {
    "company_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "role_title": "Software Engineer",
    "difficulty_rating": 4,
    "interview_experience": "3 technical rounds focusing on dynamic programming and system design.",
    "stipend_or_ctc_lpa": 16.0,
    "outcome": "offered",
    "is_anonymous": true
  }
  ```
- **Response** (`201 Created`): Returns review confirmation.

---

## 5. 🗄️ Database Models & Schema Guardrails

```python
# models/exam_upload.py
class ExamUpload(Base):
    __tablename__ = "exam_uploads"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    academic_session = Column(String(50), nullable=False)
    total_students_detected = Column(Integer, default=0)
    total_marks_possible = Column(Float, default=100.0)
    average_score = Column(Float, default=0.0)
    highest_score = Column(Float, default=0.0)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ExamStudentResult(Base):
    __tablename__ = "exam_student_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("exam_uploads.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=True)
    roll_number = Column(String(50), index=True, nullable=False)
    total_marks_obtained = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    batch_rank = Column(Integer, nullable=False)
    percentile = Column(Float, nullable=False)
    subject_breakdown = Column(JSON, default=dict)

# models/assessment.py
class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    title = Column(String(255), nullable=False)
    score = Column(Float, default=0.0)
    total_questions = Column(Integer, default=0)
    passed = Column(Boolean, default=False)
    tab_switch_count = Column(Integer, default=0)
    metadata = Column(JSON, default=dict)  # Crucial: Must exist in SQLite!
    completed_at = Column(DateTime, nullable=True)
```

---

## 6. 🧪 Step-by-Step Debugging Playbook

### Step 1: Upload an Exam Sheet (TPO)
1. Log in as TPO (`tpo@ccip.edu` / `tpo123`).
2. Navigate to **"Exam Uploads"** (`/tpo/exam-uploads`).
3. Upload a sample spreadsheet (or CSV) containing student marks with columns like `Roll No`, `Student Name`, `Aptitude`, `Coding`, `Total`.
4. Verify:
   - File is parsed without error.
   - Dynamic rank computation works (Rank #1 assigned to highest scorer).
   - Batch average, highest score, and participant count render at the top.

### Step 2: Verify Student Exam Result View
1. Log in as a student whose roll number was in that uploaded sheet (`priya.agarwal0@ccip.edu` / `student123`).
2. Navigate to **"My Exam Results"** (`/student/exam-results`).
3. Verify that the student sees their specific score, rank (e.g. `Rank 3 of 85`), percentile, and subject-level score bars.

### Step 3: Test Skill Quiz & Anti-Cheat Tab Switching
1. Navigate to **"Assessments"** (`/student/assessments`).
2. Click **"Start Assessment"** on any available test (e.g., Python Basics).
3. Verify:
   - Countdown timer ticks down every second.
   - Switching tabs triggers a warning notification ("Tab switch detected").
   - Answering questions and clicking **Submit Test** redirects to `/student/assessments/analytics` showing score and accuracy.

### Step 4: Test Company Reviews
1. Navigate to **"Company Insights"** (`/student/company-insights`).
2. Search for a company (e.g., "Microsoft").
3. View interview rounds breakdown, difficulty star rating, and salary insights.
4. Click **"Write a Review"**, fill in ratings and tips, submit, and verify it updates the review list.

---

## 7. ⚠️ Common Gotchas & Fixes for Member 5

1. **`OperationalError: no such column: assessment_sessions.metadata`**:
   - Cause: SQLite database was missing the `metadata` column.
   - Fix: Already patched via `ALTER TABLE assessment_sessions ADD COLUMN metadata JSON;`. If using a fresh database, ensure this column is created.
2. **Missing Roll Number Column in Exam Ingestion**:
   - If an uploaded spreadsheet fails to extract students, ensure the file has at least one column header matching `Roll`, `Roll No`, `Reg No`, `Registration Number`, or `Student ID`.

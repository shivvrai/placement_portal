# 🤖 AI PROMPT & SPECIFICATION: MEMBER 3 (ML Job Matching, Skill Gap Engine & Peer Benchmarking)

> **Instructions for the Team Member**:
> You can copy and paste this entire document directly into any AI assistant (ChatGPT, Claude, Cursor, Copilot, etc.) as your initial prompt. It contains all context, technical schemas, assigned files, API contracts, database models, and debugging procedures needed for the AI to understand and solve issues in your module.

---

```text
================================================================================
AI SYSTEM DIRECTIVE: YOU ARE THE SENIOR MACHINE LEARNING & ALGORITHMS ENGINEER FOR
MODULE 3 (JOB MATCHING ENGINE, SKILL GAP ANALYSIS & PEER BENCHMARKING) OF CCIP.
================================================================================
Your task is to maintain, debug, and optimize the Candidate-Job Matching Model,
Skill Gap Deficiency Classifier, Interactive "What-If" Simulator, and Peer Cohort
Benchmarking Engine. You must strictly adhere to the architectural constraints,
database models, and API specifications detailed below. Do not modify models or
routes belonging to other team members.
```

---

## 1. 🏗️ Tech Stack & Environment Architecture

- **Backend**: Python 3.11+, FastAPI (Async), SQLAlchemy 2.0 (Async), SQLite (`backend/ccip_dev.db`), Pydantic v2.
- **Machine Learning & NLP**:
  - `scikit-learn`: Gradient Boosting Regressor ($R^2 \approx 0.923$), Cosine Similarity calculations.
  - `sentence-transformers`: Vector embeddings (`all-MiniLM-L6-v2`) for semantic skill distance and title similarity.
  - `numpy`, `scipy`: Statistical cohort percentile scoring and z-score calculations.
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide React, Axios, Chart.js / Recharts (Radar & Bell Curve charts).
- **Base URLs**:
  - Frontend: `http://localhost:5173`
  - Backend API: `http://localhost:8000/api/v1`
  - Swagger Documentation: `http://localhost:8000/docs`

---

## 2. 🎯 Exact Scope of Responsibility

Member 3 owns the platform's **Intelligence Layer**:

1. **Semantic Candidate-Job Matching Engine (`/student/job-matches`)**:
   - Calculates a weighted match score ($0 - 100\%$) between a student's verified skills and active job descriptions.
   - Computes matching skills vs. missing skills for each job opening.
   - Exposes top candidate recommendations for recruiters/TPOs and top job matches for students.
2. **Skill Gap Engine (`/student/skill-gap`)**:
   - Compares a student's profile against target role requirements.
   - Classifies missing skills by severity:
     - `Critical`: Hard requirement mentioned in >80% of job descriptions.
     - `High`: Core framework/library strongly preferred.
     - `Medium`: Secondary tool or supplementary technology.
     - `Low`: Good-to-have bonus skill.
3. **Interactive "What-If" Skill Simulator**:
   - Allows students to simulate acquiring prospective skills (e.g. checking "Docker" or "AWS").
   - Dynamically recalculates and projects the new match percentage in real-time without writing permanent records to the database.
4. **Peer Cohort Benchmarking (`/student/benchmark`)**:
   - Computes statistical percentiles for students within their department and graduation batch.
   - Renders multi-axis Radar Charts comparing student skill competencies against the cohort average.
   - Displays CGPA bell curves and batch rank percentiles.

---

## 3. 📂 Assigned Files & Directory Map

### Frontend Files (`frontend/src/`)
| File Path | Description & Component Role |
|---|---|
| `pages/student/JobMatches.jsx` | Match cards, circular match score dials, required vs. matched skills breakdown. |
| `pages/student/SkillGap.jsx` | Circular readiness ring, categorized missing skills list with severity pills, "What-If" panel. |
| `pages/student/Benchmark.jsx` | Cohort ranking cards, CGPA distribution curve, Radar chart comparison. |
| `pages/student/Dashboard.jsx` | Student overview dashboard (Readiness stat card, radar snapshot). |
| `components/charts/RadarChart.jsx` | Reusable multi-axis radar chart for skill category visualization. |
| `api/endpoints.js` | Contains `matchingApi` and `skillsApi` definitions. |

### Backend Files (`backend/app/`)
| File Path | Description & Backend Role |
|---|---|
| `api/v1/matching.py` | Routers for `/matching/students/{id}/jobs`, `/matching/my-top-drives`, `/matching/skill-gap`, `/matching/simulate`. |
| `api/v1/skills.py` | Routers for `/skills/taxonomy`, `/skills/search`, `/skills/categories`. |
| `ml/match_engine.py` | ML matching algorithm, feature vectorization, and cosine similarity weighting. |
| `ml/embeddings.py` | Model caching and vector embedding calculations using `sentence-transformers`. |
| `models/skill.py` | SQLAlchemy models `Skill`, `StudentSkill`, `SkillRelationship`. |
| `models/industry.py` | SQLAlchemy models `Company`, `Job`, `JobSkill`. |

---

## 4. 🔌 API Contracts & Specifications

### A. Job Matching Endpoints

#### 1. `GET /api/v1/matching/students/{student_id}/jobs`
- **Response** (`200 OK`):
  ```json
  [
    {
      "job_id": "8fa11a22-3344-5566-7788-99aabbccdde0",
      "job_title": "Full Stack Developer",
      "company_name": "Microsoft",
      "match_score": 88.5,
      "ctc_min_lpa": 14.0,
      "ctc_max_lpa": 18.0,
      "matching_skills": ["Python", "FastAPI", "React", "PostgreSQL"],
      "missing_skills": ["Docker", "Kubernetes"],
      "eligibility": {
        "cgpa_eligible": true,
        "department_eligible": true
      }
    }
  ]
  ```

#### 2. `GET /api/v1/matching/my-top-drives`
- **Auth**: Bearer Token (logged-in student).
- **Response** (`200 OK`): Top placement drives sorted by ML compatibility score for the authenticated student.

---

### B. Skill Gap & "What-If" Simulation Endpoints

#### 1. `GET /api/v1/matching/skill-gap?target_job_id={id}`
- **Auth**: Bearer Token (Student).
- **Response** (`200 OK`):
  ```json
  {
    "target_job_title": "Full Stack Developer",
    "overall_readiness_score": 75.0,
    "missing_skills": [
      {
        "skill_name": "Docker",
        "category": "tool",
        "severity": "Critical",
        "estimated_impact_points": 12.5,
        "recommendation": "Complete the Container Fundamentals module in the Prep Hub."
      },
      {
        "skill_name": "Kubernetes",
        "category": "cloud",
        "severity": "Medium",
        "estimated_impact_points": 6.0,
        "recommendation": "Review container orchestration cheat sheet."
      }
    ]
  }
  ```

#### 2. `POST /api/v1/matching/simulate`
- **Request Body**:
  ```json
  {
    "student_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "target_job_id": "8fa11a22-3344-5566-7788-99aabbccdde0",
    "simulated_skills": ["Docker"]
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "original_score": 75.0,
    "projected_score": 87.5,
    "score_gain": 12.5,
    "remaining_missing_skills": ["Kubernetes"]
  }
  ```

---

### C. Peer Benchmarking Endpoints

#### 1. `GET /api/v1/matching/students/{student_id}/benchmark`
- **Response** (`200 OK`):
  ```json
  {
    "batch_year": 2024,
    "department_name": "Computer Science and Engineering",
    "cgpa_percentile": 88.4,
    "skill_readiness_percentile": 92.1,
    "cohort_rank": 12,
    "total_cohort_size": 150,
    "radar_data": [
      { "category": "Languages", "student_score": 85, "cohort_average": 65 },
      { "category": "Frameworks", "student_score": 90, "cohort_average": 60 },
      { "category": "Databases", "student_score": 80, "cohort_average": 70 },
      { "category": "Cloud & Tools", "student_score": 60, "cohort_average": 55 }
    ]
  }
  ```

---

## 5. 🗄️ Database Models & Schema Guardrails

```python
# models/skill.py
class Skill(Base):
    __tablename__ = "skills"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    normalized_name = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(Enum("language", "framework", "database", "tool", "concept", "cloud", name="skill_category"), nullable=False)

class StudentSkill(Base):
    __tablename__ = "student_skills"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    proficiency = Column(Enum("beginner", "intermediate", "advanced", "expert", name="proficiency_level"), default="intermediate")
    source = Column(Enum("resume", "academic", "project", "certification", "internship", "manual", "assessment", "resume_verified", name="skill_source"), nullable=False)
    is_verified = Column(Boolean, default=False)

# models/industry.py
class Job(Base):
    __tablename__ = "jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    min_cgpa = Column(Float, default=0.0)
    ctc_min_lpa = Column(Float, nullable=True)
    ctc_max_lpa = Column(Float, nullable=True)

class JobSkill(Base):
    __tablename__ = "job_skills"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    is_required = Column(Boolean, default=True)
    weight = Column(Float, default=1.0)
```

---

## 6. 🧪 Step-by-Step Debugging Playbook

### Step 1: Test Job Matches Screen
1. Log in as student (`priya.agarwal0@ccip.edu` / `student123`).
2. Navigate to **"Job Matches"** (`/student/job-matches`).
3. Verify job cards render with match dials (e.g. `88% Match`).
4. Click on a job card to expand the skills breakdown:
   - Green pills = Verified skills the student possesses.
   - Amber/Red pills = Missing required skills.

### Step 2: Test Skill Gap Analysis & What-If Simulator
1. Navigate to **"Skill Gap"** (`/student/skill-gap`).
2. Select target role: "Full Stack Developer".
3. Check the missing skills list: verify each skill displays a severity pill (`Critical`, `High`, etc.).
4. In the **"What-If Simulator"** panel:
   - Check the box next to **"Docker"**.
   - Verify that the simulated readiness score recalculates and increases immediately without reloading.

### Step 3: Test Peer Benchmarking
1. Navigate to **"Peer Benchmark"** (`/student/benchmark`).
2. Verify:
   - Percentile badge displays (e.g., "Top 12% in CSE").
   - Radar chart renders comparing student scores against cohort averages.
   - CGPA bell curve distribution renders without console errors.

---

## 7. ⚠️ Common Gotchas & Fixes for Member 3

1. **`matchingApi.getMyTopDrives is not a function`**:
   - Cause: Method was named `getTopDrives` in `endpoints.js`.
   - Fix: Ensure `endpoints.js` defines `getMyTopDrives: () => api.get('/matching/my-top-drives')`.
2. **Cold-start embedding downloads**:
   - On the first call, `sentence-transformers` downloads weights to `~/.cache/huggingface/hub/`. It runs offline on cached weights subsequently.
3. **Skill Normalization**:
   - Always search and match skills using `.normalized_name` (`token.lower().strip()`) to avoid duplicates like "React" vs "react" or "Node.js" vs "nodejs".

# CCIP — Campus Career & Curriculum Intelligence Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8.2-646CFF?style=flat-square&logo=vite)](https://vitejs.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20+%20pgvector-4169E1?style=flat-square&logo=postgresql)](https://www.postgresql.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://www.python.org)
[![Tests](https://img.shields.io/badge/Tests-76%20Passed-brightgreen?style=flat-square&logo=pytest)](https://pytest.org)
[![Docker](https://img.shields.io/badge/Docker-Compose%20Ready-2496ED?style=flat-square&logo=docker)](https://www.docker.com)

**CCIP** is an AI-powered placement management, skill analytics, and curriculum intelligence platform built for higher education institutions. It unites **Students**, **Training & Placement Officers (TPOs)**, and **Faculty / HODs** into a unified, data-driven ecosystem that bridges the gap between college curricula, student capabilities, and evolving industry hiring demand.

---

## 📌 Table of Contents

- [Key Highlights](#-key-highlights)
- [Role-Based Portals](#-role-based-portals)
  - [🎓 Student Portal](#-student-portal)
  - [💼 TPO Portal](#-tpo-portal)
  - [🏛️ Faculty & HOD Portal](#️-faculty--hod-portal)
- [Intelligent Core Engines](#-intelligent-core-engines)
  - [1. NLP Resume & JD Parsing](#1-nlp-resume--job-description-parsing)
  - [2. Machine Learning Matching & Gap Engine](#2-machine-learning-matching--gap-engine)
  - [3. Streaming AI Career Copilot](#3-streaming-ai-career-copilot)
  - [4. University Management System (UMS) Adapter](#4-university-management-system-ums-adapter)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start Guide](#-quick-start-guide)
  - [Prerequisites](#prerequisites)
  - [Option A: Local Development Setup (Recommended)](#option-a-local-development-setup-recommended)
  - [Option B: Full-Stack Docker Deployment](#option-b-full-stack-docker-deployment)
- [Demo Credentials](#-demo-credentials)
- [API Documentation](#-api-documentation)
- [Running Automated Tests](#-running-automated-tests)
- [Configuration & Environment Variables](#-configuration--environment-variables)
- [License](#-license)

---

## 🚀 Key Highlights

* **Automated Skill Ingestion**: Replaces self-reported student claims with multi-pass NLP extraction from uploaded PDF/DOCX resumes, normalizing terms against a standardized taxonomy.
* **Semantic ML Candidate-Job Matching**: Goes beyond keyword overlap and rigid CGPA cutoffs using a trained Gradient Boosting model combined with Sentence-Transformer embeddings ($R^2 \approx 0.923$).
* **Granular Skill Deficiency Scoring**: Computes per-skill gap metrics with automated severity classification (`Low`, `Medium`, `High`, `Critical`) and an aggregate readiness percentage.
* **Context-Aware Career Copilot**: Real-time streaming career coach powered by Google's Gemini API, dynamically primed with the student's academic history, verified skills, and quantified gap scores.
* **Institutional Curriculum Feedback**: Aggregates live placement and market demand data into curriculum alignment metrics for department heads to modernize course syllabi.
* **Enterprise Interoperability**: Implements an extensible adapter pattern with Celery task queues for scheduled nightly synchronization with institutional University Management Systems (UMS).

---

## 👥 Role-Based Portals

### 🎓 Student Portal
* **Intelligence Dashboard**: Real-time snapshot of profile readiness, interactive skill radar charts, top job matches, severity-classified skill gaps, and upcoming placement drive deadlines.
* **Skill Gap Analyzer**: Visual score ring, current vs. required proficiency bar charts, and prioritized remediation actions.
* **Job Matching Engine**: Tailored job cards with match percentage dials, requirement diff pills (matching vs. missing skills), and direct application submission.
* **Milestone Learning Roadmap**: 4-phase structured timeline with expandable milestones, status toggles, estimated study hours, and curated learning resources.
* **Placement Drive Pipeline**: Drive exploration with eligibility indicators, multi-stage application tracking (`Applied` → `Shortlisted` → `Interview` → `Offered`), and deadline countdowns.
* **Skill Assessments**: Timed topic quizzes across multiple difficulties (Beginner, Intermediate, Advanced) with instant scoring and verified skill credentialing.
* **Profile & Resume Parser**: Multi-tab portfolio manager (Academics, Experience, Projects, Certifications) with one-click resume upload and automated skill extraction.
* **AI Career Copilot**: Interactive chat assistant providing contextual resume tips, interview prep, and tailored study recommendations.

### 💼 TPO Portal
* **Executive KPI Dashboard**: High-level placement statistics, department-wise placement rates, average/median package trends, and recruiter volume.
* **Student Directory**: High-performance searchable directory with multi-criteria filtering (department, minimum CGPA, specific skills, readiness score) and expandable profile modals.
* **Placement Drive Manager**: End-to-end drive lifecycle management (creation, scheduling, eligibility rule enforcement, applicant tracking, and one-click shortlisting).
* **Deep Analytics Suite**: Year-over-Year (YoY) placement comparisons, compensation distribution histograms, sector breakdown, and department benchmarking.

### 🏛️ Faculty & HOD Portal
* **Department Dashboard**: Cohort readiness metrics, department skill radar vs. institutional benchmarks, curriculum coverage donuts, and top missing skill leaderboards.
* **Curriculum Mapping**: Semester-by-semester subject analysis showing syllabus coverage against current industry demand with AI-recommended course adjustments.

---

## 🧠 Intelligent Core Engines

### 1. NLP Resume & Job Description Parsing
* Located in `backend/app/nlp/`
* **Multi-Format Ingestion**: Extracts text from PDF (`pdfplumber`), DOCX (`python-docx`), and plain text with Unicode sanitization.
* **Three-Pass Extraction**: Combines known vocabulary scanning, regular expressions, and spaCy Named Entity Recognition (`en_core_web_sm`).
* **Canonical Normalization**: Uses `rapidfuzz` fuzzy matching to reconcile raw extracted text against canonical skills in the database.
* **Job Description Parser**: Structured extraction of minimum CGPA, salary range, eligible departments, and mandatory vs. optional skills.

### 2. Machine Learning Matching & Gap Engine
* Located in `backend/app/ml/`
* **Semantic Vectorization**: Employs Sentence-Transformers (`all-MiniLM-L6-v2`) to capture semantic relationships between student skills and job requirements.
* **Feature Representation**: Constructs 152-dimensional student-job feature vectors encompassing normalized skill proficiencies and comparative pair features.
* **Gradient Boosting Regressor**: Trained model (`scikit-learn`) predicting candidate-job fit with high accuracy (Test $R^2 = 0.923$, $MAE = 2.56 / 100$), supported by a heuristic fallback.

### 3. Streaming AI Career Copilot
* Located in `backend/app/services/gemini_client.py` and `prompt_builder.py`
* **Dynamic Context Injection**: Constructs real-time prompts containing the student's department, current semester, CGPA, verified skill proficiencies, and computed gap scores.
* **Asynchronous Streaming**: Uses Server-Sent Events (SSE) via FastAPI's `StreamingResponse` for immediate token-by-token output in the React frontend.
* **Robust Fallback**: Includes local offline heuristics when an external API key is not configured.

### 4. University Management System (UMS) Adapter
* Located in `backend/app/adapters/` and `backend/app/services/ums_sync_service.py`
* **Adapter Pattern**: Clean abstract interface (`UMSAdapter`) with pluggable implementations (`MockUMSAdapter`, REST, or direct DB).
* **Nightly Automated Synchronization**: Background synchronization tasks powered by Celery and Redis with an automated 2:00 AM UTC beat schedule.

---

## 🛠️ Architecture & Tech Stack

```
┌─────────────────────────────────────────────────────────────┐
│                 Frontend (React 19 + Vite)                  │
│       Role Portals: Student  │  TPO  │  Faculty / HOD       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / SSE / REST (JWT)
┌──────────────────────────────▼──────────────────────────────┐
│                  Backend API (FastAPI 0.115)                │
│  ┌──────────────┬──────────────┬──────────────┬──────────┐  │
│  │ NLP Pipeline │  ML Matcher  │ Gemini LLM   │ UMS Sync │  │
│  │ (spaCy/Fuzz) │ (GBT + SBERT)│ (Streaming)  │ (Celery) │  │
│  └──────────────┴──────────────┴──────────────┴──────────┘  │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
┌──────────────▼──────────────┐ ┌──────────────▼──────────────┐
│  PostgreSQL 16 / SQLite     │ │     Redis 7 Task Broker     │
│   (30 Relational Tables)    │ │   (Celery Background Jobs)  │
└─────────────────────────────┘ └─────────────────────────────┘
```

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend UI** | React 19, Vite 8, React Router 7 | Responsive single-page application |
| **Styling & Charts** | Vanilla CSS Tokens (Dark Theme), Recharts 3 | High-performance dashboard visualizations |
| **Backend Framework**| Python 3.11, FastAPI, Pydantic v2 | High-concurrency asynchronous REST API |
| **Database & ORM** | PostgreSQL 16 + pgvector / SQLite, SQLAlchemy 2.0 (Async) | Relational persistence & vector embeddings |
| **Task Queue** | Celery 5.4, Redis 7 | Asynchronous jobs & nightly synchronization |
| **NLP & Text Mining** | spaCy 3.8, pdfplumber, python-docx, rapidfuzz | Resume and JD parsing & skill normalization |
| **Machine Learning** | scikit-learn (GradientBoostingRegressor), Sentence-Transformers | Match score prediction & semantic similarity |
| **Generative AI** | Google Gemini API (Streaming) | Context-aware AI Career Copilot |
| **Testing** | pytest, pytest-asyncio, httpx | Automated test suites (76 tests passing) |
| **Containerization** | Docker, Docker Compose | Multi-container orchestration |

---

## 📁 Project Structure

```
p1/
├── backend/
│   ├── alembic/                # Database migration scripts
│   ├── app/
│   │   ├── adapters/           # UMS integration adapters (Mock, REST) & Celery tasks
│   │   ├── api/v1/             # API Routers (Auth, Students, Drives, Matching, Copilot, etc.)
│   │   ├── core/               # App configuration, security (JWT), database engine
│   │   ├── ml/                 # ML matcher, gap engine, feature vectors, embeddings
│   │   ├── models/             # 30 SQLAlchemy ORM models across 9 domain modules
│   │   ├── nlp/                # Resume parser, skill extractor, taxonomy matcher, JD parser
│   │   ├── schemas/            # Pydantic validation schemas
│   │   ├── services/           # Core business logic & Gemini API client
│   │   ├── main.py             # FastAPI entrypoint & router registrations
│   │   └── worker.py           # Celery application & beat schedule configuration
│   ├── scripts/
│   │   └── seed.py             # Comprehensive database seed script (realistic dataset)
│   ├── tests/                  # 5 automated test suites (76 test cases)
│   ├── requirements.txt        # Python backend dependencies
│   └── Dockerfile              # Backend container definition
│
├── frontend/
│   ├── public/
│   │   └── mocks/              # Mock JSON datasets for standalone testing
│   ├── src/
│   │   ├── api/                # Axios client & API endpoint definitions
│   │   ├── context/            # AuthContext (JWT state & user persistence)
│   │   ├── layouts/            # StudentLayout, TPOLayout, FacultyLayout
│   │   ├── pages/
│   │   │   ├── auth/           # Login & Registration pages
│   │   │   ├── student/        # 9 student pages (Dashboard, Gap, Matches, Copilot, etc.)
│   │   │   ├── tpo/            # 4 TPO pages (Dashboard, Students, Drives, Analytics)
│   │   │   └── faculty/        # 2 Faculty pages (Dashboard, Curriculum Map)
│   │   ├── router/             # AppRouter with role-based route guards
│   │   ├── index.css           # Design tokens, dark mode palette, and utility classes
│   │   └── main.jsx            # React root application
│   ├── package.json            # Node.js dependencies & scripts
│   └── vite.config.js          # Vite configuration
│
├── data/                       # Taxonomy seeds, job descriptions & evaluation sets
├── docker-compose.yml          # Multi-service container specification
└── README.md                   # Project documentation
```

---

## ⚡ Quick Start Guide

### Prerequisites
- **Node.js** (v18.0 or higher) & **npm**
- **Python** (v3.11 or higher)
- **Docker & Docker Compose** *(optional, required for containerized deployment)*

---

### Option A: Local Development Setup (Recommended)

#### 1. Backend Setup
Navigate to the `backend` directory, create a virtual environment, and install dependencies:

```bash
cd backend

# Create and activate virtual environment
# Windows:
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux:
# python3 -m venv .venv
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy NLP model
python -m spacy download en_core_web_sm
```

#### 2. Environment Configuration
Verify or adjust `backend/.env` (defaults to local SQLite for fast zero-configuration setup):

```env
APP_NAME="CCIP - Campus Career & Curriculum Intelligence Platform"
DATABASE_URL=sqlite+aiosqlite:///./ccip_dev.db
SECRET_KEY=dev-secret-key-change-in-production-32-chars-min
GEMINI_API_KEY=your_gemini_api_key_here  # Optional: Leave empty for offline fallback
```

#### 3. Populate Database (Seed Script)
Initialize the database with complete demo departments, skills, companies, jobs, placement drives, assessment questions, and student records:

```bash
python -m scripts.seed
```

#### 4. Run the Backend Server
Start the FastAPI server with hot-reload enabled:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
* **API Base URL**: `http://localhost:8000`
* **Interactive Swagger UI**: `http://localhost:8000/docs`
* **Alternative ReDoc UI**: `http://localhost:8000/redoc`

#### 5. Frontend Setup
Open a new terminal window, navigate to `frontend`, install packages, and start the development server:

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
* **Frontend Application**: `http://localhost:5173`

---

### Option B: Full-Stack Docker Deployment

To launch the complete containerized stack (PostgreSQL with `pgvector`, Redis, FastAPI Backend, Celery Worker, and React Frontend):

```bash
docker compose up --build
```

Services will be available at:
* **Frontend Web App**: `http://localhost:5173`
* **FastAPI Backend**: `http://localhost:8000` (`/docs` for API documentation)
* **PostgreSQL Database**: `localhost:5432`
* **Redis Instance**: `localhost:6379`

---

## 🔑 Demo Credentials

For quick testing and evaluation, the database is pre-seeded with accounts for each role. You can use the **Quick Fill Demo Credentials** dropdown directly on the login screen (`/login`) or enter the credentials below:

| Role | Name | Email | Password | Access Portal |
|---|---|---|---|---|
| **Student** | Priya Agarwal | `priya.agarwal0@ccip.edu` | `student123` | `/student/dashboard` |
| **TPO / Admin** | Admin TPO | `tpo@ccip.edu` | `tpo123` | `/tpo/dashboard` |
| **Faculty / HOD**| Dr. Sharma | `faculty@ccip.edu` | `faculty123` | `/faculty/dashboard` |

*(Additional students in various departments are available: `arjun.sharma1@ccip.edu`, `sneha.reddy2@ccip.edu`, etc., all with password `student123`)*

---

## 📖 API Documentation

FastAPI automatically generates interactive OpenAPI documentation:
* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Primary API Route Groups

| Tag | Prefix | Description |
|---|---|---|
| `Authentication` | `/api/v1/auth` | User registration, JWT login, token refresh, and `/me` profile |
| `Students` | `/api/v1/students` | Student profile CRUD, academic marks, skills, and privacy consent |
| `Drives` | `/api/v1/drives` | Placement drive creation, listing, details, and shortlisting queries |
| `Applications` | `/api/v1/applications`| Job application submission and student pipeline status |
| `Matching & Gaps` | `/api/v1/matching`, `/api/v1/gaps` | ML-driven job match scores, skill gap severity analysis |
| `Roadmap` | `/api/v1/roadmap` | Personalized learning roadmap generation and task status updates |
| `Analytics` | `/api/v1/analytics`| Department benchmarks, placement stats, and market skill demand |
| `Copilot` | `/api/v1/copilot` | AI career coach conversation management and streaming chat |
| `Resume` | `/api/v1/resume` | Resume file upload, parsing status, and skill extraction trigger |
| `Assessments` | `/api/v1/assessments` | Dynamic quiz questions, exam submission, and score calculation |
| `UMS` | `/api/v1/ums` | University Management System synchronization endpoints and logs |
| `Skills` | `/api/v1/skills` | Canonical skill taxonomy lookup and search |

---

## 🧪 Running Automated Tests

CCIP includes an automated test suite with **76 tests** covering API authentication, student records, UMS synchronization, ML matching, and skill assessments.

To run the tests:

```bash
cd backend

# Run all test suites
pytest

# Run with verbose output
pytest -v

# Run a specific test suite
pytest tests/test_matching.py
```

### Test Suite Summary
* `tests/test_auth.py` — Registration, authentication, token issuance, and protected routes.
* `tests/test_students.py` — Student profile updates, skill management, and academic records.
* `tests/test_matching.py` — Feature vector generation, ML gap calculations, and severity ratings.
* `tests/test_ums.py` — UMS adapter contract, data synchronization logic, and error handling.
* `tests/test_assessments.py` — Question bank querying, test submission, and score verification.

---

## ⚙️ Configuration & Environment Variables

### Backend Configuration (`backend/.env`)

| Variable | Default Value | Description |
|---|---|---|
| `APP_NAME` | `"CCIP - Campus Career & ..."` | Application display name |
| `DATABASE_URL` | `sqlite+aiosqlite:///./ccip_dev.db` | Database connection string (PostgreSQL or SQLite) |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Secret key for JWT signing (HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| `60` | JWT access token validity period |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token validity period |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis broker URL for Celery worker and caching |
| `UMS_MODE` | `mock` | UMS adapter mode (`mock`, `api`, or `etl`) |
| `GEMINI_API_KEY` | `""` | Google Gemini API key for streaming AI Copilot |
| `UPLOAD_DIR` | `./uploads` | Directory for uploaded student resumes |
| `MAX_RESUME_SIZE_MB` | `10` | Maximum resume file size limit in megabytes |
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:5173"]` | Allowed CORS origins for frontend access |

### Frontend Configuration (`frontend/.env`)

| Variable | Default Value | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000/api/v1` | Backend REST API base endpoint |
| `VITE_USE_MOCKS` | `false` | Fallback to mock JSON responses if backend is unreachable |

---

## 📄 License & Copyright

Copyright (c) 2026 shivvrai. All rights reserved.

This project and all associated source code, designs, and documentation are **Proprietary and Confidential**. Unauthorized copying, distribution, modification, reverse engineering, or commercial use of this software, in whole or in part, is strictly prohibited without prior written consent from the copyright holder. See the [LICENSE](LICENSE) file for complete terms.

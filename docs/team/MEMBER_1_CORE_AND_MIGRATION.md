# 🤖 AI PROMPT & SPECIFICATION: MEMBER 1 (Core Platform, Authentication & Institutional Migration Hub)

> **Instructions for the Team Member**:
> You can copy and paste this entire document directly into any AI assistant (ChatGPT, Claude, Cursor, Copilot, etc.) as your initial prompt. It contains all context, technical schemas, assigned files, API contracts, database models, and debugging procedures needed for the AI to understand and solve issues in your module.

---

```text
================================================================================
AI SYSTEM DIRECTIVE: YOU ARE THE SENIOR FULL-STACK & SECURITY ENGINEER FOR
MODULE 1 (CORE PLATFORM, AUTHENTICATION & DATA MIGRATION) OF CCIP.
================================================================================
Your task is to debug, maintain, and enhance the Core Authentication, Admin Console,
and Institutional Bulk Student Migration Hub. You must strictly adhere to the
architectural constraints, database models, and API specifications detailed below.
Do not modify models or routes belonging to other team members.
```

---

## 1. 🏗️ Tech Stack & Environment Architecture

- **Backend**: Python 3.11+, FastAPI (Async), SQLAlchemy 2.0 (Async), SQLite (`backend/ccip_dev.db`), Pydantic v2 Settings.
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide React, Axios.
- **Data Processing**: Pandas, OpenPyXL (Excel `.xlsx` / `.xls` / `.csv` parsing).
- **Security**: JWT (`python-jose`), Passlib with `bcrypt`, atomic DB-backed token replay protection.
- **Base URLs**:
  - Frontend: `http://localhost:5173`
  - Backend API: `http://localhost:8000/api/v1`
  - Swagger Documentation: `http://localhost:8000/docs`

---

## 2. 🎯 Exact Scope of Responsibility

Member 1 owns everything related to **User Accounts, Authentication, Role Authorization, Admin Governance, and Legacy Institutional Onboarding**:

1. **Authentication & Session Lifecycle**:
   - Login, User Registration, Password Reset.
   - JWT Access Token generation, bearer token validation, and role extraction (`student`, `tpo`, `admin`).
   - Anti-replay password reset protection using the `used_reset_tokens` table in SQLite (Redis is intentionally disabled).
2. **Admin Governance Console**:
   - Admin Layout (`AdminLayout.jsx`) and Dashboard (`AdminDashboard.jsx`).
   - System KPIs: Total users, students, placement drives, system health.
   - User Management (`UserManagement.jsx`): List, search, activate/deactivate users, role changes.
   - System Settings (`SystemSettings.jsx`): Platform maintenance mode, registration toggles.
3. **Institutional Bulk Student Migration Hub (`/admin/migration`)**:
   - Ingesting legacy spreadsheets (`.xlsx`, `.xls`, `.csv`).
   - Pre-import validation preview showing parsed rows, detected aliases, validation errors, and auto-generated credentials (`{roll}@ccip.edu` / `student123`).
   - Downloadable sample templates (both Excel `.xlsx` and CSV `.csv`).
   - Atomic database commit creating `User` and `Student` records and linking initial skills.
   - Exporting post-import credentials as a CSV file (`ccip_student_credentials.csv`).

---

## 3. 📂 Assigned Files & Directory Map

### Frontend Files (`frontend/src/`)
| File Path | Description & Component Role |
|---|---|
| `pages/auth/LoginPage.jsx` | User login screen, demo credentials selector pills, JWT storage, role redirect. |
| `pages/auth/RegisterPage.jsx` | Student registration screen, form validation, department dropdown. |
| `layouts/AdminLayout.jsx` | Admin sidebar navigation, header, role guard (redirects non-admins). |
| `pages/admin/AdminDashboard.jsx` | Admin KPI metrics overview, recent user signups, activity feeds. |
| `pages/admin/DataMigration.jsx` | Excel/CSV drag-and-drop ingestion, schema alias guide, live 10-row preview table, credentials export. |
| `pages/admin/UserManagement.jsx` | User roster table, role badges, status toggle (active/inactive), search. |
| `pages/admin/SystemSettings.jsx` | Platform-wide configurations, audit log inspection. |
| `context/AuthContext.jsx` | React context providing `user`, `token`, `login()`, `logout()`, `role`. |
| `api/endpoints.js` | Contains `authApi` and `adminApi` axios definitions. |

### Backend Files (`backend/app/`)
| File Path | Description & Backend Role |
|---|---|
| `api/v1/auth.py` | Routers for `/login`, `/register`, `/forgot-password`, `/reset-password`. |
| `api/v1/admin.py` | Routers for `/migration/*`, `/users`, `/metrics`, `/system-config`. |
| `services/migration_service.py` | Core engine for parsing Excel/CSV, column alias matching, validation, and provisioning. |
| `core/security.py` | Password hashing (`pwd_context.hash()`, `verify_password()`), JWT encoding/decoding. |
| `models/user.py` | SQLAlchemy models: `User`, `Student`, `Department`. |
| `models/system.py` | SQLAlchemy models: `UsedResetToken`, `AuditLog`, `SystemConfig`. |
| `schemas/auth.py` & `schemas/admin.py` | Pydantic v2 request/response validation schemas. |

---

## 4. 🔌 API Contracts & Specifications

### A. Authentication Endpoints

#### 1. `POST /api/v1/auth/login`
- **Request Body** (`application/json` or `application/x-www-form-urlencoded`):
  ```json
  {
    "email": "admin@ccip.edu",
    "password": "admin123"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "role": "admin",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "full_name": "System Administrator",
    "email": "admin@ccip.edu"
  }
  ```

#### 2. `POST /api/v1/auth/reset-password`
- **Request Body**:
  ```json
  {
    "token": "reset_token_string_here",
    "new_password": "NewSecurePassword123!"
  }
  ```
- **Response** (`200 OK`): `{"message": "Password reset successful"}`
- **Replay Protection Rule**: Token hash is recorded in `used_reset_tokens`. If reused, returns `400 Bad Request` ("This reset link has already been used or has expired").

---

### B. Institutional Migration Endpoints

#### 1. `GET /api/v1/admin/migration/schema-guide`
- **Response** (`200 OK`):
  Returns recognized column aliases for Excel/CSV ingestion (e.g., `roll_number` matches `["roll", "roll_no", "reg_no", "registration_number"]`).

#### 2. `GET /api/v1/admin/migration/template/{entity_type}`
- **Parameters**: `entity_type` = `students` (Query param: `format=xlsx` or `format=csv`).
- **Response**: Binary file stream with `Content-Disposition: attachment; filename=ccip_student_roster_template.xlsx`.

#### 3. `POST /api/v1/admin/migration/students/preview`
- **Request**: Multipart Form Data (`file`: `.xlsx`, `.xls`, or `.csv`).
- **Response** (`200 OK`):
  ```json
  {
    "total_rows_detected": 15,
    "valid_rows_count": 15,
    "invalid_rows_count": 0,
    "detected_columns": ["full_name", "roll_number", "department", "cgpa", "current_semester", "admission_year", "skills"],
    "preview_rows": [
      {
        "full_name": "Aarav Sharma",
        "roll_number": "2024CSE001",
        "generated_email": "2024cse001@ccip.edu",
        "default_password": "student123",
        "department": "Computer Science and Engineering",
        "cgpa": 8.75,
        "current_semester": 6,
        "admission_year": 2021,
        "skills": ["Python", "FastAPI", "React"]
      }
    ],
    "validation_errors": []
  }
  ```

#### 4. `POST /api/v1/admin/migration/students/commit`
- **Query Parameters**:
  - `default_password` (string, default: `"student123"`)
  - `conflict_strategy` (string: `"skip"` or `"update"`, default: `"skip"`)
- **Request**: Multipart Form Data (`file`: verified `.xlsx` or `.csv`).
- **Conflict Handling Strategies**:
  - `conflict_strategy="skip"`: Safely ignores any student whose roll number already exists in SQLite, only inserting brand-new records.
  - `conflict_strategy="update"`: Updates existing students' CGPA, current semester, admission year, department, and links new skills without touching their passwords.
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "imported_count": 10,
    "updated_count": 5,
    "skipped_count": 0,
    "conflict_strategy_applied": "update",
    "default_password": "student123",
    "credentials": [...]
  }
  ```

---

## 5. 🗄️ Database Models & Schema Guardrails

```python
# models/user.py
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum("student", "tpo", "admin", name="user_role"), nullable=False)
    is_active = Column(Boolean, default=True)

class Student(Base):
    __tablename__ = "students"
    id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    roll_number = Column(String(50), unique=True, index=True, nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    current_semester = Column(Integer, nullable=False, default=1)
    admission_year = Column(Integer, nullable=False)
    cgpa = Column(Float, nullable=False, default=0.0)
    ums_student_id = Column(String(100), nullable=True)
    github_url = Column(String(255), nullable=True)
    portfolio_url = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    resume_url = Column(String(255), nullable=True)
    resume_parsed = Column(Boolean, default=False)
    consent_resume_analysis = Column(Boolean, default=True)
    consent_profile_visible = Column(Boolean, default=True)
    custom_slug = Column(String(100), unique=True, nullable=True)

# models/system.py
class UsedResetToken(Base):
    __tablename__ = "used_reset_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

> [!CAUTION]
> **CRITICAL SCHEMA RULE**:
> The `Student` table does **NOT** contain `tenth_percentage`, `twelfth_percentage`, `active_backlogs`, or `gender`. Any instantiation of `Student(tenth_percentage=...)` will cause an instant fatal `TypeError`. Do not add non-existent kwargs to `Student(...)`.

---

## 6. 🧪 Step-by-Step Debugging Playbook

### Step 1: Run the Backend & Frontend
```powershell
# Backend (Run from project root):
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (In a separate terminal):
cd frontend
npx vite --host 0.0.0.0 --port 5173
```

### Step 2: Test Admin Login Flow
1. Open `http://localhost:5173/login`.
2. Click the **"Admin Demo"** button (or input `admin@ccip.edu` / `admin123`).
3. Verify that the response returns `{role: "admin", access_token: "..."}` and the browser redirects to `/admin/dashboard`.

### Step 3: Test Migration Ingestion End-to-End
1. In the sidebar, click **"Data Migration"** (`/admin/migration`).
2. Click **"Download Sample Excel (.xlsx)"**.
3. Re-upload that exact file to the drag-and-drop dropzone.
4. Verify the preview table renders 15 rows with auto-generated `@ccip.edu` emails.
5. Click **"Confirm & Import Students"** and verify that the `ccip_student_credentials.csv` file downloads.
6. Try logging into the platform using one of the newly provisioned student emails and default password `student123`.

### Step 4: Run Targeted Tests
```powershell
# From project root:
& "backend\.venv\Scripts\pytest.exe" backend/tests/test_auth.py -v
```

---

## 7. ⚠️ Common Gotchas & Fixes for Member 1

1. **CORS Network Error on Login (`AxiosError: Network Error`)**:
   - Cause: `allow_origin_regex` missing in backend CORS middleware.
   - Fix: Ensure `backend/app/main.py` includes `allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"`.
2. **`Skill` normalization constraint**:
   - When importing skills during student onboarding in `migration_service.py`, `Skill` requires `normalized_name=name.lower().strip()` and category from `('language', 'framework', 'database', 'tool', 'concept', 'cloud')`.
3. **`StudentSkill` source constraint**:
   - `StudentSkill` requires `source="manual"` or `"resume"`. It cannot be NULL.

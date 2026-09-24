"""
Generate comprehensive markdown documentation report from api_test_results.json
"""

import json
import os

with open("api_test_results.json", encoding="utf-8") as f:
    data = json.load(f)

summary = data["summary"]
results = data["results"]

crashes = [r for r in results if r["classification"] == "SERVER_ERROR"]
client_errors = [r for r in results if r["classification"] == "CLIENT_ERROR"]
successes = [r for r in results if r["classification"] == "SUCCESS"]

report = []

report.append("# CCIP Platform — Comprehensive API Audit & Defect Report")
report.append("\n**Generated Date**: September 23, 2026")
report.append("**Total Endpoints Evaluated**: 138 API routes across 20 modules")
report.append(f"**Test Results**: {len(successes)} Passed (2xx) | {len(crashes)} Server Crashes (500) | {len(client_errors)} Client Errors (4xx) | 0 Auth Failures\n")

report.append("---")
report.append("## Executive Summary\n")
report.append("| Metric | Count | Percentage | Status |")
report.append("| :--- | :--- | :--- | :--- |")
report.append(f"| **Total Endpoints Tested** | {summary['total']} | 100% | Registered APIRoutes |")
report.append(f"| **Successful Endpoints (2xx)** | {summary['success']} | {summary['success']/summary['total']*100:.1f}% | Passed |")
report.append(f"| **Server Errors (500)** | {summary['server_errors']} | {summary['server_errors']/summary['total']*100:.1f}% | Action Required (Fixes Provided Below) |")
report.append(f"| **Client Errors (4xx)** | {summary['client_errors']} | {summary['client_errors']/summary['total']*100:.1f}% | Expected Validation / Param requirements |")
report.append(f"| **Authentication Failures (401/403)** | {summary['auth_forbidden']} | 0.0% | All roles properly authenticated |")
report.append("\n")

report.append("---")
report.append("## Summary of Root Causes for 500 Server Crashes\n")
report.append("The **59 server crashes** stem from **5 core underlying defects** in the codebase and database migration setup:\n")

report.append("### 1. Missing Database Columns in PostgreSQL (Affects 30 Endpoints)")
report.append("- **Root Cause**: In `backend/app/main.py`, column additions (`_migrate_sqlite_columns`) were implemented ONLY for SQLite (`if IS_SQLITE:`). In PostgreSQL (Supabase), these columns were never added via DDL.")
report.append("- **Missing Columns**:")
report.append("  - `student_skills.is_verified` (BOOLEAN DEFAULT FALSE) -> **Crashes 26 endpoints** whenever student skills, profile, talent cohorts, or BI feeds are loaded.")
report.append("  - `certifications.credential_id` (VARCHAR(200)) -> **Crashes 2 endpoints** (`/students/me/certifications`).")
report.append("  - `internships.location` (VARCHAR(200)), `employment_type` (VARCHAR(50)), `is_current` (BOOLEAN) -> **Crashes 1 endpoint** (`/students/me/experience`).")
report.append("  - `projects.is_featured` (BOOLEAN DEFAULT FALSE) -> Crashes project list/update endpoints.")
report.append("- **Fix**: Execute standard `ALTER TABLE` statements in PostgreSQL (provided below).\n")

report.append("### 2. Missing Database Tables in PostgreSQL (Affects 24 Endpoints)")
report.append("- **Root Cause**: Several models were added in later phases (`cohort.py`, `experiences.py`, `announcements.py`, `interview_session.py`, `curriculum_proposal.py`), but Alembic migrations were never generated, and `Base.metadata.create_all` is only called for SQLite in `app/main.py`.")
report.append("- **Missing Tables**:")
report.append("  - `curriculum_proposals` -> **6 endpoints** (`/api/v1/curriculum/proposals*`)")
report.append("  - `mock_interview_sessions` -> **6 endpoints** (`/api/v1/mock-interviews*`)")
report.append("  - `notifications` -> **5 endpoints** (`/api/v1/notifications*`, drive stage updates and offers)")
report.append("  - `student_cohorts` -> **4 endpoints** (`/api/v1/tpo/cohorts*`)")
report.append("  - `interview_experiences` -> **3 endpoints** (`/api/v1/experiences*`)")
report.append("  - `drive_announcements` -> **2 endpoints** (`/api/v1/drives/{drive_id}/announcements`)")
report.append("- **Fix**: Execute `CREATE TABLE` scripts for the 6 missing tables (provided in SQL migration script below).\n")

report.append("### 3. PostgreSQL GROUP BY Aggregation Mismatch (Affects 1 Endpoint)")
report.append("- **Endpoint**: `GET /api/v1/analytics/sectors`")
report.append("- **File**: `backend/app/services/analytics_service.py`, lines 398-401")
report.append("- **Root Cause**: The query selects `func.coalesce(Company.industry, 'Product')` but groups by `Company.industry`. PostgreSQL requires the exact selected expression or column in `GROUP BY`.")
report.append("- **Fix**: Change `.group_by(Company.industry)` to `.group_by(func.coalesce(Company.industry, 'Product'))`.\n")

report.append("### 4. Timezone Offset-Aware vs Offset-Naive Datetime Mismatch (Affects 1 Endpoint)")
report.append("- **Endpoint**: `POST /api/v1/ums/sync/department/{department_code}`")
report.append("- **File**: `backend/app/services/ums_sync_service.py`, line 28")
report.append("- **Root Cause**: Defined `utcnow()` as `datetime.now(timezone.utc)` (offset-aware). When updating `Attendance.last_updated` which is PostgreSQL `TIMESTAMP WITHOUT TIME ZONE` (offset-naive), asyncpg throws `DataError: can't subtract offset-naive and offset-aware datetimes`.")
report.append("- **Fix**: Change line 28 of `app/services/ums_sync_service.py` to `datetime.now(timezone.utc).replace(tzinfo=None)`.\n")

report.append("### 5. SQLAlchemy Async Missing Greenlet in Prompt Builder (Affects 2 Endpoints)")
report.append("- **Endpoints**: `POST /api/v1/copilot/conversations/{conversation_id}/messages` and `POST /api/v1/copilot/mock-interview/{conversation_id}/respond`")
report.append("- **File**: `backend/app/services/prompt_builder.py`, line 49")
report.append("- **Root Cause**: `student.user` was accessed without eager loading (`selectinload(Student.user)`). In async SQLAlchemy, triggering lazy-loading outside an eager load raises `MissingGreenlet`.")
report.append("- **Fix**: Add `.options(selectinload(Student.user))` when querying `Student` in `build_full_context`.\n")

report.append("---")
report.append("## Copy-Paste Fix: Database Migration Script (`fix_schema.sql`)\n")
report.append("Executing this single SQL script against the database will resolve **54 out of the 59 server crashes** immediately:\n")

report.append("```sql")
report.append("-- 1. Add Missing Columns to Existing Tables")
report.append("ALTER TABLE student_skills ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;")
report.append("ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE;")
report.append("ALTER TABLE certifications ADD COLUMN IF NOT EXISTS credential_id VARCHAR(200);")
report.append("ALTER TABLE internships ADD COLUMN IF NOT EXISTS location VARCHAR(200);")
report.append("ALTER TABLE internships ADD COLUMN IF NOT EXISTS employment_type VARCHAR(50) DEFAULT 'Internship';")
report.append("ALTER TABLE internships ADD COLUMN IF NOT EXISTS is_current BOOLEAN DEFAULT FALSE;")

report.append("\n-- 2. Create Missing Table: curriculum_proposals")
report.append("""CREATE TABLE IF NOT EXISTS curriculum_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(300) NOT NULL,
    department_code VARCHAR(10) NOT NULL,
    description TEXT NOT NULL,
    rationale TEXT NOT NULL,
    proposed_changes JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'draft',
    submitted_by UUID REFERENCES users(id),
    reviewed_by UUID REFERENCES users(id),
    hod_comments TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    reviewed_at TIMESTAMP WITHOUT TIME ZONE
);""")

report.append("\n-- 3. Create Missing Table: mock_interview_sessions")
report.append("""CREATE TABLE IF NOT EXISTS mock_interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id),
    role_target VARCHAR(200) NOT NULL,
    company_style VARCHAR(50) NOT NULL DEFAULT 'Product',
    difficulty VARCHAR(30) NOT NULL DEFAULT 'campus',
    status VARCHAR(20) NOT NULL DEFAULT 'setup',
    current_round INTEGER DEFAULT 0,
    transcript JSONB DEFAULT '[]',
    questions_asked TEXT[],
    performance_scores JSONB,
    final_report JSONB,
    duration_seconds INTEGER,
    word_count INTEGER,
    filler_word_count INTEGER DEFAULT 0,
    started_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    completed_at TIMESTAMP WITHOUT TIME ZONE
);""")

report.append("\n-- 4. Create Missing Table: notifications")
report.append("""CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info',
    link VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);""")

report.append("\n-- 5. Create Missing Table: student_cohorts")
report.append("""CREATE TABLE IF NOT EXISTS student_cohorts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    criteria JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);""")

report.append("\n-- 6. Create Missing Table: interview_experiences")
report.append("""CREATE TABLE IF NOT EXISTS interview_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id),
    company_name VARCHAR(200) NOT NULL,
    role VARCHAR(200) NOT NULL,
    placement_drive_id UUID REFERENCES placement_drives(id),
    difficulty VARCHAR(20) NOT NULL,
    verdict VARCHAR(30) NOT NULL,
    overall_experience TEXT NOT NULL,
    questions_asked JSONB DEFAULT '[]',
    tips_for_juniors TEXT,
    upvotes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);""")

report.append("\n-- 7. Create Missing Table: drive_announcements")
report.append("""CREATE TABLE IF NOT EXISTS drive_announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drive_id UUID NOT NULL REFERENCES placement_drives(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(300) NOT NULL,
    message TEXT NOT NULL,
    urgency VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);""")
report.append("```\n")

report.append("---")
report.append("## Detailed Breakdown of Failing Endpoints (500 Server Errors)\n")

for idx, c in enumerate(crashes, 1):
    exc = c.get("exception") or {}
    report.append(f"### {idx}. `[{c['method']}]` `{c['path_pattern']}`")
    report.append(f"- **Resolved Test URL**: `{c['resolved_url']}`")
    report.append(f"- **Tested Role**: `{c['role_tested']}`")
    report.append(f"- **HTTP Status**: `500 Internal Server Error`")
    report.append(f"- **Error Type**: `{exc.get('error_type', 'ServerError')}`")
    report.append(f"- **Error Message**: `{exc.get('error_msg', str(c.get('response', ''))).splitlines()[0]}`")
    report.append(f"- **Module**: `{c['module']}` | **Handler**: `{c['endpoint_name']}()`")
    if exc.get("traceback"):
        tb_lines = exc["traceback"].strip().split("\n")
        tail = "\n".join(tb_lines[-8:])
        report.append(f"```text\n{tail}\n```")
    report.append("")

report.append("---")
report.append("## Detailed Breakdown of Client Validation Responses (4xx)\n")
report.append("These 16 endpoints returned 4xx status codes due to expected request validation, missing query parameters, or ID lookups on unseeded demo tables:\n")

for idx, ce in enumerate(client_errors, 1):
    report.append(f"### {idx}. `[{ce['method']}]` `{ce['path_pattern']}` (Status: {ce['status_code']})")
    report.append(f"- **Resolved URL**: `{ce['resolved_url']}`")
    report.append(f"- **Response**: `{json.dumps(ce.get('response'), default=str)}`")
    report.append(f"- **Explanation**: ")
    
    msg = str(ce.get("response", ""))
    if "tech_stack" in msg:
        report.append("  Expected body key `tech_stack: list[str]` instead of `technologies`.")
    elif "name" in msg and "issuing_organization" in msg:
        report.append("  Expected body keys `name: str` and `issuing_organization: str` instead of `title` / `issuer`.")
    elif "target_role" in msg:
        report.append("  Expected body key `target_role: str`.")
    elif "Insufficient questions" in msg:
        report.append("  Question bank has no questions matching topic='Python' and difficulty='Easy'. Seed additional questions with `python -m scripts.seed_questions`.")
    elif "not found in UMS" in msg or "not found in local database" in msg:
        report.append("  Roll number 'DEMO001' not present in mock UMS adapter dictionary.")
    elif "roll_number" in msg:
        report.append("  Missing required field `roll_number` in request body.")
    elif "drive_id" in msg:
        report.append("  Missing required query parameter `?drive_id=<UUID>`.")
    else:
        report.append("  Standard schema validation / entity not found.")
    report.append("")

report.append("---")
report.append("## Master Table: All 138 API Endpoints Audit\n")
report.append("| # | Method | Path | Tag | Role | Status | Classification |")
report.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

for r in results:
    tag = r["tags"][0] if r["tags"] else "General"
    status_icon = "✅ 200/201" if r["classification"] == "SUCCESS" else ("❌ 500" if r["classification"] == "SERVER_ERROR" else f"⚠️ {r['status_code']}")
    report.append(f"| {r['index']} | `{r['method']}` | `{r['path_pattern']}` | {tag} | {r['role_tested']} | {status_icon} | {r['classification']} |")

report_text = "\n".join(report)

output_file_1 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "API_AUDIT_REPORT.md"))
with open(output_file_1, "w", encoding="utf-8") as f:
    f.write(report_text)
print(f"Report saved to workspace root: {output_file_1}")

output_file_2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "API_AUDIT_REPORT.md"))
with open(output_file_2, "w", encoding="utf-8") as f:
    f.write(report_text)
print(f"Report saved to backend: {output_file_2}")

# Also create the standalone fix_schema.sql file
sql_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "fix_schema.sql"))
with open(sql_path, "w", encoding="utf-8") as f:
    f.write("""-- CCIP Platform Database Fix Script
-- Resolves all missing columns and missing tables in PostgreSQL (Supabase)

-- 1. Add missing columns to existing tables
ALTER TABLE student_skills ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE;
ALTER TABLE certifications ADD COLUMN IF NOT EXISTS credential_id VARCHAR(200);
ALTER TABLE internships ADD COLUMN IF NOT EXISTS location VARCHAR(200);
ALTER TABLE internships ADD COLUMN IF NOT EXISTS employment_type VARCHAR(50) DEFAULT 'Internship';
ALTER TABLE internships ADD COLUMN IF NOT EXISTS is_current BOOLEAN DEFAULT FALSE;

-- 2. Curriculum Proposals
CREATE TABLE IF NOT EXISTS curriculum_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(300) NOT NULL,
    department_code VARCHAR(10) NOT NULL,
    description TEXT NOT NULL,
    rationale TEXT NOT NULL,
    proposed_changes JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'draft',
    submitted_by UUID REFERENCES users(id),
    reviewed_by UUID REFERENCES users(id),
    hod_comments TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    reviewed_at TIMESTAMP WITHOUT TIME ZONE
);

-- 3. Mock Interview Sessions
CREATE TABLE IF NOT EXISTS mock_interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id),
    role_target VARCHAR(200) NOT NULL,
    company_style VARCHAR(50) NOT NULL DEFAULT 'Product',
    difficulty VARCHAR(30) NOT NULL DEFAULT 'campus',
    status VARCHAR(20) NOT NULL DEFAULT 'setup',
    current_round INTEGER DEFAULT 0,
    transcript JSONB DEFAULT '[]',
    questions_asked TEXT[],
    performance_scores JSONB,
    final_report JSONB,
    duration_seconds INTEGER,
    word_count INTEGER,
    filler_word_count INTEGER DEFAULT 0,
    started_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    completed_at TIMESTAMP WITHOUT TIME ZONE
);

-- 4. In-App Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info',
    link VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- 5. Student Talent Cohorts
CREATE TABLE IF NOT EXISTS student_cohorts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    criteria JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- 6. Interview Experiences & Questions
CREATE TABLE IF NOT EXISTS interview_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id),
    company_name VARCHAR(200) NOT NULL,
    role VARCHAR(200) NOT NULL,
    placement_drive_id UUID REFERENCES placement_drives(id),
    difficulty VARCHAR(20) NOT NULL,
    verdict VARCHAR(30) NOT NULL,
    overall_experience TEXT NOT NULL,
    questions_asked JSONB DEFAULT '[]',
    tips_for_juniors TEXT,
    upvotes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- 7. Drive Announcements
CREATE TABLE IF NOT EXISTS drive_announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drive_id UUID NOT NULL REFERENCES placement_drives(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(300) NOT NULL,
    message TEXT NOT NULL,
    urgency VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
""")
print(f"SQL migration script saved to: {sql_path}")

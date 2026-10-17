"""
Comprehensive test suite for Sakshi's Final Task Sheet Submission:
  - TASK 1: Rich Portfolio System V2 & Full Lifecycle CRUD
  - TASK 2: Public Vanity Portfolio & Completeness Calculator
  - TASK 3: Automated Resume Parser & ATS Compatibility Analyzer
  - TASK 4: Placement Preparation Resource Hub & Collections
  - TASK 5: Alumni Mentorship & Professional Network
"""

import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, Student
from app.models.portfolio import Project, Certification, Internship, CareerGoal
from app.core.security import hash_password
from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


# ─── Helper to create a second student ──────────────────────────────────────────

async def _create_test_student(db: AsyncSession, department_id: uuid.UUID, roll_suffix: str) -> tuple[User, Student]:
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"sakshi_student_{roll_suffix}_{user_id.hex[:4]}@ccip.edu",
        password_hash=hash_password("password123"),
        first_name="Priya",
        last_name="Agarwal",
        role="student",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    student = Student(
        id=user_id,
        roll_number=f"22CS{roll_suffix[:6].upper()}",
        department_id=department_id,
        current_semester=7,
        admission_year=2022,
        cgpa=9.12,
        bio="Full-Stack Engineer & Open Source Contributor. Passionate about distributed systems.",
        github_url="https://github.com/priya-agarwal",
        linkedin_url="https://linkedin.com/in/priya-agarwal",
        consent_profile_visible=True,
    )
    db.add(student)
    await db.commit()
    await db.refresh(user)
    await db.refresh(student)
    return user, student


# ─── TASK 1: Rich Portfolio System V2 & Full Lifecycle CRUD ────────────────────

class TestTask1RichPortfolioCRUD:
    """Full lifecycle CRUD tests for Project, Certification, Internship, CareerGoal."""

    async def test_project_rich_crud_lifecycle(self, client: AsyncClient, seed_student):
        user, _ = seed_student
        headers = auth_headers(user)

        # 1. Create Project with rich production fields
        payload = {
            "title": "Cloud Scale Analytics Engine",
            "description": "High-throughput stream analytics pipeline processing 50k events/sec.",
            "tech_stack": ["FastAPI", "Apache Kafka", "ClickHouse", "Docker"],
            "github_url": "https://github.com/priya/cloud-analytics",
            "live_url": "https://analytics.demo.priya.dev",
            "thumbnail_url": "https://assets.priya.dev/preview.png",
            "status": "completed",
            "role": "Lead Architect",
            "team_size": 3,
            "highlights": ["Reduced end-to-end query latency by 45%", "Benchmarked at 50,000 req/sec"],
            "is_featured": True,
            "start_date": "2024-01-15",
            "end_date": "2024-05-30",
        }
        res_create = await client.post("/api/v1/students/me/projects", json=payload, headers=headers)
        assert res_create.status_code == 201
        created = res_create.json()
        proj_id = created["id"]
        assert created["title"] == payload["title"]
        assert created["is_featured"] is True
        assert created["featured"] is True
        assert created["thumbnail_url"] == payload["thumbnail_url"]
        assert created["role"] == "Lead Architect"
        assert created["team_size"] == 3
        assert len(created["highlights"]) == 2

        # 2. Get projects list
        res_list = await client.get("/api/v1/students/me/projects", headers=headers)
        assert res_list.status_code == 200
        items = res_list.json()
        assert any(p["id"] == proj_id for p in items)

        # 3. Patch project details and toggle featured
        patch_payload = {
            "title": "Cloud Scale Analytics Engine V2",
            "is_featured": False,
            "status": "archived",
            "role": "Principal Engineer",
        }
        res_patch = await client.patch(f"/api/v1/students/me/projects/{proj_id}", json=patch_payload, headers=headers)
        assert res_patch.status_code == 200
        patched = res_patch.json()
        assert patched["title"] == "Cloud Scale Analytics Engine V2"
        assert patched["is_featured"] is False
        assert patched["role"] == "Principal Engineer"
        assert patched["status"] == "archived"

        # 4. Delete project
        res_del = await client.delete(f"/api/v1/students/me/projects/{proj_id}", headers=headers)
        assert res_del.status_code == 204

        # 5. Verify deletion
        res_list_after = await client.get("/api/v1/students/me/projects", headers=headers)
        assert all(p["id"] != proj_id for p in res_list_after.json())

    async def test_certification_rich_crud_lifecycle(self, client: AsyncClient, seed_student):
        user, _ = seed_student
        headers = auth_headers(user)

        # 1. Create certification
        payload = {
            "name": "AWS Certified Solutions Architect – Associate",
            "issuing_organization": "Amazon Web Services",
            "issue_date": "2024-03-10",
            "expiration_date": "2027-03-10",
            "credential_id": "AWS-PSA-99128",
            "credential_url": "https://www.credly.com/badges/aws-solutions-architect",
            "certificate_image_url": "https://assets.priya.dev/aws-cert.png",
            "skills_covered": ["AWS EC2", "AWS S3", "VPC", "IAM", "Cloud Architecture"],
            "is_verified": True,
        }
        res_create = await client.post("/api/v1/students/me/certifications", json=payload, headers=headers)
        assert res_create.status_code == 201
        created = res_create.json()
        cert_id = created["id"]
        assert created["name"] == payload["name"]
        assert created["credential_id"] == "AWS-PSA-99128"
        assert created["is_verified"] is True
        assert len(created["skills_covered"]) == 5

        # 2. Get certifications list
        res_list = await client.get("/api/v1/students/me/certifications", headers=headers)
        assert res_list.status_code == 200
        assert any(c["id"] == cert_id for c in res_list.json())

        # 3. Patch certification
        patch_payload = {
            "name": "AWS Certified Solutions Architect – Professional",
            "credential_id": "AWS-PSA-99128-PRO",
        }
        res_patch = await client.patch(f"/api/v1/students/me/certifications/{cert_id}", json=patch_payload, headers=headers)
        assert res_patch.status_code == 200
        assert res_patch.json()["name"] == patch_payload["name"]
        assert res_patch.json()["credential_id"] == "AWS-PSA-99128-PRO"

        # 4. Delete certification
        res_del = await client.delete(f"/api/v1/students/me/certifications/{cert_id}", headers=headers)
        assert res_del.status_code == 204

    async def test_internship_and_experience_crud_lifecycle(self, client: AsyncClient, seed_student):
        user, _ = seed_student
        headers = auth_headers(user)

        # 1. Create Internship via /internships alias
        payload = {
            "company_name": "Microsoft India",
            "role": "Software Engineering Intern",
            "location": "Hyderabad, Telangana",
            "employment_type": "Internship",
            "start_date": "2024-05-15",
            "end_date": "2024-07-25",
            "is_current": False,
            "description": "Engineered Azure Cosmos DB query caching layer improving throughput by 30%.",
            "skills_used": ["C#", ".NET Core", "Azure Cosmos DB", "Redis"],
            "stipend_monthly": 125000.0,
            "offer_letter_url": "https://vault.ccip.edu/docs/msft-offer.pdf",
            "completion_certificate_url": "https://vault.ccip.edu/docs/msft-cert.pdf",
            "is_verified": True,
        }
        res_create = await client.post("/api/v1/students/me/internships", json=payload, headers=headers)
        assert res_create.status_code == 201
        created = res_create.json()
        intern_id = created["id"]
        assert created["company_name"] == "Microsoft India"
        assert created["role"] == "Software Engineering Intern"
        assert float(created["stipend_monthly"]) == 125000.0
        assert created["is_verified"] is True

        # 2. Get internships
        res_get = await client.get("/api/v1/students/me/internships", headers=headers)
        assert res_get.status_code == 200
        assert any(i["id"] == intern_id for i in res_get.json())

        # 3. Patch internship via /experience alias
        patch_payload = {
            "role": "Senior Software Engineering Intern",
            "stipend_monthly": 140000.0,
        }
        res_patch = await client.patch(f"/api/v1/students/me/experience/{intern_id}", json=patch_payload, headers=headers)
        assert res_patch.status_code == 200
        assert res_patch.json()["role"] == "Senior Software Engineering Intern"
        assert float(res_patch.json()["stipend_monthly"]) == 140000.0

        # 4. Delete internship
        res_del = await client.delete(f"/api/v1/students/me/internships/{intern_id}", headers=headers)
        assert res_del.status_code == 204

    async def test_career_goals_endpoints(self, client: AsyncClient, seed_student):
        user, _ = seed_student
        headers = auth_headers(user)

        # 1. Create or set career goal
        payload = {
            "target_role": "Backend Distributed Systems Engineer",
            "target_domain": "Cloud Infrastructure",
            "target_companies": ["Google", "Microsoft", "Uber", "Stripe"],
            "preferred_locations": ["Bengaluru", "Hyderabad", "Remote"],
            "expected_ctc_lpa": 28.5,
            "expected_ctc_range": "25 - 35 LPA",
            "priority": 1,
            "is_active": True,
        }
        res_post = await client.post("/api/v1/students/me/career-goals", json=payload, headers=headers)
        assert res_post.status_code in (200, 201)
        data = res_post.json()
        assert data["target_role"] == payload["target_role"]
        assert "Bengaluru" in data["preferred_locations"]
        assert float(data["expected_ctc_lpa"]) == 28.5

        # 2. Get career goals
        res_get = await client.get("/api/v1/students/me/career-goals", headers=headers)
        assert res_get.status_code == 200
        goals = res_get.json()
        assert len(goals) >= 1
        assert goals[0]["target_role"] == payload["target_role"]

        # 3. Patch career goals
        res_patch = await client.patch(
            "/api/v1/students/me/career-goals",
            json={"target_role": "Staff Platform Engineer", "expected_ctc_lpa": 36.0},
            headers=headers,
        )
        assert res_patch.status_code == 200
        assert res_patch.json()["target_role"] == "Staff Platform Engineer"
        assert float(res_patch.json()["expected_ctc_lpa"]) == 36.0


# ─── TASK 2: Public Vanity Portfolio & Completeness Calculator ─────────────────

class TestTask2PublicPortfolioAndCompleteness:
    """Tests for public showcase, custom vanity slugs, settings, and completeness score."""

    async def test_profile_completeness_calculator(self, client: AsyncClient, seed_student):
        user, _ = seed_student
        headers = auth_headers(user)

        res = await client.get("/api/v1/portfolio/me/completeness", headers=headers)
        assert res.status_code == 200
        body = res.json()

        assert "completeness_score" in body
        assert "score" in body
        assert 0 <= body["score"] <= 100
        assert body["tier"] in ("Beginner", "Intermediate", "All-Star", "Recruiter Ready")
        assert "breakdown" in body

        # Verify all 8 criteria exist in breakdown
        for category in ["basic_profile", "skills", "projects", "internships", "certifications", "resume", "external_links", "career_goals"]:
            assert category in body["breakdown"]
            item = body["breakdown"][category]
            assert "points_earned" in item
            assert "max_points" in item
            assert "completed" in item
            assert item["points_earned"] <= item["max_points"]

        assert isinstance(body["actionable_steps"], list)

    async def test_portfolio_settings_and_vanity_slug(self, client: AsyncClient, seed_student, db: AsyncSession):
        user, student = seed_student
        headers = auth_headers(user)

        unique_slug = f"priya-agarwal-{uuid.uuid4().hex[:6]}"

        # 1. Update settings with vanity slug and public visibility
        res_settings = await client.patch(
            "/api/v1/portfolio/me/settings",
            json={"custom_slug": unique_slug, "is_public": True},
            headers=headers,
        )
        assert res_settings.status_code == 200
        settings_data = res_settings.json()
        assert settings_data["custom_slug"] == unique_slug
        assert settings_data["is_public"] is True
        assert f"/portfolio/slug/{unique_slug}" in settings_data["public_url"]

        # 2. Access public portfolio via slug (Zero authentication required)
        res_slug = await client.get(f"/portfolio/slug/{unique_slug}")
        assert res_slug.status_code == 200
        pub = res_slug.json()
        assert pub["custom_slug"] == unique_slug
        assert pub["is_public"] is True
        assert pub["name"] == f"{user.first_name} {user.last_name}"
        assert pub["college_name"] == "University Placement Cell"
        assert "social_links" in pub
        assert "verified_skills" in pub

        # 3. Access public portfolio via student ID (Zero authentication required)
        res_id = await client.get(f"/portfolio/{student.id}")
        assert res_id.status_code == 200
        assert res_id.json()["id"] == str(student.id)

        # 4. Verify privacy: phone number and emails must NOT be in public portfolio
        assert "phone" not in pub
        assert "email" not in pub
        assert "backlogs" not in pub

        # 5. Invalid slug format returns 400
        res_bad_slug = await client.patch(
            "/api/v1/portfolio/me/settings",
            json={"custom_slug": "A!"},  # too short and illegal characters
            headers=headers,
        )
        assert res_bad_slug.status_code == 400

        # 6. Test slug conflict when another student takes it
        user2, _ = await _create_test_student(db, student.department_id, "999")
        headers2 = auth_headers(user2)
        res_conflict = await client.patch(
            "/api/v1/portfolio/me/settings",
            json={"custom_slug": unique_slug},  # already taken by student 1
            headers=headers2,
        )
        assert res_conflict.status_code == 409

        # 7. Privacy protection: toggle is_public = False
        await client.patch(
            "/api/v1/portfolio/me/settings",
            json={"is_public": False},
            headers=headers,
        )
        res_private_slug = await client.get(f"/portfolio/slug/{unique_slug}")
        assert res_private_slug.status_code == 403
        res_private_id = await client.get(f"/portfolio/{student.id}")
        assert res_private_id.status_code == 403


# ─── TASK 3: Automated Resume Parser & ATS Compatibility Analyzer ──────────────

class TestTask3ResumeAtsAnalyzer:
    """Tests for ATS score calculation and entity recognition."""

    async def test_ats_score_with_explicit_text(self, client: AsyncClient, seed_student):
        user, _ = seed_student
        headers = auth_headers(user)

        resume_sample = """
        Priya Agarwal
        Email: priya.agarwal@example.com | Phone: +91 9876543210
        GitHub: https://github.com/priya-agarwal | LinkedIn: https://linkedin.com/in/priya-agarwal

        Summary
        Results-driven Full-Stack Engineer with 2+ years of hands-on experience building high-performance microservices.

        Skills
        Technical Skills: Python, Java, JavaScript, TypeScript, React, Node.js, FastAPI, SQL, PostgreSQL, Docker, Kubernetes, Git, Algorithms, System Design

        Experience
        Software Engineering Intern - Microsoft India (May 2024 - July 2024)
        • Architected and deployed an internal query cache in Redis, reducing latency by 45% and serving 10,000+ daily queries.
        • Engineered automated CI/CD pipeline using Docker and GitHub Actions, cutting build duration by 35%.

        Projects
        Distributed Task Queue
        • Developed a scalable asynchronous background task engine using Python and Redis.
        • Improved message processing throughput by 50% across 4 worker nodes.

        Education
        Bachelor of Technology (B.Tech) in Computer Science & Engineering
        CGPA: 9.12/10 | Expected Graduation: 2026
        """

        jd_sample = """
        We are seeking a Backend Software Engineer proficient in Python, React, PostgreSQL, Docker, and System Design.
        Experience building distributed systems, optimizing queries, and deploying containerized applications is required.
        """

        payload = {
            "resume_text": resume_sample,
            "job_description": jd_sample,
        }
        res = await client.post("/api/v1/resume/ats-score", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()

        assert "ats_score" in data
        assert 0.0 <= data["ats_score"] <= 100.0
        assert data["grade"] in ("Exceptional", "Strong", "Competitive", "Needs Improvement")
        assert data["ats_score"] >= 75.0  # Strong resume with metrics, verbs, skills, sections
        assert len(data["matched_skills"]) >= 3
        assert len(data["formatting_flags"]) >= 1
        assert "breakdown" in data
        assert data["breakdown"]["keyword_coverage_score"] <= 50.0
        assert data["breakdown"]["structure_score"] <= 25.0
        assert data["breakdown"]["metrics_and_verbs_score"] <= 25.0

    async def test_ats_score_service_logic(self):
        from app.services.resume_parser import analyze_ats_score, extract_contact_info, extract_education

        sample_text = """
        John Doe - john@ccip.edu - 9876543210
        github.com/johndoe - linkedin.com/in/johndoe
        B.Tech in Computer Science, CGPA 8.75, Class of 2025.
        Skills: React, TypeScript, Docker, SQL, Python
        Projects: Built web application that reduced latency by 30% and increased users by 100%.
        """

        contact = extract_contact_info(sample_text)
        assert contact["email"] == "john@ccip.edu"
        assert contact["phone"] == "9876543210"
        assert "linkedin.com/in/johndoe" in contact["linkedin_url"]

        edu = extract_education(sample_text)
        assert edu["degree"] == "B.Tech"
        assert edu["cgpa"] == 8.75
        assert edu["graduation_year"] == 2025

        analysis = analyze_ats_score(sample_text, target_skills=["React", "TypeScript", "Docker", "Go"])
        assert analysis["ats_score"] > 40.0
        assert "React" in analysis["matched_skills"]
        assert "Go" in analysis["missing_target_skills"]


# ─── TASK 4: Placement Preparation Resource Hub & Collections ─────────────────

class TestTask4PrepResourceHub:
    """Tests for placement preparation resources, search, upvotes, and progress tracking."""

    async def test_prep_resources_listing_and_filtering(self, client: AsyncClient, seed_student, seed_tpo):
        tpo_user = seed_tpo
        student_user, _ = seed_student
        tpo_headers = auth_headers(tpo_user)
        student_headers = auth_headers(student_user)

        # 1. Create a prep resource as TPO
        res_create = await client.post(
            "/api/v1/prep/resources",
            json={
                "title": "FAANG System Design Primer & Scale Playbook",
                "description": "Comprehensive guide to distributed caching, load balancers, and sharding.",
                "category": "system_design",
                "resource_type": "article",
                "difficulty": "advanced",
                "url": "https://prep.ccip.edu/guides/system-design-faang",
                "tags": ["System Design", "Microservices", "Scalability"],
                "target_companies": ["Google", "Amazon", "Microsoft"],
                "estimated_minutes": 60,
            },
            headers=tpo_headers,
        )
        assert res_create.status_code == 200
        created = res_create.json()
        resource_id = created["id"]

        # 2. Test paginated listing with target_company filter
        res_list = await client.get("/api/v1/prep/resources?company=Google", headers=student_headers)
        assert res_list.status_code == 200
        data = res_list.json()
        assert "data" in data
        assert "meta" in data
        assert data["meta"]["page"] == 1
        assert data["meta"]["total_pages"] >= 1
        assert data["meta"]["page_size"] >= 1
        assert any(r["id"] == resource_id for r in data["data"])

        # 3. Test upvote resource
        res_upvote = await client.post(f"/api/v1/prep/resources/{resource_id}/upvote", headers=student_headers)
        assert res_upvote.status_code == 200
        assert "upvoted" in res_upvote.json()["message"].lower()

        # 4. Test progress tracking
        res_prog = await client.post(
            f"/api/v1/prep/progress/{resource_id}",
            json={"status": "completed", "progress_pct": 100.0, "notes": "Mastered horizontal sharding patterns"},
            headers=student_headers,
        )
        assert res_prog.status_code == 200
        assert res_prog.json()["status"] == "completed"
        assert res_prog.json()["progress_pct"] == 100.0

        # 5. Fetch my progress statistics
        res_mine = await client.get("/api/v1/prep/progress/mine", headers=student_headers)
        assert res_mine.status_code == 200
        assert isinstance(res_mine.json(), list)


# ─── TASK 5: Alumni Mentorship & Professional Network ──────────────────────────

class TestTask5AlumniMentorshipNetwork:
    """Tests for alumni mentor registration, directory queries, requests, and sessions."""

    async def test_alumni_directory_and_session_booking(self, client: AsyncClient, seed_student, seed_tpo):
        tpo_user = seed_tpo
        student_user, _ = seed_student
        tpo_headers = auth_headers(tpo_user)
        student_headers = auth_headers(student_user)

        # 1. Register as Alumni Mentor
        res_reg = await client.post(
            "/api/v1/alumni/profile",
            json={
                "graduation_year": 2023,
                "department_code": "CS",
                "current_company": "Google",
                "current_designation": "Software Engineer II",
                "linkedin_url": "https://linkedin.com/in/alumni-mentor",
                "expertise_areas": ["Distributed Systems", "DSA", "System Design"],
                "bio": "Mentoring campus students for Tier-1 product company interviews.",
                "max_mentees": 4,
            },
            headers=tpo_headers,
        )
        assert res_reg.status_code == 200
        alumni_profile = res_reg.json()
        alumni_id = alumni_profile["id"]
        assert alumni_profile["current_company"] == "Google"
        assert alumni_profile["graduation_year"] == 2023

        # 2. Browse alumni directory with company and domain filter
        res_dir = await client.get("/api/v1/alumni?company=Google&domain=CS", headers=student_headers)
        assert res_dir.status_code == 200
        dir_data = res_dir.json()
        assert "data" in dir_data
        assert "meta" in dir_data
        assert any(a["id"] == alumni_id for a in dir_data["data"])

        # 3. Student requests mentorship connection
        res_req = await client.post(
            "/api/v1/alumni/mentorship",
            json={
                "alumni_id": alumni_id,
                "message": "Hi, I am preparing for Google L3 SWE interviews and would love your guidance.",
                "goals": ["Mock System Design", "Resume Feedback"],
            },
            headers=student_headers,
        )
        assert res_req.status_code in (200, 201)
        conn_id = res_req.json()["id"]

        # 4. Mentor accepts connection
        res_accept = await client.patch(
            f"/api/v1/alumni/mentorship/{conn_id}",
            params={"new_status": "active"},
            headers=tpo_headers,
        )
        assert res_accept.status_code == 200
        assert res_accept.json()["status"] == "active"

        # 5. Schedule session with calendar link
        scheduled_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        res_session = await client.post(
            "/api/v1/alumni/sessions",
            json={
                "connection_id": conn_id,
                "scheduled_at": scheduled_time,
                "duration_minutes": 45,
                "topic": "Google System Design Mock Interview",
                "meeting_link": "https://meet.google.com/abc-defg-hij",
            },
            headers=tpo_headers,
        )
        assert res_session.status_code == 200
        session_id = res_session.json()["id"]

        # 6. Student submits session feedback
        res_fb = await client.post(
            f"/api/v1/alumni/sessions/{session_id}/feedback",
            json={"rating": 5, "feedback": "Exceptional insights into distributed cache consistency!"},
            headers=student_headers,
        )
        assert res_fb.status_code == 200
        assert res_fb.json()["student_rating"] == 5

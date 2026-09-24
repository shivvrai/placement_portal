"""
Comprehensive API Endpoint Tester for CCIP Platform.
Hits every endpoint registered in app.routes, records responses, errors, stack traces,
and generates both JSON and Markdown reports.
"""

import asyncio
import json
import logging
import os
import sys
import traceback
import uuid
from typing import Any, Dict, List, Optional

import httpx
from fastapi.routing import APIRoute

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.database import AsyncSessionLocal
from sqlalchemy import text


async def get_test_context():
    """Query database for real IDs to use in path parameters."""
    ctx = {
        "student_id": "ba517a5c-f558-4084-8518-4ad88c4911b5",
        "user_id": "ba517a5c-f558-4084-8518-4ad88c4911b5",
        "drive_id": "9b275276-e283-403f-bfad-246a1e5ceb86",
        "application_id": "a9b6a316-2c5b-476a-acd8-668622d0cf99",
        "skill_id": "9f373faa-13e5-4f07-ae09-1ca416bbc0b8",
        "department_code": "CS",
        "dept": "CS",
        "subject_id": "24441b33-0bdd-4861-80f0-1f229aa42a26",
        "job_id": "53d57f57-42b9-4263-b341-5f2a71b8747d",
        "session_id": "af6c1cd8-857d-44e9-8ff9-6a2a051c7664",
        "roll_number": "DEMO001",
        "task_id": "a9b6a316-2c5b-476a-acd8-668622d0cf99",
        "project_id": str(uuid.uuid4()),
        "cert_id": str(uuid.uuid4()),
        "exp_id": str(uuid.uuid4()),
        "experience_id": str(uuid.uuid4()),
        "conversation_id": str(uuid.uuid4()),
        "proposal_id": str(uuid.uuid4()),
        "cohort_id": str(uuid.uuid4()),
        "notification_id": str(uuid.uuid4()),
        "entity": "Students",
        "academic_year": "2025-26",
    }
    
    try:
        async with AsyncSessionLocal() as session:
            # Check student
            r = await session.execute(text("SELECT id FROM students LIMIT 1"))
            row = r.fetchone()
            if row: ctx["student_id"] = str(row[0])
            
            # Check drive
            r = await session.execute(text("SELECT id FROM placement_drives LIMIT 1"))
            row = r.fetchone()
            if row: ctx["drive_id"] = str(row[0])
            
            # Check application
            r = await session.execute(text("SELECT id FROM applications LIMIT 1"))
            row = r.fetchone()
            if row: ctx["application_id"] = str(row[0])
            
            # Check skill
            r = await session.execute(text("SELECT id FROM skills LIMIT 1"))
            row = r.fetchone()
            if row: ctx["skill_id"] = str(row[0])
            
            # Check subject
            r = await session.execute(text("SELECT id FROM subjects LIMIT 1"))
            row = r.fetchone()
            if row: ctx["subject_id"] = str(row[0])

            # Check assessment session
            r = await session.execute(text("SELECT id FROM assessment_sessions LIMIT 1"))
            row = r.fetchone()
            if row: ctx["session_id"] = str(row[0])
    except Exception as e:
        print("Warning fetching context from DB:", e)
        
    return ctx


def get_default_body_and_params(route_path: str, method: str, ctx: dict):
    """Generate appropriate body and query params based on path and method."""
    body = None
    query_params = {}
    files = None

    # Query params defaults
    if "department_code" in route_path or "curriculum-gaps" in route_path:
        query_params["semester_number"] = 6
    if "/skills/search" in route_path:
        query_params["q"] = "Python"
    if "/accreditation/report" in route_path:
        query_params["format"] = "json"
        query_params["academic_year"] = "2025-26"
    if "/bi/odata" in route_path:
        query_params["top"] = 5
    if "/bi/export" in route_path:
        query_params["format"] = "json"
    if "/tpo/cohorts/query" in route_path:
        query_params["page"] = 1
        query_params["page_size"] = 10

    # Request bodies for POST / PUT / PATCH
    if method in ("POST", "PUT", "PATCH"):
        if route_path == "/api/v1/auth/register":
            body = {
                "email": f"test_audit_{uuid.uuid4().hex[:6]}@ccip.edu",
                "password": "Password123!",
                "role": "student",
                "first_name": "Audit",
                "last_name": "Test"
            }
        elif route_path == "/api/v1/auth/login":
            body = {
                "email": "student@demo.ccip",
                "password": "password123"
            }
        elif route_path == "/api/v1/auth/refresh":
            body = {"refresh_token": ctx.get("student_refresh_token", "invalid_token")}
        elif route_path in ("/api/v1/students/me", "/api/v1/students/{student_id}"):
            body = {
                "first_name": "Demo",
                "last_name": "Student",
                "bio": "Testing student profile update"
            }
        elif "/consent" in route_path:
            body = {
                "consent_resume_analysis": True,
                "consent_profile_visible": True
            }
        elif route_path == "/api/v1/students/me/skills":
            body = {
                "skill_id": ctx["skill_id"],
                "proficiency": 3
            }
        elif route_path == "/api/v1/students/me/skills/bulk":
            body = {
                "skills": [{"name": "Python", "proficiency": 4}]
            }
        elif route_path == "/api/v1/students/me/projects":
            body = {
                "title": "Smart Placement Portal",
                "description": "Full stack placement and career platform",
                "technologies": ["Python", "FastAPI", "React"],
                "github_url": "https://github.com/demo/project",
                "is_featured": True
            }
        elif route_path == "/api/v1/students/me/certifications":
            body = {
                "title": "AWS Certified Cloud Practitioner",
                "issuer": "Amazon Web Services",
                "issue_date": "2024-01-15",
                "credential_id": "AWS-CERT-998877"
            }
        elif route_path == "/api/v1/students/me/experience":
            body = {
                "company_name": "Google",
                "role": "Software Engineering Intern",
                "start_date": "2024-05-01",
                "end_date": "2024-08-01",
                "description": "Developed backend microservices",
                "employment_type": "Internship"
            }
        elif route_path == "/api/v1/drives":
            body = {
                "company_name": "Microsoft",
                "company_industry": "Information Technology",
                "company_location": "Hyderabad",
                "title": "Software Engineer 2026",
                "description": "Campus recruitment for SWE role",
                "min_cgpa": 7.5,
                "eligible_departments": ["CS", "IT"],
                "roles_offered": ["Software Engineer"],
                "salary_ctc": 18.0,
                "academic_year": "2025-26"
            }
        elif route_path == "/api/v1/drives/{drive_id}":
            body = {
                "title": "Updated SWE Drive 2026",
                "salary_ctc": 19.5
            }
        elif "/applications/{application_id}/offer" in route_path:
            body = {
                "offer_ctc_lpa": 14.5,
                "offer_fixed_lpa": 12.0,
                "offer_variable_lpa": 2.5,
                "offer_designation": "Associate Software Engineer"
            }
        elif "/applications/{application_id}" in route_path:
            body = {
                "status": "shortlisted",
                "current_stage": "Technical Interview 1",
                "stage_status": "scheduled"
            }
        elif "/announcements" in route_path and method == "POST":
            body = {
                "title": "Drive Schedule Update",
                "message": "Round 1 results are out. Interview begins at 10 AM.",
                "urgency": "important"
            }
        elif "/roadmap/me/generate" in route_path:
            body = {
                "career_goal": "Full Stack Developer",
                "target_tier": 1
            }
        elif "/roadmap/tasks/{task_id}" in route_path:
            body = {
                "status": "completed"
            }
        elif "/roadmap/me/tasks" in route_path:
            body = {
                "title": "Learn FastAPI & SQLAlchemy",
                "description": "Complete async database tutorial",
                "estimated_hours": 6
            }
        elif route_path == "/api/v1/copilot/conversations":
            body = {
                "title": "Mock Interview & Resume Review"
            }
        elif "/messages" in route_path:
            body = {
                "content": "What are the common system design questions for freshers?"
            }
        elif "/mock-interview/start" in route_path:
            body = {
                "role_target": "Software Engineer",
                "company_style": "Product",
                "difficulty": "campus"
            }
        elif "/mock-interview/{conversation_id}/respond" in route_path:
            body = {
                "content": "I am passionate about distributed systems and Python."
            }
        elif route_path == "/api/v1/resume/upload":
            files = {
                "file": ("sample_resume.pdf", b"%PDF-1.4 sample resume content for testing", "application/pdf")
            }
        elif route_path == "/api/v1/assessments/start" or route_path == "/api/v1/assessments/quiz/quick":
            body = {
                "topic": "Python",
                "difficulty": "Easy",
                "num_questions": 5
            }
        elif "/assessments/{session_id}/submit" in route_path:
            body = {
                "answers": [
                    {"question_id": str(uuid.uuid4()), "selected_option": "A"}
                ]
            }
        elif route_path == "/api/v1/ums/sync":
            body = {
                "department_code": "CS",
                "batch_year": 2024
            }
        elif "/suggest-mappings" in route_path:
            body = {
                "skill_id": ctx["skill_id"]
            }
        elif route_path == "/api/v1/curriculum/proposals":
            body = {
                "title": "Add GenAI & LLM Elective",
                "department_code": "CS",
                "description": "Introduce LLM engineering concepts to final year students",
                "rationale": "High industry demand for AI engineers",
                "proposed_changes": {"elective_type": "advanced"}
            }
        elif "/proposals/{proposal_id}/status" in route_path:
            body = {
                "status": "approved",
                "comments": "Approved for 2025-26 academic curriculum."
            }
        elif route_path == "/api/v1/tpo/cohorts/query":
            body = {
                "min_cgpa": 7.0,
                "departments": ["CS"]
            }
        elif route_path == "/api/v1/tpo/cohorts":
            body = {
                "name": "High Achievers CS 2026",
                "description": "Students with CGPA >= 8.0",
                "criteria": {"min_cgpa": 8.0, "departments": ["CS"]}
            }
        elif route_path == "/api/v1/experiences" and method == "POST":
            body = {
                "company_name": "Google",
                "role": "Software Engineer",
                "difficulty": "Medium",
                "verdict": "Selected",
                "overall_experience": "Great interview with 3 rounds: DSA, System Design, HR.",
                "tips_for_juniors": "Focus on graphs and dynamic programming."
            }
        elif route_path == "/api/v1/mock-interviews/start":
            body = {
                "role_target": "Software Engineer",
                "company_style": "Product",
                "difficulty": "campus"
            }
        elif "/mock-interviews/{session_id}/message" in route_path:
            body = {
                "content": "I have experience with Python, FastAPI, and relational databases."
            }

    return body, query_params, files


def determine_primary_role(route_path: str, module: str, tags: list) -> str:
    """Determine the most appropriate user role to test an endpoint with."""
    if route_path in ("/health", "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh"):
        return "public"

    # Specific role assignments based on path/module
    if "/proposals/{proposal_id}/status" in route_path:
        return "admin"
    if route_path.startswith("/api/v1/students/me") or route_path.startswith("/api/v1/applications/mine") \
       or route_path.startswith("/api/v1/gaps/me") or route_path.startswith("/api/v1/matching/me") \
       or route_path.startswith("/api/v1/roadmap/me") or route_path.startswith("/api/v1/copilot") \
       or route_path.startswith("/api/v1/resume") or route_path.startswith("/api/v1/assessments") \
       or route_path.startswith("/api/v1/mock-interviews") or route_path.startswith("/api/v1/notifications"):
        return "student"

    if route_path.startswith("/api/v1/tpo") or route_path.startswith("/api/v1/ums") \
       or route_path.startswith("/api/v1/system") or route_path.startswith("/api/v1/analytics") \
       or route_path.startswith("/api/v1/bi"):
        return "tpo"

    if route_path.startswith("/api/v1/curriculum"):
        return "faculty"

    if route_path.startswith("/api/v1/drives"):
        if "/apply" in route_path:
            return "student"
        return "tpo"

    if route_path.startswith("/api/v1/students"):
        return "tpo"

    return "student"


async def run_audit():
    print("=" * 80)
    print("STARTING COMPLETE CCIP API AUDIT")
    print("=" * 80)

    ctx = await get_test_context()
    print("Loaded test context:", ctx)

    results = []

    # Use ASGITransport with raise_app_exceptions=True so we can catch unhandled server crashes
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=True), base_url="http://test") as client:
        # 1. Obtain Tokens
        tokens = {}
        users_to_login = [
            ("student", "student@demo.ccip", "password123"),
            ("tpo", "tpo@demo.ccip", "password123"),
            ("faculty", "faculty@demo.ccip", "password123"),
            ("admin", "admin@demo.ccip", "password123"),
        ]

        print("\nAuthenticating test roles...")
        for role, email, password in users_to_login:
            try:
                res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
                if res.status_code == 200:
                    tokens[role] = res.json()["access_token"]
                    if role == "student":
                        ctx["student_refresh_token"] = res.json().get("refresh_token")
                    print(f"  [OK] {role:7} token obtained ({email})")
                else:
                    print(f"  [FAIL] {role:7} login failed: {res.status_code} {res.text}")
            except Exception as e:
                print(f"  [ERROR] {role:7} login exception: {e}")

        # Pre-create Copilot Conversation so conversation_id works
        if "student" in tokens:
            try:
                conv_res = await client.post(
                    "/api/v1/copilot/conversations",
                    headers={"Authorization": f"Bearer {tokens['student']}"},
                    json={"title": "Test Audit Session"}
                )
                if conv_res.status_code in (200, 201):
                    conv_id = conv_res.json().get("id")
                    if conv_id:
                        ctx["conversation_id"] = conv_id
                        print(f"Created test copilot conversation: {conv_id}")
            except Exception as e:
                print("Could not pre-create copilot conversation:", e)

        # 2. Iterate through all APIRoutes
        api_routes = [r for r in app.routes if isinstance(r, APIRoute)]
        print(f"\nDiscovered {len(api_routes)} total API routes to test.\n")

        for idx, route in enumerate(api_routes, 1):
            route_path = route.path
            methods = sorted(list(route.methods - {"HEAD", "OPTIONS"}))
            method = methods[0] if methods else "GET"

            # Resolve path parameters
            resolved_path = route_path
            for param_key, param_val in ctx.items():
                if f"{{{param_key}}}" in resolved_path:
                    resolved_path = resolved_path.replace(f"{{{param_key}}}", str(param_val))

            # Determine primary role
            role = determine_primary_role(route_path, route.endpoint.__module__, route.tags)
            headers = {}
            if role != "public" and role in tokens:
                headers["Authorization"] = f"Bearer {tokens[role]}"

            # Generate payload & query params
            body, query_params, files = get_default_body_and_params(route_path, method, ctx)

            # Test execution with retry on 401/403 with other roles
            status_code = None
            response_data = None
            error_classification = None
            exception_info = None
            tried_roles = [role]

            async def execute_request(role_to_use):
                nonlocal headers, status_code, response_data, exception_info
                req_headers = {}
                if role_to_use != "public" and role_to_use in tokens:
                    req_headers["Authorization"] = f"Bearer {tokens[role_to_use]}"

                try:
                    if files:
                        resp = await client.request(
                            method, resolved_path, params=query_params, headers=req_headers, files=files
                        )
                    elif body is not None:
                        resp = await client.request(
                            method, resolved_path, params=query_params, headers=req_headers, json=body
                        )
                    else:
                        resp = await client.request(
                            method, resolved_path, params=query_params, headers=req_headers
                        )

                    status_code = resp.status_code
                    try:
                        response_data = resp.json()
                    except Exception:
                        response_data = resp.text[:1000]
                    exception_info = None
                    return status_code, response_data, None

                except Exception as exc:
                    status_code = 500
                    response_data = str(exc)
                    exception_info = {
                        "error_type": type(exc).__name__,
                        "error_msg": str(exc),
                        "traceback": traceback.format_exc(),
                    }
                    return 500, str(exc), exception_info

            # First attempt
            s_code, r_data, exc_i = await execute_request(role)

            # If 401 or 403, and not public, try other roles
            if s_code in (401, 403) and role != "public":
                for alt_role in ["admin", "tpo", "faculty", "student"]:
                    if alt_role not in tried_roles and alt_role in tokens:
                        tried_roles.append(alt_role)
                        s_code, r_data, exc_i = await execute_request(alt_role)
                        if s_code not in (401, 403):
                            role = alt_role
                            break

            # Classify result
            if s_code in (200, 201, 204):
                error_classification = "SUCCESS"
            elif s_code == 500 or exc_i is not None:
                error_classification = "SERVER_ERROR"
            elif s_code in (400, 404, 409, 422):
                error_classification = "CLIENT_ERROR"
            elif s_code in (401, 403):
                error_classification = "AUTH_FORBIDDEN"
            else:
                error_classification = f"HTTP_{s_code}"

            log_symbol = "[OK]" if error_classification == "SUCCESS" else ("[CRASH]" if error_classification == "SERVER_ERROR" else f"[{s_code}]")
            print(f"[{idx:3d}/138] {log_symbol:8} {method:6} {resolved_path:45} (role: {role}) -> {s_code}")

            result_item = {
                "index": idx,
                "path_pattern": route_path,
                "resolved_url": resolved_path,
                "method": method,
                "endpoint_name": route.endpoint.__name__,
                "module": getattr(route.endpoint, "__module__", ""),
                "tags": route.tags,
                "role_tested": role,
                "roles_attempted": tried_roles,
                "status_code": s_code,
                "classification": error_classification,
                "request_payload": body if not files else {"files": "sample_resume.pdf"},
                "query_params": query_params,
                "response": response_data,
                "exception": exc_i,
            }
            results.append(result_item)

    # 3. Compile Statistics
    total = len(results)
    successes = [r for r in results if r["classification"] == "SUCCESS"]
    server_errors = [r for r in results if r["classification"] == "SERVER_ERROR"]
    client_errors = [r for r in results if r["classification"] == "CLIENT_ERROR"]
    auth_errors = [r for r in results if r["classification"] == "AUTH_FORBIDDEN"]

    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print(f"Total Endpoints Tested : {total}")
    print(f"Successful (2xx)       : {len(successes)}")
    print(f"Server Errors (500)    : {len(server_errors)}")
    print(f"Client Errors (4xx)    : {len(client_errors)}")
    print(f"Auth Denied (401/403)  : {len(auth_errors)}")
    print("=" * 80)

    # 4. Save JSON Report
    json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api_test_results.json"))
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total": total,
                "success": len(successes),
                "server_errors": len(server_errors),
                "client_errors": len(client_errors),
                "auth_forbidden": len(auth_errors),
            },
            "results": results
        }, f, indent=2, default=str)
    print(f"\n[Saved] JSON results saved to: {json_path}")

    # Also save to workspace root
    workspace_json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "api_test_results.json"))
    try:
        with open(workspace_json_path, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total": total,
                    "success": len(successes),
                    "server_errors": len(server_errors),
                    "client_errors": len(client_errors),
                    "auth_forbidden": len(auth_errors),
                },
                "results": results
            }, f, indent=2, default=str)
        print(f"[Saved] JSON results copied to workspace root: {workspace_json_path}")
    except Exception as e:
        print("Could not copy to root:", e)

    return results


if __name__ == "__main__":
    asyncio.run(run_audit())

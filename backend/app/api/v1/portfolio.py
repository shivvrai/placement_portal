"""
Portfolio API — Public Showcase, Vanity URL resolution, Settings, Completeness Calculator.

Sprint Final — Sakshi Kumari

Endpoints:
  GET    /portfolio/{student_id}     — Unauthenticated public portfolio showcase
  GET    /portfolio/slug/{custom_slug} — Resolve public portfolio via vanity slug
  PATCH  /portfolio/me/settings      — Configure portfolio visibility and vanity slug
  GET    /portfolio/me/completeness  — Profile completeness calculation and recommendations
"""

import re
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user, get_current_student
from app.models.user import User, Student
from app.models.portfolio import Project, Certification, Internship, CareerGoal
from app.models.skill import StudentSkill, Skill
from app.schemas.portfolio import (
    PublicPortfolioResponse,
    PublicSocialLinks,
    PublicProjectItem,
    PublicCertificationItem,
    PublicInternshipItem,
    PortfolioSettingsUpdate,
    PortfolioSettingsResponse,
    ProfileCompletenessResponse,
    CompletenessBreakdownItem,
)

router = APIRouter(prefix="/portfolio", tags=["Student Portfolio & Identity"])


def _build_public_portfolio(student: Student) -> PublicPortfolioResponse:
    """Build sanitized, recruiter-friendly public portfolio payload."""
    user = student.user
    first_name = user.first_name if user else ""
    last_name = user.last_name if user else ""
    full_name = f"{first_name} {last_name}".strip() or "Student"

    dept_name = student.department.name if student.department else "Engineering"
    branch_name = student.department.code if student.department else "General"
    grad_year = (student.admission_year + 4) if student.admission_year else 2026

    # Extract verified and general skills
    verified_skills: list[str] = []
    all_skills: list[str] = []
    seen = set()

    skills_sorted = sorted(
        student.skills,
        key=lambda s: (s.is_verified, s.confidence or 0.0),
        reverse=True,
    )
    for ss in skills_sorted:
        s_name = ss.skill.name if ss.skill else None
        if not s_name:
            continue
        low = s_name.lower()
        if low not in seen:
            seen.add(low)
            all_skills.append(s_name)
            if getattr(ss, "is_verified", False) or ss.source in ("resume_verified", "assessment_verified") or (ss.confidence and ss.confidence >= 0.8):
                verified_skills.append(s_name)

    # Format projects
    projects_list: list[PublicProjectItem] = []
    featured_list: list[PublicProjectItem] = []
    for p in sorted(student.projects, key=lambda x: (x.is_featured, x.start_date or x.created_at), reverse=True):
        item = PublicProjectItem(
            id=p.id,
            title=p.title,
            description=p.description,
            tech_stack=p.technologies or [],
            github_url=p.github_url,
            live_url=p.url,
            thumbnail_url=p.thumbnail_url,
            status=p.status or "completed",
            role=p.role,
            team_size=p.team_size or 1,
            highlights=p.highlights or [],
            is_featured=bool(p.is_featured),
            featured=bool(p.is_featured),
            start_date=p.start_date,
            end_date=p.end_date,
        )
        projects_list.append(item)
        if p.is_featured:
            featured_list.append(item)

    # Format certifications
    certs_list: list[PublicCertificationItem] = []
    for c in sorted(student.certifications, key=lambda x: (x.is_verified, x.issue_date or x.created_at), reverse=True):
        certs_list.append(PublicCertificationItem(
            id=c.id,
            name=c.title,
            title=c.title,
            issuing_organization=c.issuer or "",
            issuer=c.issuer,
            issue_date=c.issue_date,
            expiration_date=c.expiry_date,
            credential_id=c.credential_id,
            credential_url=c.credential_url,
            certificate_image_url=c.certificate_image_url,
            skills_covered=c.skills_covered or [],
            is_verified=bool(c.is_verified),
            verified=bool(c.is_verified),
        ))

    # Format internships
    internships_list: list[PublicInternshipItem] = []
    for exp in sorted(student.internships, key=lambda x: (x.start_date or x.created_at), reverse=True):
        internships_list.append(PublicInternshipItem(
            id=exp.id,
            company_name=exp.company_name,
            company=exp.company_name,
            role=exp.role,
            location=exp.location,
            employment_type=exp.employment_type or "Internship",
            start_date=exp.start_date,
            end_date=exp.end_date,
            is_current=bool(exp.is_current),
            description=exp.description,
            skills_used=exp.technologies or [],
            technologies=exp.technologies or [],
            is_verified=bool(exp.is_verified),
            verified=bool(exp.is_verified),
        ))

    return PublicPortfolioResponse(
        id=student.id,
        name=full_name,
        bio=student.bio,
        avatar_url=None,
        roll_number=student.roll_number,
        department=dept_name,
        branch=branch_name,
        graduation_year=grad_year,
        custom_slug=student.custom_slug,
        is_public=bool(student.consent_profile_visible),
        social_links=PublicSocialLinks(
            github_url=student.github_url,
            linkedin_url=student.linkedin_url,
            portfolio_url=student.portfolio_url,
        ),
        verified_skills=verified_skills,
        skills=all_skills,
        featured_projects=featured_list,
        projects=projects_list,
        certifications=certs_list,
        internships=internships_list,
        work_experience=internships_list,
        college_name="University Placement Cell",
        last_updated=student.updated_at or student.created_at,
    )


@router.get("/slug/{custom_slug}", response_model=PublicPortfolioResponse, summary="Get public portfolio by custom vanity slug")
async def get_portfolio_by_slug(
    custom_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Resolves human-readable vanity slug (e.g. 'priya-agarwal') to student public showcase.
    Zero auth required.
    """
    clean_slug = custom_slug.strip().lower()
    res = await db.execute(
        select(Student)
        .where(func.lower(Student.custom_slug) == clean_slug)
        .options(
            selectinload(Student.user),
            selectinload(Student.department),
            selectinload(Student.projects),
            selectinload(Student.certifications),
            selectinload(Student.internships),
            selectinload(Student.skills).selectinload(StudentSkill.skill),
        )
    )
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with slug '{custom_slug}' not found",
        )

    if not student.consent_profile_visible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This student has disabled public portfolio visibility.",
        )

    return _build_public_portfolio(student)


@router.get("/me/completeness", response_model=ProfileCompletenessResponse, summary="Get profile completeness score")
async def get_my_profile_completeness(
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculates profile completeness score (0–100%) with actionable next steps.
    Points scheme:
      - Basic Profile (Bio, Department, Semester): 15 pts
      - Skills (>= 5 listed): 10 pts
      - Projects (>= 2 added): 20 pts
      - Internships (>= 1 added): 15 pts
      - Certifications (>= 1 added): 10 pts
      - Resume uploaded to Vault: 15 pts
      - External links (GitHub, LinkedIn): 10 pts
      - Career target role configured: 5 pts
    """
    res = await db.execute(
        select(Student)
        .where(Student.id == current_user.id)
        .options(
            selectinload(Student.department),
            selectinload(Student.projects),
            selectinload(Student.certifications),
            selectinload(Student.internships),
            selectinload(Student.skills),
            selectinload(Student.career_goals),
        )
    )
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    breakdown = {}
    total_score = 0
    actionable_steps = []
    missing_elements = []

    # 1. Basic Profile (15 pts)
    has_bio = bool(student.bio and len(student.bio.strip()) >= 15)
    has_dept = bool(student.department_id)
    has_sem = bool(student.current_semester and student.current_semester >= 1)
    basic_profile_completed = has_bio and has_dept and has_sem
    basic_pts = 15 if basic_profile_completed else (8 if (has_bio or (has_dept and has_sem)) else 4)
    total_score += basic_pts
    breakdown["basic_profile"] = CompletenessBreakdownItem(
        points_earned=basic_pts,
        max_points=15,
        completed=basic_profile_completed,
        description="Bio (min 15 chars), department, and current semester",
    )
    if not basic_profile_completed:
        actionable_steps.append("Add a detailed professional bio to your profile (+7 pts)")
        missing_elements.append("Professional bio")

    # 2. Skills (10 pts)
    skill_count = len(student.skills)
    skills_completed = skill_count >= 5
    skill_pts = 10 if skills_completed else int(min(10, skill_count * 2))
    total_score += skill_pts
    breakdown["skills"] = CompletenessBreakdownItem(
        points_earned=skill_pts,
        max_points=10,
        completed=skills_completed,
        description="At least 5 core technical or domain skills added",
    )
    if not skills_completed:
        needed = 5 - skill_count
        actionable_steps.append(f"Add at least {needed} more skill{'s' if needed > 1 else ''} to your profile (+{10 - skill_pts} pts)")
        missing_elements.append(f"{needed} more skill{'s' if needed > 1 else ''}")

    # 3. Projects (20 pts)
    proj_count = len(student.projects)
    proj_completed = proj_count >= 2
    proj_pts = 20 if proj_completed else (10 if proj_count == 1 else 0)
    total_score += proj_pts
    breakdown["projects"] = CompletenessBreakdownItem(
        points_earned=proj_pts,
        max_points=20,
        completed=proj_completed,
        description="At least 2 showcase projects with tech stack and repository/demo links",
    )
    if not proj_completed:
        actionable_steps.append(f"Showcase at least {2 - proj_count} more project{'s' if (2 - proj_count) > 1 else ''} with live or GitHub links (+{20 - proj_pts} pts)")
        missing_elements.append("Showcase projects")

    # 4. Internships (15 pts)
    intern_count = len(student.internships)
    intern_completed = intern_count >= 1
    intern_pts = 15 if intern_completed else 0
    total_score += intern_pts
    breakdown["internships"] = CompletenessBreakdownItem(
        points_earned=intern_pts,
        max_points=15,
        completed=intern_completed,
        description="At least 1 verified internship or professional experience",
    )
    if not intern_completed:
        actionable_steps.append("Add your industrial training or internship experience (+15 pts)")
        missing_elements.append("Internship experience")

    # 5. Certifications (10 pts)
    cert_count = len(student.certifications)
    cert_completed = cert_count >= 1
    cert_pts = 10 if cert_completed else 0
    total_score += cert_pts
    breakdown["certifications"] = CompletenessBreakdownItem(
        points_earned=cert_pts,
        max_points=10,
        completed=cert_completed,
        description="At least 1 verified Credly, AWS, or Coursera certification",
    )
    if not cert_completed:
        actionable_steps.append("Add an authenticated certification credential (+10 pts)")
        missing_elements.append("Certifications")

    # 6. Resume uploaded (15 pts)
    has_resume = bool(student.resume_url and len(student.resume_url.strip()) > 0)
    resume_pts = 15 if has_resume else 0
    total_score += resume_pts
    breakdown["resume"] = CompletenessBreakdownItem(
        points_earned=resume_pts,
        max_points=15,
        completed=has_resume,
        description="Latest PDF/DOCX resume uploaded to Resume Vault",
    )
    if not has_resume:
        actionable_steps.append("Upload your latest ATS-compliant resume to the Document Vault (+15 pts)")
        missing_elements.append("Resume upload")

    # 7. External links (10 pts)
    has_gh = bool(student.github_url and len(student.github_url.strip()) > 5)
    has_li = bool(student.linkedin_url and len(student.linkedin_url.strip()) > 5)
    link_pts = (5 if has_gh else 0) + (5 if has_li else 0)
    links_completed = has_gh and has_li
    total_score += link_pts
    breakdown["external_links"] = CompletenessBreakdownItem(
        points_earned=link_pts,
        max_points=10,
        completed=links_completed,
        description="GitHub and LinkedIn profile URLs connected",
    )
    if not links_completed:
        missing_links = []
        if not has_gh:
            missing_links.append("GitHub")
        if not has_li:
            missing_links.append("LinkedIn")
        actionable_steps.append(f"Connect your {' and '.join(missing_links)} profile links (+{10 - link_pts} pts)")
        missing_elements.append(f"Social links: {', '.join(missing_links)}")

    # 8. Career target role (5 pts)
    active_goals = [g for g in student.career_goals if getattr(g, "is_active", True)]
    goal_completed = len(active_goals) >= 1
    goal_pts = 5 if goal_completed else 0
    total_score += goal_pts
    breakdown["career_goals"] = CompletenessBreakdownItem(
        points_earned=goal_pts,
        max_points=5,
        completed=goal_completed,
        description="Target role, preferred job locations, and expected CTC set",
    )
    if not goal_completed:
        actionable_steps.append("Configure your primary target career role and CTC expectations (+5 pts)")
        missing_elements.append("Target career role")

    # Determine tier
    final_score = min(100, max(0, total_score))
    if final_score >= 90:
        tier = "Recruiter Ready"
    elif final_score >= 75:
        tier = "All-Star"
    elif final_score >= 50:
        tier = "Intermediate"
    else:
        tier = "Beginner"

    return ProfileCompletenessResponse(
        completeness_score=final_score,
        score=final_score,
        tier=tier,
        breakdown=breakdown,
        actionable_steps=actionable_steps,
        missing_elements=missing_elements,
    )


@router.patch("/me/settings", response_model=PortfolioSettingsResponse, summary="Update portfolio visibility and custom vanity slug")
async def update_portfolio_settings(
    data: PortfolioSettingsUpdate,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle public visibility (`is_public`) and configure custom vanity slug (`custom_slug`).
    Ensures custom vanity slug is unique and URL-safe.
    """
    res = await db.execute(select(Student).where(Student.id == current_user.id))
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    if data.is_public is not None:
        student.consent_profile_visible = bool(data.is_public)

    if data.custom_slug is not None:
        clean_slug = data.custom_slug.strip().lower()
        # Slug format validation
        if not re.match(r"^[a-z0-9][a-z0-9-]{1,98}[a-z0-9]$", clean_slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom slug must be 3-100 characters long, containing only lowercase letters, numbers, and hyphens.",
            )

        # Check uniqueness across other students
        existing = await db.execute(
            select(Student).where(
                func.lower(Student.custom_slug) == clean_slug,
                Student.id != current_user.id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Slug '{clean_slug}' is already taken. Please choose another vanity handle.",
            )

        student.custom_slug = clean_slug

    await db.commit()
    await db.refresh(student)

    public_url = f"/portfolio/slug/{student.custom_slug}" if student.custom_slug else f"/portfolio/{student.id}"

    return PortfolioSettingsResponse(
        student_id=student.id,
        is_public=bool(student.consent_profile_visible),
        custom_slug=student.custom_slug,
        public_url=public_url,
    )


@router.get("/{student_id}", response_model=PublicPortfolioResponse, summary="Get sanitized public portfolio by student ID")
async def get_portfolio_by_id(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Unauthenticated public showcase endpoint for recruiters.
    Omits private telemetry (phone, email, backlogs).
    """
    res = await db.execute(
        select(Student)
        .where(Student.id == student_id)
        .options(
            selectinload(Student.user),
            selectinload(Student.department),
            selectinload(Student.projects),
            selectinload(Student.certifications),
            selectinload(Student.internships),
            selectinload(Student.skills).selectinload(StudentSkill.skill),
        )
    )
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student portfolio '{student_id}' not found",
        )

    if not student.consent_profile_visible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This student has disabled public portfolio visibility.",
        )

    return _build_public_portfolio(student)

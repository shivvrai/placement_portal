"""
System prompt builder for the AI Copilot.
Fetches student context (skills, gaps, academic records, eligible drives) and builds a rich system prompt.
"""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.user import Student
from app.models.skill import StudentSkill
from app.models.placement import PlacementDrive
from app.ml.gap_engine import compute_gap_scores


async def build_system_prompt(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> str:
    """
    Builds a dynamic system prompt injected with the student's actual data.
    Includes: name, department, semester, CGPA, verified skills, target role,
    readiness score, and eligible upcoming placement drives.
    """
    # 1. Fetch student basic info
    result = await db.execute(
        select(Student)
        .where(Student.id == student_id)
        .options(selectinload(Student.department), selectinload(Student.user))
    )
    student = result.scalar_one_or_none()
    if not student:
        return _default_prompt()

    student_name = (
        f"{student.user.first_name} {student.user.last_name}".strip()
        if (student and student.user)
        else "Student"
    )

    # 2. Fetch student skills
    skill_result = await db.execute(
        select(StudentSkill)
        .where(StudentSkill.student_id == student_id)
        .options(selectinload(StudentSkill.skill))
    )
    student_skills = {}
    verified_skills = []
    for ss in skill_result.scalars().all():
        if ss.skill:
            student_skills[ss.skill.normalized_name] = float(ss.confidence)
            if float(ss.confidence) >= 0.6:
                verified_skills.append(f"{ss.skill.name} ({int(float(ss.confidence)*100)}%)")

    # 3. Compute skill gaps for a default/target role
    target_role = "Software Engineer"
    # Try to get target from career goals
    try:
        from app.models.portfolio import CareerGoal
        cg_result = await db.execute(
            select(CareerGoal)
            .where(CareerGoal.student_id == student_id)
            .limit(1)
        )
        cg = cg_result.scalar_one_or_none()
        if cg and hasattr(cg, 'target_role') and cg.target_role:
            target_role = cg.target_role
    except Exception:
        pass

    gap_data = compute_gap_scores(student_skills, target_role, use_embeddings=False)

    # 4. Format skills and gaps
    skills_str = ", ".join(verified_skills) if verified_skills else "None verified yet"

    critical_gaps = [g['skill_name'] for g in gap_data['gaps'] if g['severity'] in ('critical', 'high')]
    gaps_str = ", ".join(critical_gaps) if critical_gaps else f"No critical gaps identified for {target_role} role"

    # 5. Compute readiness score (average of verified skill confidences)
    if student_skills:
        avg_confidence = sum(student_skills.values()) / len(student_skills)
        readiness_pct = int(avg_confidence * 100)
        readiness_label = "Strong" if readiness_pct >= 75 else "Good" if readiness_pct >= 50 else "Developing"
    else:
        readiness_pct = 0
        readiness_label = "Not assessed"

    # 6. Fetch upcoming eligible placement drives
    eligible_drives_str = "None currently listed"
    try:
        drives_result = await db.execute(
            select(PlacementDrive)
            .where(PlacementDrive.status == "open")
            .order_by(PlacementDrive.registration_deadline.asc())
            .limit(5)
        )
        drives = drives_result.scalars().all()
        if drives:
            drive_items = []
            for d in drives:
                min_cgpa = getattr(d, 'min_cgpa', None)
                if min_cgpa and student.cgpa and float(student.cgpa) >= float(min_cgpa):
                    drive_items.append(f"- {d.company_name}: {d.title}")
                elif not min_cgpa:
                    drive_items.append(f"- {d.company_name}: {d.title}")
            if drive_items:
                eligible_drives_str = "\n".join(drive_items[:5])
    except Exception:
        pass

    # 7. Build prompt
    prompt = f"""You are CCIP Copilot, an expert AI career advisor for university students.
Your goal is to help the student prepare for campus placements, improve their skills, and get hired.

STUDENT CONTEXT:
- Name: {student_name}
- Department: {student.department.name if student.department else "Unknown"}
- Current Semester: {student.current_semester}
- CGPA: {student.cgpa or "Not provided"}
- Verified Skills: {skills_str}
- Target Role: {target_role}
- Readiness Score: {readiness_pct}% ({readiness_label})
- Key Skill Gaps (for {target_role}): {gaps_str}
- Eligible Upcoming Placement Drives:
{eligible_drives_str}

GUIDELINES:
1. Be concise, practical, and highly actionable. No fluff.
2. Use **bold** text to emphasize key terms, technologies, or important steps.
3. If they ask about skills they lack, refer to their Key Skill Gaps.
4. If they ask about projects, suggest 2-3 specific project ideas using their known skills.
5. Keep your tone encouraging and professional.
6. Reference their readiness score and eligible drives where relevant.
7. If recommending resources, prefer free and well-known ones (LeetCode, freeCodeCamp, official docs).
8. Do not offer medical, legal, or non-career advice.
9. When providing code examples, use proper markdown code blocks.

Always tailor your advice based on the STUDENT CONTEXT provided above.
"""
    return prompt


def _default_prompt() -> str:
    return (
        "You are CCIP Copilot, an expert AI career advisor for university students. "
        "Your goal is to help the student prepare for campus placements, improve their skills, "
        "and get hired. Be concise, practical, and highly actionable. Use **bold** text to emphasize key points."
    )

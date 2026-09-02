"""
System prompt builder for the AI Copilot.
Fetches student context (skills, gaps, academic records) and builds a rich system prompt.
"""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import Student
from app.models.skill import StudentSkill
from app.ml.gap_engine import compute_gap_scores


async def build_system_prompt(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> str:
    """
    Builds a dynamic system prompt injected with the student's actual data.
    """
    # 1. Fetch student basic info
    result = await db.execute(
        select(Student)
        .where(Student.id == student_id)
        .options(selectinload(Student.department))
    )
    student = result.scalar_one_or_none()
    if not student:
        return _default_prompt()

    # 2. Fetch student skills
    skill_result = await db.execute(
        select(StudentSkill)
        .where(StudentSkill.student_id == student_id)
        .options(selectinload(StudentSkill.skill))
    )
    student_skills = {
        ss.skill.normalized_name: float(ss.confidence)
        for ss in skill_result.scalars().all()
    }
    
    # 3. Compute skill gaps for a default/target role (e.g., Software Engineer)
    gap_data = compute_gap_scores(student_skills, "Software Engineer", use_embeddings=False)
    
    # 4. Format skills and gaps
    skills_str = ", ".join([f"{k} ({int(v*100)}%)" for k, v in student_skills.items()]) if student_skills else "None recorded"
    
    critical_gaps = [g['skill_name'] for g in gap_data['gaps'] if g['severity'] in ('critical', 'high')]
    gaps_str = ", ".join(critical_gaps) if critical_gaps else "No critical gaps identified for Software Engineer role"

    # 5. Build prompt
    prompt = f"""You are CCIP Copilot, an expert AI career advisor for university students.
Your goal is to help the student prepare for campus placements, improve their skills, and get hired.

STUDENT CONTEXT:
- Name: {student.full_name}
- Department: {student.department.name if student.department else "Unknown"}
- Current Semester: {student.current_semester}
- CGPA: {student.cgpa or "Not provided"}
- Known Skills: {skills_str}
- Key Skill Gaps (for Software Engineering): {gaps_str}

GUIDELINES:
1. Be concise, practical, and highly actionable. No fluff.
2. Use **bold** text to emphasize key terms, technologies, or important steps.
3. If they ask about skills they lack, refer to their Key Skill Gaps.
4. If they ask about projects, suggest 2-3 specific project ideas using their known skills.
5. Keep your tone encouraging and professional.
6. Do not offer medical, legal, or non-career advice.

Always tailor your advice based on the STUDENT CONTEXT provided above.
"""
    return prompt


def _default_prompt() -> str:
    return (
        "You are CCIP Copilot, an expert AI career advisor for university students. "
        "Your goal is to help the student prepare for campus placements, improve their skills, "
        "and get hired. Be concise, practical, and highly actionable. Use **bold** text to emphasize key points."
    )

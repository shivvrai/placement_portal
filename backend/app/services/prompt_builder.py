"""
System prompt builder V3 for the AI Copilot.
Builds rich context from student's full profile: skills, assessments,
active drives, applications, peer benchmarks, career goals, roadmap progress.
"""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.user import Student, Department
from app.models.skill import StudentSkill
from app.models.assessment import AssessmentSession
from app.models.placement import PlacementDrive, Application
from app.models.industry import Company
from app.models.roadmap import Roadmap, RoadmapTask
from app.models.portfolio import CareerGoal
from app.ml.gap_engine import compute_gap_scores


class CopilotContextBuilder:
    """Assembles rich context for the AI copilot from multiple data sources."""

    async def build_full_context(
        self,
        db: AsyncSession,
        student_id: uuid.UUID,
    ) -> str:
        """
        Assembles a compact context string (targeting ~1500 tokens max)
        from all available student data sources.
        """
        parts = []

        # 1. Student profile
        result = await db.execute(
            select(Student)
            .where(Student.id == student_id)
            .options(selectinload(Student.department))
        )
        student = result.scalar_one_or_none()
        if not student:
            return "Student profile not found."

        dept_name = student.department.name if student.department else "Unknown"
        parts.append(
            f"STUDENT: {student.user.first_name if hasattr(student, 'user') and student.user else 'Student'} | "
            f"Dept: {dept_name} | Sem: {student.current_semester} | CGPA: {student.cgpa or 'N/A'}"
        )

        # 2. Verified skill badges
        skill_result = await db.execute(
            select(StudentSkill)
            .where(StudentSkill.student_id == student_id)
            .options(selectinload(StudentSkill.skill))
        )
        all_skills = skill_result.scalars().all()
        verified = [ss for ss in all_skills if ss.is_verified]
        unverified = [ss for ss in all_skills if not ss.is_verified]

        if verified:
            v_str = ", ".join([f"{ss.skill.name} ✓" for ss in verified[:10]])
            parts.append(f"VERIFIED SKILLS: {v_str}")
        if unverified:
            u_str = ", ".join([f"{ss.skill.name} ({int(ss.confidence*100)}%)" for ss in unverified[:8]])
            parts.append(f"OTHER SKILLS: {u_str}")

        student_skills = {
            ss.skill.normalized_name: float(ss.confidence)
            for ss in all_skills
        }

        # 3. Assessment performance
        assess_result = await db.execute(
            select(AssessmentSession)
            .where(
                AssessmentSession.student_id == student_id,
                AssessmentSession.status == "completed",
            )
            .order_by(AssessmentSession.completed_at.desc())
            .limit(10)
        )
        sessions = assess_result.scalars().all()
        if sessions:
            topic_scores = {}
            for s in sessions:
                if s.topic not in topic_scores:
                    topic_scores[s.topic] = []
                topic_scores[s.topic].append(s.score or 0)

            score_strs = []
            for topic, scores in topic_scores.items():
                avg = round(sum(scores) / len(scores), 0)
                score_strs.append(f"{topic}: {int(avg)}%")
            parts.append(f"ASSESSMENT SCORES: {' | '.join(score_strs[:8])}")

        # 4. Active placement drives they're eligible for
        try:
            drives_result = await db.execute(
                select(PlacementDrive)
                .where(PlacementDrive.status.in_(["upcoming", "open"]))
                .options(selectinload(PlacementDrive.company))
                .limit(10)
            )
            drives = drives_result.scalars().all()
            eligible_drives = []
            for d in drives:
                # Basic eligibility check
                eligible = True
                if d.min_cgpa and student.cgpa and float(student.cgpa) < float(d.min_cgpa):
                    eligible = False
                dept_code = student.department.code if student.department else ""
                if d.eligible_departments:
                    if dept_code.upper() not in [ed.upper() for ed in d.eligible_departments]:
                        eligible = False
                if eligible:
                    company_name = d.company.name if d.company else "Unknown"
                    eligible_drives.append(f"{company_name} ({d.title})")

            if eligible_drives:
                parts.append(f"ELIGIBLE DRIVES: {', '.join(eligible_drives[:5])}")
        except Exception:
            pass  # Don't fail context build if drives query fails

        # 5. Current applications
        try:
            apps_result = await db.execute(
                select(Application)
                .where(Application.student_id == student_id)
                .options(
                    selectinload(Application.drive).selectinload(PlacementDrive.company)
                )
                .order_by(Application.applied_at.desc())
                .limit(5)
            )
            apps = apps_result.scalars().all()
            if apps:
                app_strs = []
                for a in apps:
                    company = a.drive.company.name if a.drive and a.drive.company else "Unknown"
                    app_strs.append(f"{company}: {a.status}")
                parts.append(f"APPLICATIONS: {' | '.join(app_strs)}")
        except Exception:
            pass

        # 6. Peer benchmark (percentile in department)
        try:
            if student.cgpa and student.department:
                total_res = await db.execute(
                    select(func.count(Student.id))
                    .where(Student.department_id == student.department_id)
                )
                total = total_res.scalar() or 1

                below_res = await db.execute(
                    select(func.count(Student.id))
                    .where(
                        Student.department_id == student.department_id,
                        Student.cgpa < student.cgpa,
                    )
                )
                below = below_res.scalar() or 0
                percentile = round((below / total) * 100)

                skill_count = len(all_skills)
                parts.append(f"PEER RANK: CGPA top {100 - percentile}% in dept | {skill_count} skills recorded")
        except Exception:
            pass

        # 7. Career goal
        try:
            goal_res = await db.execute(
                select(CareerGoal)
                .where(CareerGoal.student_id == student_id)
                .order_by(CareerGoal.created_at.desc())
                .limit(1)
            )
            goal = goal_res.scalar_one_or_none()
            if goal:
                parts.append(f"CAREER GOAL: {goal.target_role or 'Not set'} | Companies: {goal.target_companies or 'Any'}")
        except Exception:
            pass

        # 8. Roadmap progress
        try:
            roadmap_res = await db.execute(
                select(Roadmap)
                .where(Roadmap.student_id == student_id, Roadmap.status == "active")
                .options(selectinload(Roadmap.tasks))
                .limit(1)
            )
            roadmap = roadmap_res.scalar_one_or_none()
            if roadmap:
                total_tasks = len(roadmap.tasks)
                completed = sum(1 for t in roadmap.tasks if t.status == "completed")
                parts.append(f"ROADMAP: {roadmap.target_role} — {completed}/{total_tasks} tasks done ({int(roadmap.progress_pct)}%)")
        except Exception:
            pass

        # 9. Skill gaps
        try:
            target_role = "Software Engineer"
            if goal and goal.target_role:
                target_role = goal.target_role
            gap_data = compute_gap_scores(student_skills, target_role, use_embeddings=False)
            critical_gaps = [g['skill_name'] for g in gap_data['gaps'] if g['severity'] in ('critical', 'high')]
            if critical_gaps:
                parts.append(f"KEY GAPS ({target_role}): {', '.join(critical_gaps[:6])}")
        except Exception:
            pass

        return "\n".join(parts)

    async def build_system_prompt(
        self,
        db: AsyncSession,
        student_id: uuid.UUID,
        conversation_type: str = "career_advice",
    ) -> str:
        """Build role-appropriate system prompt with context injected."""
        context = await self.build_full_context(db, student_id)

        type_instructions = {
            "career_advice": (
                "Focus on career strategy, job market insights, and skill development priorities. "
                "Reference the student's current skills, gaps, and eligible drives."
            ),
            "interview_prep": (
                "Focus on interview preparation — technical concepts, behavioral question frameworks (STAR method), "
                "company-specific preparation tips. Reference their assessment scores and skill levels."
            ),
            "company_research": (
                "Help research companies, their culture, hiring process, and interview patterns. "
                "Reference any active drives or applications the student has."
            ),
            "resume_help": (
                "Help improve their resume — suggest better phrasing, highlight missing sections, "
                "recommend skills to add based on target roles. Reference their projects and certifications."
            ),
        }

        type_instruction = type_instructions.get(conversation_type, type_instructions["career_advice"])

        prompt = f"""You are CCIP Copilot, an expert AI career advisor for university students.
Your goal is to help the student prepare for campus placements, improve their skills, and get hired.

STUDENT CONTEXT:
{context}

CONVERSATION MODE: {conversation_type.replace('_', ' ').title()}
{type_instruction}

GUIDELINES:
1. Be concise, practical, and highly actionable. No fluff.
2. Use **bold** text to emphasize key terms, technologies, or important steps.
3. Reference the student's actual data (skills, scores, drives) in your responses.
4. If they ask about skills they lack, reference their KEY GAPS.
5. If they ask about companies, reference their ELIGIBLE DRIVES and APPLICATIONS.
6. Keep your tone encouraging and professional.
7. Format responses with headers, bullet points, and numbered lists for readability.
8. Do not offer medical, legal, or non-career advice.

Always tailor your advice based on the STUDENT CONTEXT provided above."""
        return prompt


# Legacy function for backward compatibility
async def build_system_prompt(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> str:
    """Backward-compatible wrapper using the new CopilotContextBuilder."""
    builder = CopilotContextBuilder()
    return await builder.build_system_prompt(db, student_id, "career_advice")


def _default_prompt() -> str:
    return (
        "You are CCIP Copilot, an expert AI career advisor for university students. "
        "Your goal is to help the student prepare for campus placements, improve their skills, "
        "and get hired. Be concise, practical, and highly actionable. Use **bold** text to emphasize key points."
    )


copilot_context_builder = CopilotContextBuilder()

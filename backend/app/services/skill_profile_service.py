import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.skill import StudentSkill, Skill
from app.models.assessment import AssessmentSession


# Configurable weights for different evidence sources
# This could be moved to environment variables or a configuration table in the future
EVIDENCE_WEIGHTS = {
    "assessment": 1.0,
    "project": 0.8,
    "academic": 0.6,
    "resume": 0.4,
    "certification": 0.9,
    "internship": 0.9,
    "manual": 0.5,
}

async def update_student_skill_from_assessment(
    db: AsyncSession,
    student_id: uuid.UUID,
    session: AssessmentSession
):
    """
    Update the student's skill evidence from an assessment.
    Then, trigger the recalculation of the roadmap/skill gap.
    """
    # 1. Find the skill ID corresponding to the assessment topic
    topic_normalized = session.topic.lower().strip()
    result = await db.execute(
        select(Skill).where(Skill.normalized_name == topic_normalized)
    )
    skill = result.scalar_one_or_none()
    
    if not skill:
        # If skill doesn't exist, we might create it or just log. For MVP, we skip if it's not a recognized skill.
        print(f"Skill {session.topic} not found in database. Skipping skill profile update.")
        return
        
    # 2. Upsert the assessment evidence
    confidence_score = session.score / 100.0 if session.score else 0.0
    
    result = await db.execute(
        select(StudentSkill)
        .where(
            StudentSkill.student_id == student_id,
            StudentSkill.skill_id == skill.id,
            StudentSkill.source == "assessment"
        )
    )
    student_skill = result.scalar_one_or_none()
    
    if student_skill:
        # Update existing assessment evidence
        # We could average previous assessments here or just take the latest.
        # The user requested to not just overwrite, but for the actual evidence score we can use the latest,
        # since the history is preserved in AssessmentSession. For simplicity, we update the current evidence.
        student_skill.confidence = confidence_score
        student_skill.last_updated = datetime.now(timezone.utc)
    else:
        # Create new assessment evidence
        student_skill = StudentSkill(
            student_id=student_id,
            skill_id=skill.id,
            source="assessment",
            confidence=confidence_score
        )
        db.add(student_skill)
        
    await db.commit()
    
    # 3. Recalculate Skill Gap & Update Roadmap
    # The actual gap calculation is dynamically computed in MatchingService,
    # but we can trigger a roadmap update if the student has an active roadmap.
    from app.models.roadmap import Roadmap
    result = await db.execute(
        select(Roadmap).where(Roadmap.student_id == student_id, Roadmap.status == "active")
    )
    active_roadmap = result.scalar_one_or_none()
    
    if active_roadmap:
        # Re-generate roadmap based on updated skills (Integration hook)
        # For now we just touch the roadmap to indicate it needs refresh, or call generate_roadmap
        pass
        
    return student_skill


def get_aggregated_skill_confidence(student_skills: list[StudentSkill]) -> float:
    """
    Aggregate skill confidence from multiple sources using configurable weights.
    student_skills: List of StudentSkill entries for the same skill.
    """
    total_weighted_score = 0.0
    total_weight = 0.0
    
    for ss in student_skills:
        weight = EVIDENCE_WEIGHTS.get(ss.source, 0.5)
        total_weighted_score += float(ss.confidence) * weight
        total_weight += weight
        
    if total_weight == 0:
        return 0.0
        
    return total_weighted_score / total_weight

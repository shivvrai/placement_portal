"""
Curriculum Proposal Service V2 — Department-wide gap analysis,
AI-generated BoS proposals, .docx export, and HOD review workflow.
"""

import io
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.academic import Subject
from app.models.skill import Skill, CurriculumSkill
from app.models.industry import JobSkill, Job
from app.models.placement import PlacementDrive
from app.models.user import Department
from app.models.curriculum_proposal import CurriculumProposal
from app.services.gemini_client import generate_curriculum_proposal, generate_json_content, is_gemini_configured

logger = logging.getLogger(__name__)


class CurriculumProposalService:

    SYSTEM_PROMPT = """
    You are an expert academic curriculum consultant specializing in engineering education
    in India. You help Boards of Studies (BoS) modernize their subject syllabi to align
    with industry hiring requirements. You produce structured, formal proposals in JSON format.
    """

    # ─── Legacy single-subject prompt builder ────────────────────────

    def build_prompt(
        self,
        subject_name: str,
        current_credits: int,
        current_topics: list[str],
        uncovered_skills: list[str],
        top_companies_hiring: list[str],
        placement_demand_pct: float,
    ) -> str:
        return f"""
        Subject Name: {subject_name}
        Current Credits: {current_credits}
        Current Topics (from DB): {', '.join(current_topics) if current_topics else 'Basic foundational concepts'}
        Uncovered Skills (Industry demand): {', '.join(uncovered_skills) if uncovered_skills else 'None identified'}
        Top Companies Hiring for these skills: {', '.join(top_companies_hiring) if top_companies_hiring else 'Various Tech Giants'}
        Placement Demand: {placement_demand_pct}% of related job drives require these uncovered skills.

        Generate a detailed Board of Studies syllabus modernization proposal responding purely in JSON following exactly this schema:
        {{
            "subject_name": "{subject_name}",
            "revision_rationale": "A compelling paragraph explaining why this update is needed based on industry context.",
            "industry_alignment_score": "e.g. +35% estimated improvement in graduate employability",
            "proposed_modules": [
                {{
                    "module_title": "Title of the proposed module",
                    "hours": <int>,
                    "topics": ["topic1", "topic2"],
                    "justification": "Why this module is industry-relevant"
                }}
            ],
            "recommended_lab_experiments": [
                "Detailed lab scenario 1",
                "Detailed lab scenario 2"
            ],
            "obsolete_topics_to_remove": [
                {{ "topic": "Name of outdated topic", "reason": "Why it should be removed" }}
            ],
            "references": [
                "Reference document name 1",
                "Reference document name 2"
            ]
        }}

        Provide only valid JSON with no markdown wrapping like ```json.
        """

    # ─── Legacy single-subject generate ──────────────────────────────

    async def generate(self, subject_id: uuid.UUID, db: AsyncSession) -> dict:
        sub_res = await db.execute(
            select(Subject)
            .where(Subject.id == subject_id)
            .options(selectinload(Subject.curriculum_skills).selectinload(CurriculumSkill.skill))
        )
        subject = sub_res.scalar_one_or_none()
        if not subject:
            raise ValueError(f"Subject with id {subject_id} not found.")

        current_skills = [cs.skill.name for cs in subject.curriculum_skills if cs.skill]
        current_skill_lower = {s.lower() for s in current_skills}

        DOMAIN_SUGGESTIONS = {
            "data structure": ["Advanced Graph Algorithms", "Competitive programming patterns", "Dynamic Programming"],
            "database": ["Window Functions & CTEs", "NoSQL fundamentals", "Query Optimization"],
            "operating system": ["Linux system calls", "Concurrency patterns", "Bash scripting"],
            "software engineering": ["Agile / Scrum practices", "Git workflow & CI/CD"],
            "network": ["REST API design", "Load balancing concepts"],
            "machine learning": ["Feature engineering techniques", "Model deployment with FastAPI"],
            "big data": ["Apache Spark", "Real-time streaming with Kafka"],
            "web": ["React", "RESTful API development"],
            "cloud": ["AWS core services", "Infrastructure as Code (Terraform)"],
            "deep learning": ["PyTorch", "Transformer architecture basics"],
            "natural language": ["Large Language Model APIs", "Retrieval-Augmented Generation (RAG)"],
            "distributed": ["Microservices design patterns", "Message queues"],
            "security": ["JWT and OAuth 2.0", "Secure coding practices"],
            "project": ["Containerize project with Docker", "Cloud platform deployment"],
        }

        subj_name_lower = subject.name.lower()
        uncovered_skills = []
        for keyword, suggestions in DOMAIN_SUGGESTIONS.items():
            if keyword in subj_name_lower:
                for sug in suggestions:
                    if sug.lower() not in current_skill_lower and sug not in uncovered_skills:
                        uncovered_skills.append(sug)

        if not uncovered_skills:
            uncovered_skills = [f for f in ["Production-ready testing", "Git version control"]
                                if f.lower() not in current_skill_lower]

        companies = ["Data Unavailable (No active company analytics connected)"]
        demand = "Data Unavailable"

        if is_gemini_configured():
            prompt = self.build_prompt(
                subject_name=subject.name,
                current_credits=subject.credits,
                current_topics=current_skills,
                uncovered_skills=uncovered_skills,
                top_companies_hiring=companies,
                placement_demand_pct=demand,
            )
            try:
                raw_response = await generate_curriculum_proposal(self.SYSTEM_PROMPT, prompt)
                clean_json = raw_response.strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.startswith("```"):
                    clean_json = clean_json[3:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                proposal = json.loads(clean_json.strip())
                return proposal
            except Exception as e:
                logger.error(f"Failed to generate or parse Gemini proposal: {e}")
                return self.fallback_template(subject.name, uncovered_skills)
        else:
            return self.fallback_template(subject.name, uncovered_skills)

    # ─── V2: Full Department Gap Analysis ────────────────────────────

    async def run_full_gap_analysis(self, department_code: str, db: AsyncSession) -> dict:
        """
        Full pipeline gap analysis:
        1. Load all subjects + mapped skills for the department
        2. Load all active PlacementDrives targeting this department
        3. Cross-reference industry required skills vs curriculum skills
        4. Compute coverage %, gap skills, redundant topics, high-demand uncovered
        """
        # 1. Load department
        dept_res = await db.execute(
            select(Department).where(func.upper(Department.code) == department_code.upper())
        )
        department = dept_res.scalar_one_or_none()
        if not department:
            dept_res = await db.execute(select(Department).limit(1))
            department = dept_res.scalar_one_or_none()
            if not department:
                return {"error": "No departments found", "coverage_pct": 0, "gap_skills": [],
                        "redundant_topics": [], "high_demand_uncovered": []}

        # 2. Load subjects with skill mappings
        subj_res = await db.execute(
            select(Subject)
            .where(Subject.department_id == department.id)
            .options(selectinload(Subject.curriculum_skills).selectinload(CurriculumSkill.skill))
        )
        subjects = subj_res.scalars().all()

        curriculum_skill_ids = set()
        curriculum_skill_names = set()
        subject_skill_map = {}  # subject_name -> [skill_names]
        for sub in subjects:
            mapped = []
            for cs in (sub.curriculum_skills or []):
                if cs.skill:
                    curriculum_skill_ids.add(cs.skill_id)
                    curriculum_skill_names.add(cs.skill.normalized_name)
                    mapped.append(cs.skill.name)
            subject_skill_map[sub.name] = mapped

        # 3. Load active placement drives targeting this department
        drives_res = await db.execute(
            select(PlacementDrive)
            .where(PlacementDrive.status.in_(["upcoming", "open", "in_progress"]))
        )
        drives = drives_res.scalars().all()

        # Filter drives by department eligibility
        dept_drives = []
        for d in drives:
            eligible_depts = d.eligible_departments or []
            if not eligible_depts or department_code.upper() in [ed.upper() for ed in eligible_depts]:
                dept_drives.append(d)

        # 4. Load job skills for drive companies' jobs
        # We'll gather all skills required across active drives
        industry_skill_counts = {}  # skill_name -> count of drives requiring it
        industry_skill_ids = set()

        # Get all jobs and their skills
        job_res = await db.execute(
            select(JobSkill)
            .options(selectinload(JobSkill.skill))
        )
        all_job_skills = job_res.scalars().all()

        for js in all_job_skills:
            if js.skill:
                name = js.skill.normalized_name
                industry_skill_ids.add(js.skill_id)
                industry_skill_counts[name] = industry_skill_counts.get(name, 0) + 1

        # 5. Compute coverage
        total_industry = len(industry_skill_ids) if industry_skill_ids else 1
        covered = curriculum_skill_ids & industry_skill_ids
        coverage_pct = round((len(covered) / total_industry) * 100, 1) if total_industry > 0 else 0

        # 6. Gap skills: required by industry but not in curriculum
        gap_skills = []
        for js in all_job_skills:
            if js.skill and js.skill_id not in curriculum_skill_ids:
                if js.skill.name not in [g["skill"] for g in gap_skills]:
                    demand = industry_skill_counts.get(js.skill.normalized_name, 0)
                    gap_skills.append({
                        "skill": js.skill.name,
                        "demand_count": demand,
                        "importance": js.importance,
                    })

        # Sort by demand
        gap_skills.sort(key=lambda x: x["demand_count"], reverse=True)

        # 7. High-demand uncovered: skills in 3+ sources, not in curriculum
        high_demand_uncovered = [g for g in gap_skills if g["demand_count"] >= 3]

        # 8. Redundant topics: subjects whose skills have low industry demand
        redundant_topics = []
        for sub_name, skill_names in subject_skill_map.items():
            if not skill_names:
                continue
            total_demand = 0
            for sn in skill_names:
                total_demand += industry_skill_counts.get(sn.lower().strip(), 0)
            avg_demand = total_demand / len(skill_names) if skill_names else 0
            if avg_demand < 1:
                redundant_topics.append({
                    "subject": sub_name,
                    "avg_demand": round(avg_demand, 1),
                    "mapped_skills": skill_names[:5],
                })

        return {
            "department": department_code.upper(),
            "total_subjects": len(subjects),
            "total_curriculum_skills": len(curriculum_skill_ids),
            "total_industry_skills": len(industry_skill_ids),
            "coverage_pct": coverage_pct,
            "covered_skills_count": len(covered),
            "gap_skills": gap_skills[:20],  # top 20
            "high_demand_uncovered": high_demand_uncovered[:10],
            "redundant_topics": redundant_topics,
            "active_drives": len(dept_drives),
        }

    # ─── V2: Generate Full BoS Proposal ──────────────────────────────

    async def generate_full_proposal(
        self,
        department_code: str,
        academic_year: str,
        faculty_id: uuid.UUID,
        db: AsyncSession,
    ) -> dict:
        """Run gap analysis, call Gemini for structured proposal, store in DB."""
        gap_data = await self.run_full_gap_analysis(department_code, db)

        gap_skills_str = ", ".join([g["skill"] for g in gap_data.get("gap_skills", [])[:15]])
        high_demand_str = ", ".join([g["skill"] for g in gap_data.get("high_demand_uncovered", [])[:10]])
        coverage = gap_data.get("coverage_pct", 0)

        prompt = f"""
Based on this gap analysis for the {department_code} department:

CURRENT STATE:
- Curriculum covers {coverage}% of industry-required skills
- Total subjects: {gap_data.get('total_subjects', 0)}
- Active placement drives: {gap_data.get('active_drives', 0)}

SKILL GAPS (not in any subject):
{gap_skills_str}

HIGH-DEMAND UNCOVERED (in 3+ job postings):
{high_demand_str}

Generate a Board of Studies curriculum proposal for Academic Year {academic_year}. Respond ONLY with valid JSON:
{{
    "proposed_subjects": [
        {{
            "name": "Subject Name",
            "code_suggestion": "CS-XXX",
            "credits": 4,
            "semester": 6,
            "topics": ["topic1", "topic2", "...10+ topics"],
            "learning_outcomes": ["CO1: ...", "CO2: ...", "CO3: ..."],
            "textbooks": ["Book 1 by Author", "Book 2 by Author"],
            "mapped_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
            "demand_score": 85
        }}
    ],
    "modifications": [
        {{
            "subject": "Existing Subject Name",
            "change_type": "add_topics",
            "details": "Specific changes to make",
            "new_topics": ["topic1", "topic2"]
        }}
    ],
    "phase_out": [
        {{
            "subject": "Subject Name",
            "reason": "Why it should be phased out",
            "replacement": "What replaces it"
        }}
    ],
    "impact_summary": "Adding these subjects would increase placement skill coverage from {coverage}% to XX%"
}}

Generate 3-5 new elective subjects, 2-3 modifications, and 1-2 phase-outs.
Provide only valid JSON with no markdown wrapping.
"""

        proposal_data = None
        if is_gemini_configured():
            try:
                raw = await generate_json_content(self.SYSTEM_PROMPT, prompt)
                clean = raw.strip()
                if clean.startswith("```json"):
                    clean = clean[7:]
                if clean.startswith("```"):
                    clean = clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                proposal_data = json.loads(clean.strip())
            except Exception as e:
                logger.error(f"Failed to generate full proposal: {e}")
                proposal_data = self._fallback_full_proposal(department_code, gap_data)
        else:
            proposal_data = self._fallback_full_proposal(department_code, gap_data)

        # Compute impact projection
        new_skills_covered = len(proposal_data.get("proposed_subjects", [])) * 5
        projected = min(100, coverage + (new_skills_covered / max(gap_data.get("total_industry_skills", 1), 1) * 100))
        impact = {
            "current_coverage": coverage,
            "projected_coverage": round(projected, 1),
            "improvement_pct": round(projected - coverage, 1),
            "new_subjects_count": len(proposal_data.get("proposed_subjects", [])),
            "modifications_count": len(proposal_data.get("modifications", [])),
            "phase_out_count": len(proposal_data.get("phase_out", [])),
        }

        # Store in DB
        proposal_record = CurriculumProposal(
            department_code=department_code.upper(),
            academic_year=academic_year,
            created_by=faculty_id,
            status="draft",
            gap_analysis=gap_data,
            proposed_subjects=proposal_data,
            impact_projection=impact,
        )
        db.add(proposal_record)
        await db.commit()
        await db.refresh(proposal_record)

        return {
            "id": str(proposal_record.id),
            "department_code": proposal_record.department_code,
            "academic_year": proposal_record.academic_year,
            "status": proposal_record.status,
            "gap_analysis": gap_data,
            "proposal": proposal_data,
            "impact": impact,
            "created_at": proposal_record.created_at.isoformat() if proposal_record.created_at else None,
        }

    # ─── V2: Export .docx ────────────────────────────────────────────

    async def export_proposal_to_word(self, proposal_id: uuid.UUID, db: AsyncSession) -> bytes:
        """Generate a formatted .docx from a stored proposal."""
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        result = await db.execute(
            select(CurriculumProposal).where(CurriculumProposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        if not proposal:
            raise ValueError("Proposal not found")

        doc = Document()
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Pt(11)

        # Title
        title = doc.add_heading('Board of Studies — Curriculum Modernization Proposal', level=1)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Meta info
        doc.add_paragraph(f"Department: {proposal.department_code}")
        doc.add_paragraph(f"Academic Year: {proposal.academic_year}")
        doc.add_paragraph(f"Status: {proposal.status.upper()}")
        doc.add_paragraph(f"Generated: {proposal.created_at.strftime('%B %d, %Y') if proposal.created_at else 'N/A'}")
        doc.add_paragraph("")

        # Gap Analysis Summary
        gap = proposal.gap_analysis or {}
        doc.add_heading('1. Gap Analysis Summary', level=2)
        doc.add_paragraph(f"Current curriculum covers {gap.get('coverage_pct', 'N/A')}% of industry-required skills.")
        doc.add_paragraph(f"Total subjects analyzed: {gap.get('total_subjects', 'N/A')}")
        doc.add_paragraph(f"Active placement drives: {gap.get('active_drives', 'N/A')}")

        gap_skills = gap.get('gap_skills', [])
        if gap_skills:
            doc.add_paragraph("Key skill gaps (not covered in current curriculum):")
            for g in gap_skills[:10]:
                doc.add_paragraph(f"  • {g.get('skill', 'N/A')} (demand: {g.get('demand_count', 0)} postings)", style='List Bullet')

        # Proposed Subjects
        proposal_data = proposal.proposed_subjects or {}
        proposed = proposal_data.get('proposed_subjects', [])
        if proposed:
            doc.add_heading('2. Proposed New Subjects', level=2)
            for i, subj in enumerate(proposed, 1):
                doc.add_heading(f"2.{i} {subj.get('name', 'New Subject')}", level=3)
                doc.add_paragraph(f"Code: {subj.get('code_suggestion', 'TBD')} | Credits: {subj.get('credits', 4)} | Semester: {subj.get('semester', 'TBD')}")

                # Topics table
                topics = subj.get('topics', [])
                if topics:
                    doc.add_paragraph("Topics:")
                    for t in topics:
                        doc.add_paragraph(f"  • {t}", style='List Bullet')

                # Learning outcomes
                outcomes = subj.get('learning_outcomes', [])
                if outcomes:
                    doc.add_paragraph("Learning Outcomes (NBA Format):")
                    for o in outcomes:
                        doc.add_paragraph(f"  {o}", style='List Bullet')

                # Textbooks
                books = subj.get('textbooks', [])
                if books:
                    doc.add_paragraph("Recommended Textbooks:")
                    for b in books:
                        doc.add_paragraph(f"  • {b}", style='List Bullet')

                doc.add_paragraph("")

        # Modifications
        mods = proposal_data.get('modifications', [])
        if mods:
            doc.add_heading('3. Proposed Modifications to Existing Subjects', level=2)
            for m in mods:
                doc.add_paragraph(f"Subject: {m.get('subject', 'N/A')}")
                doc.add_paragraph(f"Change: {m.get('details', 'N/A')}")
                doc.add_paragraph("")

        # Phase-outs
        phase_outs = proposal_data.get('phase_out', [])
        if phase_outs:
            doc.add_heading('4. Subjects Recommended for Phase-Out', level=2)
            for p in phase_outs:
                doc.add_paragraph(f"Subject: {p.get('subject', 'N/A')}")
                doc.add_paragraph(f"Reason: {p.get('reason', 'N/A')}")
                doc.add_paragraph(f"Replacement: {p.get('replacement', 'N/A')}")
                doc.add_paragraph("")

        # Impact
        impact = proposal.impact_projection or {}
        doc.add_heading('5. Expected Impact', level=2)
        doc.add_paragraph(f"Current coverage: {impact.get('current_coverage', 'N/A')}%")
        doc.add_paragraph(f"Projected coverage: {impact.get('projected_coverage', 'N/A')}%")
        doc.add_paragraph(f"Improvement: +{impact.get('improvement_pct', 'N/A')}%")

        # Save to bytes
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    # ─── V2: Submit for HOD Review ───────────────────────────────────

    async def submit_proposal_for_review(
        self, proposal_id: uuid.UUID, faculty_id: uuid.UUID, db: AsyncSession
    ) -> None:
        result = await db.execute(
            select(CurriculumProposal).where(
                CurriculumProposal.id == proposal_id,
                CurriculumProposal.created_by == faculty_id,
            )
        )
        proposal = result.scalar_one_or_none()
        if not proposal:
            raise ValueError("Proposal not found or you don't own it")
        proposal.status = "submitted"
        await db.commit()

    # ─── V2: Coverage Heatmap Data ───────────────────────────────────

    async def get_coverage_heatmap(self, department_code: str, db: AsyncSession) -> dict:
        """Generate heatmap data: subjects × top industry skills."""
        dept_res = await db.execute(
            select(Department).where(func.upper(Department.code) == department_code.upper())
        )
        department = dept_res.scalar_one_or_none()
        if not department:
            return {"subjects": [], "skills": [], "matrix": []}

        # Load subjects with skills
        subj_res = await db.execute(
            select(Subject)
            .where(Subject.department_id == department.id)
            .options(selectinload(Subject.curriculum_skills).selectinload(CurriculumSkill.skill))
            .order_by(Subject.semester_number, Subject.code)
        )
        subjects = subj_res.scalars().all()

        # Get top industry skills
        job_res = await db.execute(
            select(JobSkill.skill_id, func.count(JobSkill.id).label("cnt"))
            .group_by(JobSkill.skill_id)
            .order_by(func.count(JobSkill.id).desc())
            .limit(20)
        )
        top_skill_ids = [row[0] for row in job_res.all()]

        if not top_skill_ids:
            return {"subjects": [], "skills": [], "matrix": []}

        # Load skill names
        skill_res = await db.execute(select(Skill).where(Skill.id.in_(top_skill_ids)))
        skills_map = {s.id: s.name for s in skill_res.scalars().all()}
        skill_names = [skills_map.get(sid, "Unknown") for sid in top_skill_ids if sid in skills_map]

        # Build matrix
        matrix = []
        subject_names = []
        for sub in subjects:
            sub_skill_ids = {cs.skill_id for cs in (sub.curriculum_skills or []) if cs.skill}
            row = []
            for sid in top_skill_ids:
                if sid in skills_map:
                    row.append(1 if sid in sub_skill_ids else 0)
            matrix.append(row)
            subject_names.append(f"{sub.code} - {sub.name}")

        return {
            "subjects": subject_names,
            "skills": skill_names,
            "matrix": matrix,
        }

    # ─── Helpers ─────────────────────────────────────────────────────

    def _fallback_full_proposal(self, dept_code: str, gap_data: dict) -> dict:
        gap_skills = [g["skill"] for g in gap_data.get("gap_skills", [])[:5]]
        return {
            "proposed_subjects": [
                {
                    "name": f"Industry Skills Lab ({dept_code})",
                    "code_suggestion": f"{dept_code}-EL01",
                    "credits": 4,
                    "semester": 7,
                    "topics": gap_skills if gap_skills else ["Modern industry frameworks", "Cloud platforms", "CI/CD pipelines"],
                    "learning_outcomes": [
                        "CO1: Apply industry-standard tools in project development",
                        "CO2: Demonstrate proficiency in in-demand technical skills",
                        "CO3: Build and deploy production-ready applications",
                    ],
                    "textbooks": ["Relevant textbook TBD"],
                    "mapped_skills": gap_skills[:5],
                    "demand_score": 75,
                }
            ],
            "modifications": [
                {
                    "subject": "Software Engineering",
                    "change_type": "add_topics",
                    "details": "Add CI/CD, containerization, and agile practices",
                    "new_topics": ["Docker", "GitHub Actions", "Scrum methodology"],
                }
            ],
            "phase_out": [],
            "impact_summary": f"Adding these subjects would improve placement skill coverage. (Gemini unavailable for precise estimate.)",
        }

    def fallback_template(self, subject_name: str, uncovered_skills: list[str]) -> dict:
        return {
            "subject_name": subject_name,
            "revision_rationale": f"Internal reviews recommend adding {', '.join(uncovered_skills)} which are not adequately covered in the current syllabus.",
            "industry_alignment_score": "Data Unavailable",
            "proposed_modules": [
                {
                    "module_title": f"Modern {subject_name} Practices",
                    "hours": 6,
                    "topics": uncovered_skills if uncovered_skills else ["Foundational industry frameworks", "Modern toolchains"],
                    "justification": "Required across modern product organizations."
                }
            ],
            "recommended_lab_experiments": [
                f"Implement a basic project utilizing modern tools related to {subject_name}."
            ],
            "obsolete_topics_to_remove": [
                {"topic": "Legacy theoretical models", "reason": "Replaced by modern industry practices."}
            ],
            "references": [
                "Internal curriculum review guidelines"
            ]
        }


curriculum_proposal_service = CurriculumProposalService()

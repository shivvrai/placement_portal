import json
import logging
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.academic import Subject
from app.models.skill import CurriculumSkill
from app.services.gemini_client import generate_curriculum_proposal, is_gemini_configured

logger = logging.getLogger(__name__)

class CurriculumProposalService:
    
    SYSTEM_PROMPT = """
    You are an expert academic curriculum consultant specializing in engineering education 
    in India. You help Boards of Studies (BoS) modernize their subject syllabi to align 
    with industry hiring requirements. You produce structured, formal proposals in JSON format.
    """
    
    def build_prompt(
        self,
        subject_name: str,
        current_credits: int,
        current_topics: list[str],        # Existing syllabus topics
        uncovered_skills: list[str],       # Skills in job postings not in current syllabus
        top_companies_hiring: list[str],   # e.g., Amazon, Google, Infosys
        placement_demand_pct: float,       # % of drives requiring any of uncovered_skills
    ) -> str:
        """
        Builds a detailed prompt for Gemini to generate the modernization proposal.
        """
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
    
    async def generate(self, subject_id: uuid.UUID, db: AsyncSession) -> dict:
        """
        1. Fetch the Subject from DB by subject_id.
        2. Fetch SubjectSkill mappings.
        3. Determine uncovered skills.
        4. Build prompt.
        5. Call Gemini.
        6. Parse JSON.
        7. Fallback correctly on failure.
        """
        sub_res = await db.execute(
            select(Subject)
            .where(Subject.id == subject_id)
            .options(selectinload(Subject.curriculum_skills).selectinload(CurriculumSkill.skill))
        )
        subject = sub_res.scalar_one_or_none()
        if not subject:
            raise ValueError(f"Subject with id {subject_id} not found.")

        # Gather currently mapped skills
        current_skills = [cs.skill.name for cs in subject.curriculum_skills if cs.skill]
        current_skill_lower = {s.lower() for s in current_skills}

        # To avoid circular imports from curriculum.py, we mirror the domain logic here
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
            uncovered_skills = [f for f in ["Production-ready testing", "Git version control"] if f.lower() not in current_skill_lower]

        # However, the existing repository does not currently have an active analytics engine returning
        # live placement demand percentage or top companies. We must not fabricate them.
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
                
                # Clean up any potential markdown wrapper
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

    
    def fallback_template(
        self,
        subject_name: str,
        uncovered_skills: list[str],
    ) -> dict:
        """
        Generates a reasonable static proposal when Gemini is unavailable.
        Uses predefined module templates based on skill category.
        This ensures the feature works in development without a Gemini API key.
        """
        return {
          "subject_name": subject_name,
          "revision_rationale": f"Internal reviews recommend adding {', '.join(uncovered_skills)} which are not adequately covered in the current syllabus. Without active analytics, further justification is unavailable.",
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
            { "topic": "Legacy theoretical models", "reason": "Replaced by modern industry practices." }
          ],
          "references": [
            "Internal curriculum review guidelines"
          ]
        }

curriculum_proposal_service = CurriculumProposalService()

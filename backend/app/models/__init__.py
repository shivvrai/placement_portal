"""
Central model registry. Imports all models so Alembic and SQLAlchemy can discover them.
"""

from app.models.user import User, Department, Student, Faculty
from app.models.academic import Semester, Subject, AcademicRecord, Attendance
from app.models.skill import Skill, SkillRelationship, StudentSkill, CurriculumSkill
from app.models.industry import Company, Job, JobSkill, IndustrySkillTrend
from app.models.portfolio import Project, Certification, Internship, CareerGoal, Resume
from app.models.placement import PlacementDrive, Application, InterviewStage, PlacementOutcome
from app.models.roadmap import Resource, ResourceSkill, Roadmap, RoadmapTask
from app.models.system import CopilotConversation, AuditLog
from app.models.assessment import AssessmentQuestionBank, AssessmentSession, AssessmentSessionQuestion
from app.models.cohort import StudentCohort, Notification

__all__ = [
    # Identity & Auth (4)
    "User", "Department", "Student", "Faculty",
    # Academic (4)
    "Semester", "Subject", "AcademicRecord", "Attendance",
    # Skills (4)
    "Skill", "SkillRelationship", "StudentSkill", "CurriculumSkill",
    # Industry & Jobs (4)
    "Company", "Job", "JobSkill", "IndustrySkillTrend",
    # Student Portfolio (5)
    "Project", "Certification", "Internship", "CareerGoal", "Resume",
    # Placement (4)
    "PlacementDrive", "Application", "InterviewStage", "PlacementOutcome",
    # Learning & Roadmap (4)
    "Resource", "ResourceSkill", "Roadmap", "RoadmapTask",
    # Intelligence & System (2)
    "CopilotConversation", "AuditLog",
    "AssessmentQuestionBank", "AssessmentSession", "AssessmentSessionQuestion",
    "StudentCohort", "Notification",
]
# Total: 36 tables


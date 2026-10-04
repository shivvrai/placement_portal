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
from app.models.experiences import InterviewExperience
from app.models.announcements import DriveAnnouncement
from app.models.interview_session import MockInterviewSession
from app.models.curriculum_proposal import CurriculumProposal
from app.models.alumni import AlumniProfile, MentorshipConnection, MentorshipSession
from app.models.prep_resources import PrepResource, PrepCollection, PrepProgress
from app.models.feedback import FeedbackSurvey, SurveyQuestion, SurveyResponse
from app.models.company_reviews import CompanyReview, CompanyInsight
from app.models.document_vault import StudentDocument
from app.models.application_timeline import ApplicationTimelineEvent

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
    # Placement (5)
    "PlacementDrive", "Application", "InterviewStage", "PlacementOutcome", "DriveAnnouncement",
    # Learning & Roadmap (4)
    "Resource", "ResourceSkill", "Roadmap", "RoadmapTask",
    # Intelligence & System (2)
    "CopilotConversation", "AuditLog",
    "AssessmentQuestionBank", "AssessmentSession", "AssessmentSessionQuestion",
    "StudentCohort", "Notification",
    "InterviewExperience",
    # Sprint 3 — AI Learning Infrastructure
    "MockInterviewSession",
    "CurriculumProposal",
    # Sprint 3 — Sakshi: Alumni & Mentorship, Prep Resources, Feedback
    "AlumniProfile", "MentorshipConnection", "MentorshipSession",
    "PrepResource", "PrepCollection", "PrepProgress",
    "FeedbackSurvey", "SurveyQuestion", "SurveyResponse",
    # Sprint 3 — Anjula: Company Reviews, Document Vault, Application Timeline
    "CompanyReview", "CompanyInsight",
    "StudentDocument",
    "ApplicationTimelineEvent",
]
# Total: 53 tables


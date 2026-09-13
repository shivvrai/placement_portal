"""Pydantic schemas — Analytics domain (TPO & Faculty)."""

import uuid
from typing import Optional
from pydantic import BaseModel


class PlacementStatsResponse(BaseModel):
    academic_year: str
    total_students: int
    registered: int
    placed: int
    placement_pct: float
    avg_package: Optional[float] = None
    median_package: Optional[float] = None
    highest_package: Optional[float] = None
    companies_visited: int
    offers_released: int


class DeptPlacementRow(BaseModel):
    department_code: str
    department_name: str
    total: int
    placed: int
    placement_pct: float
    avg_package: Optional[float] = None


class MonthlyTrendRow(BaseModel):
    month: str
    placed: int
    offers: int


class RecruiterRow(BaseModel):
    company_name: str
    company: Optional[str] = None
    sector: Optional[str] = None
    offers: int
    avg_ctc: Optional[float] = None


class PackageBandRow(BaseModel):
    band_label: str   # e.g. "4-7L"
    count: int


class SkillDemandRow(BaseModel):
    skill_name: str
    demand_pct: float
    supply_pct: float
    gap: float


class CurriculumGapRow(BaseModel):
    subject_code: str
    subject_name: str
    semester_number: int
    coverage_pct: float
    demand_score: float
    gap_score: float
    top_missing_skills: list[str] = []


class YoYPlacementRow(BaseModel):
    year: str
    placed: int
    rate: float
    avg_pkg: Optional[float] = None


class SectorPieRow(BaseModel):
    name: str
    value: int
    color: Optional[str] = None


class DeptKpis(BaseModel):
    avg_skill_score: float
    curriculum_coverage: float
    subjects_high_gap: int
    students_at_risk: int


class SkillRadarItem(BaseModel):
    skill: str
    score: float
    benchmark: float


class CoverageDonutItem(BaseModel):
    name: str
    value: float
    color: str


class SubjectGapRankItem(BaseModel):
    subject: str
    gap: float
    dept: str
    sem: int


class BatchSkillItem(BaseModel):
    batch: str
    score: float


class AtRiskStudentItem(BaseModel):
    roll: str
    name: str
    cgpa: float
    skill: float
    risk: str  # 'high' | 'medium'
    id: Optional[uuid.UUID] = None


class DepartmentOverviewResponse(BaseModel):
    department_code: str
    department_name: str
    kpis: DeptKpis
    skill_radar: list[SkillRadarItem] = []
    coverage_donut: list[CoverageDonutItem] = []
    subject_gap_rank: list[SubjectGapRankItem] = []
    batch_skill: list[BatchSkillItem] = []
    at_risk: list[AtRiskStudentItem] = []
    total_at_risk_count: int = 0


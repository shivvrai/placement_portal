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


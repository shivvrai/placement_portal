"""
Feature Engineering — build numeric feature vectors for ML models.

StudentFeatureVector:
  - CGPA (normalised 0-1)
  - Semester (normalised)
  - Per-skill confidence scores (binary + continuous)
  - Resume parsed flag
  - Number of skills, certifications, projects

JobFeatureVector:
  - Min CGPA requirement
  - Skill importance weights
  - Job type encoding
  - Department eligibility flags

Pair features for matching:
  - Skill overlap ratio (weighted)
  - Semantic skill similarity (embedding-based)
  - CGPA margin
  - Department eligibility flag
"""

from __future__ import annotations

import numpy as np
from typing import Optional


# ---------------------------------------------------------------------------
# Skill taxonomy used for fixed-size feature vectors
# (Must be consistent across training and inference)
# ---------------------------------------------------------------------------
CANONICAL_SKILLS: list[str] = [
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "sql", "r", "scala", "kotlin", "php", "swift",
    # Web
    "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
    "spring", "html", "css", "graphql", "rest api",
    # Data / ML
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "statistics", "data analysis", "data engineering",
    "xgboost", "spark", "kafka", "airflow",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "sqlite", "bigquery", "cassandra",
    # Cloud / DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
    "ci/cd", "linux", "nginx", "git",
    # CS Fundamentals
    "data structures", "algorithms", "system design", "os",
    "computer networks", "oop", "design patterns",
    # Tools
    "tableau", "power bi", "excel", "figma", "postman",
]

SKILL_INDEX: dict[str, int] = {s: i for i, s in enumerate(CANONICAL_SKILLS)}
N_SKILLS = len(CANONICAL_SKILLS)

DEPT_CODES = ["CS", "IT", "ECE", "ME", "CE", "MBA"]
DEPT_INDEX = {d: i for i, d in enumerate(DEPT_CODES)}
N_DEPTS = len(DEPT_CODES)


def student_skill_vector(
    student_skills: dict[str, float],  # {normalised_skill_name: confidence 0-1}
) -> np.ndarray:
    """
    Build a fixed-length skill confidence vector for a student.
    Shape: (N_SKILLS,)  — confidence scores 0-1 for each canonical skill.
    """
    vec = np.zeros(N_SKILLS, dtype=np.float32)
    for skill, confidence in student_skills.items():
        idx = SKILL_INDEX.get(skill.lower())
        if idx is not None:
            vec[idx] = float(confidence)
    return vec


def job_skill_vector(
    job_skills: dict[str, str],  # {normalised_skill_name: importance}
) -> np.ndarray:
    """
    Build a fixed-length skill weight vector for a job.
    Shape: (N_SKILLS,)  — importance weights (1.5=required, 1.0=preferred, 0.5=nice_to_have)
    """
    weight_map = {"required": 1.5, "preferred": 1.0, "nice_to_have": 0.5}
    vec = np.zeros(N_SKILLS, dtype=np.float32)
    for skill, importance in job_skills.items():
        idx = SKILL_INDEX.get(skill.lower())
        if idx is not None:
            vec[idx] = weight_map.get(importance, 1.0)
    return vec


def build_student_features(
    cgpa: Optional[float],
    semester: int,
    student_skills: dict[str, float],
    department_code: Optional[str],
    n_projects: int = 0,
    n_certs: int = 0,
    resume_parsed: bool = False,
) -> np.ndarray:
    """
    Build the full student feature vector.
    Shape: (N_SKILLS + N_DEPTS + 6,)
    """
    skill_vec = student_skill_vector(student_skills)

    # Scalar features
    cgpa_norm = float(cgpa) / 10.0 if cgpa else 0.5
    sem_norm = (semester - 1) / 9.0
    proj_norm = min(n_projects / 5.0, 1.0)
    cert_norm = min(n_certs / 5.0, 1.0)
    resume_flag = 1.0 if resume_parsed else 0.0
    n_skills_norm = min(len(student_skills) / 20.0, 1.0)

    scalars = np.array(
        [cgpa_norm, sem_norm, proj_norm, cert_norm, resume_flag, n_skills_norm],
        dtype=np.float32,
    )

    # Department one-hot
    dept_vec = np.zeros(N_DEPTS, dtype=np.float32)
    if department_code and department_code in DEPT_INDEX:
        dept_vec[DEPT_INDEX[department_code]] = 1.0

    return np.concatenate([skill_vec, dept_vec, scalars])


def build_job_features(
    min_cgpa: Optional[float],
    min_experience: int = 0,
    job_skills: dict[str, str] = None,
    eligible_depts: list[str] = None,
) -> np.ndarray:
    """
    Build the full job feature vector.
    Shape: (N_SKILLS + N_DEPTS + 2,)
    """
    skill_vec = job_skill_vector(job_skills or {})
    cgpa_req = float(min_cgpa) / 10.0 if min_cgpa else 0.0
    exp_norm = min(min_experience / 5.0, 1.0)

    dept_vec = np.zeros(N_DEPTS, dtype=np.float32)
    for dept in (eligible_depts or []):
        if dept in DEPT_INDEX:
            dept_vec[DEPT_INDEX[dept]] = 1.0

    scalars = np.array([cgpa_req, exp_norm], dtype=np.float32)
    return np.concatenate([skill_vec, dept_vec, scalars])


def build_pair_features(
    student_skills: dict[str, float],
    job_skills: dict[str, str],
    student_cgpa: Optional[float],
    job_min_cgpa: Optional[float],
    student_dept: Optional[str],
    eligible_depts: Optional[list[str]],
) -> np.ndarray:
    """
    Build pairwise interaction features for one student-job pair.
    These are used as input to the match-score model.

    Shape: (N_SKILLS * 2 + 8,)
    """
    weight_map = {"required": 1.5, "preferred": 1.0, "nice_to_have": 0.5}

    stu_vec = student_skill_vector(student_skills)
    job_vec = job_skill_vector(job_skills)

    # Element-wise product = matched skill signal
    match_vec = stu_vec * (job_vec > 0).astype(np.float32)

    # Gap vector = job requirement - student level (clipped to 0)
    gap_vec = np.clip(job_vec / 1.5 - stu_vec, 0, 1)

    # Scalars
    cgpa_margin = (float(student_cgpa or 0) - float(job_min_cgpa or 0)) / 10.0
    dept_match = 1.0 if (
        not eligible_depts or not student_dept or student_dept in eligible_depts
    ) else 0.0
    required_skills = {s for s, imp in job_skills.items() if imp == "required"}
    req_matched = sum(1 for s in required_skills if student_skills.get(s, 0) >= 0.5)
    req_ratio = req_matched / max(len(required_skills), 1)
    total_job_skills = len(job_skills)
    total_matched = sum(1 for s in job_skills if student_skills.get(s, 0) >= 0.5)
    overall_match_ratio = total_matched / max(total_job_skills, 1)
    avg_confidence = np.mean(list(student_skills.values())) if student_skills else 0.0
    n_student_skills = min(len(student_skills) / 20.0, 1.0)

    scalars = np.array([
        cgpa_margin, dept_match, req_ratio, overall_match_ratio,
        avg_confidence, n_student_skills,
        float(len(required_skills)) / max(total_job_skills, 1),
        float(total_job_skills) / 20.0,
    ], dtype=np.float32)

    return np.concatenate([match_vec, gap_vec, scalars])


PAIR_FEATURE_DIM = N_SKILLS * 2 + 8
STUDENT_FEATURE_DIM = N_SKILLS + N_DEPTS + 6
JOB_FEATURE_DIM = N_SKILLS + N_DEPTS + 2


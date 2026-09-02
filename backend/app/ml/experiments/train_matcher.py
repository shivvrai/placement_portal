"""
Training Script — train the job-student matching model.

Usage:
    cd backend
    python -m app.ml.experiments.train_matcher

Generates: app/ml/matcher_model.pkl

The script:
  1. Generates synthetic training data (student-job pairs with known match quality)
  2. Builds pair feature vectors via features.py
  3. Trains a GradientBoostingRegressor
  4. Evaluates on held-out test set
  5. Saves model to app/ml/matcher_model.pkl
"""

from __future__ import annotations

import sys
import os
import pickle
import random
import logging
import numpy as np

# Make sure parent packages are importable
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from app.ml.features import (
    build_pair_features, CANONICAL_SKILLS
)
from app.ml.gap_engine import ROLE_PROFILES

# Alias expected by generate_training_data
ROLE_PROFILES_FOR_TRAINING = ROLE_PROFILES


logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "matcher_model.pkl")


# ---------------------------------------------------------------------------
# Synthetic data generation
# ---------------------------------------------------------------------------

SKILL_POOL = CANONICAL_SKILLS
JOB_TEMPLATES = [
    {
        "job_skills": {"python": "required", "machine learning": "required", "sql": "preferred", "docker": "nice_to_have"},
        "min_cgpa": 7.0, "eligible_departments": ["CS", "IT"],
        "true_quality": 0.9,  # high-demand, high-match baseline
    },
    {
        "job_skills": {"javascript": "required", "react": "required", "node.js": "preferred"},
        "min_cgpa": 6.5, "eligible_departments": ["CS", "IT"],
        "true_quality": 0.8,
    },
    {
        "job_skills": {"data structures": "required", "algorithms": "required", "system design": "preferred"},
        "min_cgpa": 7.5, "eligible_departments": [],
        "true_quality": 0.85,
    },
    {
        "job_skills": {"docker": "required", "kubernetes": "required", "linux": "required", "aws": "preferred"},
        "min_cgpa": 6.0, "eligible_departments": ["CS", "IT", "ECE"],
        "true_quality": 0.75,
    },
    {
        "job_skills": {"sql": "required", "python": "required", "tableau": "preferred", "statistics": "preferred"},
        "min_cgpa": 6.5, "eligible_departments": [],
        "true_quality": 0.80,
    },
    {
        "job_skills": {"spark": "required", "kafka": "required", "python": "required", "airflow": "preferred"},
        "min_cgpa": 7.0, "eligible_departments": ["CS", "IT"],
        "true_quality": 0.70,
    },
]

DEPT_POOL = ["CS", "IT", "ECE", "ME"]


def _random_student(rng: random.Random) -> dict:
    """Generate a random synthetic student."""
    n_skills = rng.randint(3, 15)
    skills = rng.sample(SKILL_POOL, min(n_skills, len(SKILL_POOL)))
    return {
        "skills": {s: round(rng.uniform(0.3, 1.0), 2) for s in skills},
        "cgpa": round(rng.uniform(5.5, 10.0), 1),
        "dept": rng.choice(DEPT_POOL),
    }


def _label_match(student: dict, job_template: dict) -> float:
    """
    Compute a synthetic ground-truth match score (0-100) for a student-job pair.
    This approximates what a recruiter would rate.
    """
    weight_map = {"required": 2.0, "preferred": 1.0, "nice_to_have": 0.5}
    total_w = sum(weight_map[imp] for imp in job_template["job_skills"].values())
    weighted_match = sum(
        weight_map[imp] * student["skills"].get(skill, 0.0)
        for skill, imp in job_template["job_skills"].items()
    )
    skill_score = (weighted_match / total_w) if total_w > 0 else 0.5

    cgpa_ok = student["cgpa"] >= job_template["min_cgpa"]
    dept_ok = (
        not job_template["eligible_departments"]
        or student["dept"] in job_template["eligible_departments"]
    )

    base = skill_score * 70 + (10 if cgpa_ok else 0) + (10 if dept_ok else 0)
    # Add noise to simulate recruiter subjectivity
    noise = random.gauss(0, 3)
    return round(max(0.0, min(100.0, base + noise + job_template["true_quality"] * 10)), 1)


def generate_training_data(n_samples: int = 4000) -> tuple[np.ndarray, np.ndarray]:
    rng = random.Random(42)
    X_list, y_list = [], []

    for _ in range(n_samples):
        student = _random_student(rng)
        job = rng.choice(JOB_TEMPLATES)
        label = _label_match(student, job)

        features = build_pair_features(
            student_skills=student["skills"],
            job_skills=job["job_skills"],
            student_cgpa=student["cgpa"],
            job_min_cgpa=job["min_cgpa"],
            student_dept=student["dept"],
            eligible_depts=job["eligible_departments"] or None,
        )
        X_list.append(features)
        y_list.append(label)

    return np.stack(X_list), np.array(y_list, dtype=np.float32)


def train():
    logger.info("Generating %d synthetic training samples...", 4000)
    X, y = generate_training_data(4000)
    logger.info("Feature shape: %s, Label range: %.1f - %.1f", X.shape, y.min(), y.max())

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Model pipeline
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("gbr", GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.08,
            max_depth=4,
            subsample=0.8,
            min_samples_leaf=5,
            random_state=42,
            verbose=0,
        )),
    ])

    logger.info("Training GradientBoostingRegressor...")
    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    logger.info("Test MAE: %.2f  |  R²: %.4f", mae, r2)

    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    logger.info("5-fold CV R²: %.4f ± %.4f", cv_scores.mean(), cv_scores.std())

    # Feature importances (from inner GBR)
    gbr = model.named_steps["gbr"]
    importances = gbr.feature_importances_
    top_idx = np.argsort(importances)[::-1][:10]
    logger.info("Top 10 feature importances:")
    for i in top_idx:
        logger.info("  feature[%d] = %.4f", i, importances[i])

    # Save model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    logger.info("Model saved to %s", MODEL_PATH)

    return mae, r2


if __name__ == "__main__":
    mae, r2 = train()
    print(f"\nTraining complete. MAE={mae:.2f}, R²={r2:.4f}")
    print(f"Model saved to: {MODEL_PATH}")

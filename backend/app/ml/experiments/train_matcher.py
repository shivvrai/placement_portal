"""
Training Script — train the job-student matching model with MLflow experiment tracking.

Usage:
    cd backend
    python -m app.ml.experiments.train_matcher

Generates: app/ml/matcher_model.pkl
MLflow UI: mlflow ui --port 5000 (from backend/ directory)

The script:
  1. Generates realistic synthetic training data with non-linear scoring
  2. Builds pair feature vectors via features.py
  3. Trains and compares multiple model architectures:
     - GradientBoostingRegressor (sklearn)
     - LightGBM Regressor (gradient boosted decision trees)
  4. Logs all experiments, parameters, metrics, and artifacts to MLflow
  5. Selects the best model by test R² and saves to app/ml/matcher_model.pkl
  6. Reports overfitting diagnostics and feature importance analysis

Label Generation Philosophy:
  - Labels simulate realistic recruiter evaluation with non-linear interactions
  - Adjacent skills receive partial credit via embedding cosine similarity
  - Experience and certification bonuses compound non-linearly with skills
  - CGPA has diminishing returns above the threshold (log-scaled)
  - Labels include calibrated heteroscedastic noise
"""

from __future__ import annotations

import sys
import os
import pickle
import random
import math
import logging
import json
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

# Make sure parent packages are importable
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from app.ml.features import (
    build_pair_features, CANONICAL_SKILLS, N_SKILLS
)
from app.ml.gap_engine import ROLE_PROFILES
from app.ml.embeddings import get_embedder

# Alias expected by generate_training_data
ROLE_PROFILES_FOR_TRAINING = ROLE_PROFILES


logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "matcher_model.pkl")
MLFLOW_EXPERIMENT = "CCIP-Matcher-Training"


# ---------------------------------------------------------------------------
# MLflow initialization (graceful fallback if not installed)
# ---------------------------------------------------------------------------

_mlflow_available = False
try:
    import mlflow
    import mlflow.sklearn
    _mlflow_available = True
except ImportError:
    logger.warning("mlflow not installed — running without experiment tracking. pip install mlflow")


def _init_mlflow():
    """Initialize MLflow experiment tracking."""
    if not _mlflow_available:
        return
    
    # Use SQLite backend (required by MLflow 3.x — file store is deprecated)
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "mlflow.db")
    db_path = os.path.abspath(db_path)
    mlflow.set_tracking_uri(f"sqlite:///{db_path}")
    mlflow.set_experiment(MLFLOW_EXPERIMENT)
    logger.info("MLflow tracking URI: %s", mlflow.get_tracking_uri())
    logger.info("MLflow experiment: %s", MLFLOW_EXPERIMENT)


# ---------------------------------------------------------------------------
# LightGBM import (graceful fallback)
# ---------------------------------------------------------------------------

_lgbm_available = False
try:
    import lightgbm as lgb
    _lgbm_available = True
except ImportError:
    logger.warning("lightgbm not installed — skipping LightGBM comparison. pip install lightgbm")


# ---------------------------------------------------------------------------
# Expanded job templates — diverse roles with realistic skill profiles
# ---------------------------------------------------------------------------

SKILL_POOL = CANONICAL_SKILLS

JOB_TEMPLATES = [
    # Software Engineering roles
    {
        "job_skills": {"python": "required", "data structures": "required", "algorithms": "required",
                       "system design": "preferred", "git": "preferred", "sql": "nice_to_have"},
        "min_cgpa": 7.0, "eligible_departments": ["CS", "IT"],
        "role_weight": {"academic": 0.25, "skill": 0.55, "experience": 0.20},
    },
    {
        "job_skills": {"java": "required", "spring": "required", "sql": "required",
                       "docker": "preferred", "system design": "preferred"},
        "min_cgpa": 7.0, "eligible_departments": ["CS", "IT"],
        "role_weight": {"academic": 0.20, "skill": 0.60, "experience": 0.20},
    },
    # Frontend / Full-Stack
    {
        "job_skills": {"javascript": "required", "react": "required", "node.js": "preferred",
                       "css": "nice_to_have", "html": "nice_to_have", "git": "preferred"},
        "min_cgpa": 6.5, "eligible_departments": ["CS", "IT"],
        "role_weight": {"academic": 0.15, "skill": 0.55, "experience": 0.30},
    },
    {
        "job_skills": {"javascript": "required", "typescript": "required", "react": "required",
                       "graphql": "preferred", "docker": "nice_to_have"},
        "min_cgpa": 7.0, "eligible_departments": ["CS", "IT"],
        "role_weight": {"academic": 0.20, "skill": 0.55, "experience": 0.25},
    },
    # Data Science / ML
    {
        "job_skills": {"python": "required", "machine learning": "required", "sql": "preferred",
                       "statistics": "required", "pandas": "preferred", "docker": "nice_to_have"},
        "min_cgpa": 7.5, "eligible_departments": ["CS", "IT"],
        "role_weight": {"academic": 0.30, "skill": 0.50, "experience": 0.20},
    },
    {
        "job_skills": {"python": "required", "deep learning": "required", "pytorch": "required",
                       "nlp": "preferred", "docker": "preferred"},
        "min_cgpa": 8.0, "eligible_departments": ["CS"],
        "role_weight": {"academic": 0.30, "skill": 0.50, "experience": 0.20},
    },
    # DevOps / Infrastructure
    {
        "job_skills": {"docker": "required", "kubernetes": "required", "linux": "required",
                       "aws": "preferred", "terraform": "preferred", "python": "nice_to_have"},
        "min_cgpa": 6.0, "eligible_departments": ["CS", "IT", "ECE"],
        "role_weight": {"academic": 0.10, "skill": 0.50, "experience": 0.40},
    },
    # Data Engineering
    {
        "job_skills": {"spark": "required", "kafka": "required", "python": "required",
                       "sql": "required", "airflow": "preferred", "aws": "preferred"},
        "min_cgpa": 7.0, "eligible_departments": ["CS", "IT"],
        "role_weight": {"academic": 0.20, "skill": 0.55, "experience": 0.25},
    },
    # Data Analyst
    {
        "job_skills": {"sql": "required", "python": "required", "tableau": "preferred",
                       "statistics": "preferred", "excel": "nice_to_have"},
        "min_cgpa": 6.5, "eligible_departments": [],
        "role_weight": {"academic": 0.25, "skill": 0.50, "experience": 0.25},
    },
    # Backend Developer
    {
        "job_skills": {"python": "required", "fastapi": "preferred", "postgresql": "required",
                       "redis": "preferred", "docker": "preferred", "rest api": "required"},
        "min_cgpa": 6.5, "eligible_departments": ["CS", "IT"],
        "role_weight": {"academic": 0.15, "skill": 0.55, "experience": 0.30},
    },
    # Cloud Architect
    {
        "job_skills": {"aws": "required", "gcp": "preferred", "docker": "required",
                       "kubernetes": "required", "terraform": "required", "python": "preferred"},
        "min_cgpa": 7.0, "eligible_departments": ["CS", "IT", "ECE"],
        "role_weight": {"academic": 0.10, "skill": 0.50, "experience": 0.40},
    },
    # Embedded / IoT
    {
        "job_skills": {"c++": "required", "linux": "required", "python": "preferred",
                       "git": "preferred"},
        "min_cgpa": 7.0, "eligible_departments": ["ECE", "CS", "ME"],
        "role_weight": {"academic": 0.30, "skill": 0.50, "experience": 0.20},
    },
]

DEPT_POOL = ["CS", "IT", "ECE", "ME"]


# ---------------------------------------------------------------------------
# Embedding-based adjacent skill credit
# ---------------------------------------------------------------------------

_embedder = None

def _get_adjacent_credit(student_skills: dict, required_skill: str) -> float:
    """
    If a student doesn't have the exact required skill but has a semantically
    similar one, grant partial credit based on cosine similarity.
    
    Returns a value in [0, 0.5] — partial credit, never full.
    """
    global _embedder
    if _embedder is None:
        _embedder = get_embedder()
    
    best_credit = 0.0
    for owned_skill, confidence in student_skills.items():
        if confidence < 0.3:
            continue
        sim = _embedder.cosine_similarity(owned_skill, required_skill)
        if sim >= 0.55 and sim < 0.95:  # Adjacent, not exact match
            credit = sim * confidence * 0.6
            if credit > best_credit:
                best_credit = credit
    
    return min(best_credit, 0.5)


# ---------------------------------------------------------------------------
# Non-linear, multi-factor label generation
# ---------------------------------------------------------------------------

def _random_student(rng: random.Random) -> dict:
    """Generate a random synthetic student with rich profile."""
    n_skills = rng.randint(3, 15)
    skills = rng.sample(SKILL_POOL, min(n_skills, len(SKILL_POOL)))
    
    skill_confidences = {}
    for s in skills:
        if rng.random() < 0.4:
            skill_confidences[s] = round(rng.uniform(0.3, 0.55), 2)
        else:
            skill_confidences[s] = round(rng.uniform(0.55, 1.0), 2)
    
    n_projects = rng.choices([0, 1, 2, 3, 4, 5], weights=[15, 25, 25, 20, 10, 5])[0]
    n_certs = rng.choices([0, 1, 2, 3, 4], weights=[30, 30, 25, 10, 5])[0]
    
    return {
        "skills": skill_confidences,
        "cgpa": round(rng.uniform(5.5, 10.0), 1),
        "dept": rng.choice(DEPT_POOL),
        "n_projects": n_projects,
        "n_certs": n_certs,
    }


def _label_match(student: dict, job_template: dict) -> float:
    """
    Compute a realistic non-linear match score (0-100) with:
    1. Weighted skill scoring with adjacent-skill partial credit (via embeddings)
    2. Non-linear CGPA scoring (diminishing returns above threshold)
    3. Department eligibility as a hard gate
    4. Experience bonuses that compound with skill score (interaction term)
    5. Calibrated heteroscedastic noise
    """
    importance_weight = {"required": 2.0, "preferred": 1.0, "nice_to_have": 0.5}
    
    total_weight = sum(importance_weight[imp] for imp in job_template["job_skills"].values())
    weighted_match = 0.0
    required_met = 0
    required_total = 0
    
    for skill, importance in job_template["job_skills"].items():
        w = importance_weight[importance]
        direct_conf = student["skills"].get(skill.lower(), 0.0)
        
        if direct_conf > 0.0:
            weighted_match += w * direct_conf
        else:
            try:
                adjacent_credit = _get_adjacent_credit(student["skills"], skill)
                weighted_match += w * adjacent_credit
            except Exception:
                pass
        
        if importance == "required":
            required_total += 1
            if direct_conf >= 0.5 or student["skills"].get(skill.lower(), 0.0) >= 0.5:
                required_met += 1
    
    skill_score = (weighted_match / total_weight) * 100 if total_weight > 0 else 50.0
    
    if required_total > 0:
        req_ratio = required_met / required_total
        if req_ratio < 0.5:
            skill_score *= (req_ratio ** 1.5)
    
    cgpa_score = 0.0
    min_cgpa = job_template["min_cgpa"]
    student_cgpa = student["cgpa"]
    
    if student_cgpa >= min_cgpa:
        margin = student_cgpa - min_cgpa
        cgpa_score = 70.0 + 30.0 * (1 - math.exp(-margin * 0.8))
    else:
        deficit = min_cgpa - student_cgpa
        cgpa_score = max(0.0, 70.0 * math.exp(-deficit * 1.2))
    
    dept_ok = True
    if job_template["eligible_departments"]:
        dept_ok = student["dept"] in job_template["eligible_departments"]
    
    if not dept_ok:
        return round(max(0.0, min(15.0, skill_score * 0.15)), 1)
    
    project_factor = 1.0 + min(student["n_projects"] / 5.0, 1.0) * 0.15
    cert_factor = 1.0 + min(student["n_certs"] / 4.0, 1.0) * 0.08
    
    role_w = job_template["role_weight"]
    raw_score = (
        role_w["academic"] * cgpa_score +
        role_w["skill"] * skill_score +
        role_w["experience"] * min(100.0, skill_score * project_factor * cert_factor)
    )
    
    noise_scale = 2.0 + 3.0 * math.exp(-((raw_score - 55) ** 2) / (2 * 20 ** 2))
    noise = random.gauss(0, noise_scale)
    
    return round(max(0.0, min(100.0, raw_score + noise)), 1)


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

def generate_training_data(n_samples: int = 6000) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic training pairs with embedding-based adjacent skill credit."""
    rng = random.Random(42)
    X_list, y_list = [], []

    for i in range(n_samples):
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
        
        if (i + 1) % 1000 == 0:
            logger.info("  Generated %d / %d samples...", i + 1, n_samples)

    return np.stack(X_list), np.array(y_list, dtype=np.float32)


# ---------------------------------------------------------------------------
# Feature name mapping for interpretability
# ---------------------------------------------------------------------------

def _feature_name(idx: int) -> str:
    """Map feature index to a human-readable name."""
    if idx < N_SKILLS:
        return f"match_signal[{CANONICAL_SKILLS[idx]}]"
    elif idx < 2 * N_SKILLS:
        return f"gap_signal[{CANONICAL_SKILLS[idx - N_SKILLS]}]"
    else:
        scalar_names = [
            "cgpa_margin", "dept_match", "req_ratio", "overall_match_ratio",
            "avg_confidence", "n_student_skills", "req_skill_fraction", "job_skill_density",
        ]
        scalar_idx = idx - 2 * N_SKILLS
        return scalar_names[scalar_idx] if scalar_idx < len(scalar_names) else f"scalar[{scalar_idx}]"


# ---------------------------------------------------------------------------
# Model evaluation helper
# ---------------------------------------------------------------------------

def _evaluate_model(model, X_train, y_train, X_test, y_test, X_all, y_all):
    """Compute comprehensive evaluation metrics."""
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    metrics = {
        "train_mae": mean_absolute_error(y_train, y_pred_train),
        "train_r2": r2_score(y_train, y_pred_train),
        "test_mae": mean_absolute_error(y_test, y_pred_test),
        "test_rmse": math.sqrt(mean_squared_error(y_test, y_pred_test)),
        "test_r2": r2_score(y_test, y_pred_test),
    }
    
    # Overfitting gap
    metrics["overfit_gap"] = metrics["train_r2"] - metrics["test_r2"]
    
    # Error distribution
    errors = y_test - y_pred_test
    metrics["mean_error"] = float(np.mean(errors))
    metrics["std_error"] = float(np.std(errors))
    metrics["pct_within_5"] = float(np.mean(np.abs(errors) < 5) * 100)
    metrics["pct_within_10"] = float(np.mean(np.abs(errors) < 10) * 100)
    
    # 5-fold cross-validation
    cv_r2 = cross_val_score(model, X_all, y_all, cv=5, scoring="r2")
    cv_mae = -cross_val_score(model, X_all, y_all, cv=5, scoring="neg_mean_absolute_error")
    metrics["cv_r2_mean"] = float(cv_r2.mean())
    metrics["cv_r2_std"] = float(cv_r2.std())
    metrics["cv_mae_mean"] = float(cv_mae.mean())
    metrics["cv_mae_std"] = float(cv_mae.std())
    
    return metrics


# ---------------------------------------------------------------------------
# Training pipeline
# ---------------------------------------------------------------------------

def train():
    logger.info("=" * 60)
    logger.info("CCIP Matcher Model Training Pipeline (with MLflow)")
    logger.info("=" * 60)
    
    # Initialize MLflow
    _init_mlflow()
    
    # Generate data
    n_samples = 6000
    logger.info("\nGenerating %d synthetic training samples...", n_samples)
    X, y = generate_training_data(n_samples)
    logger.info("Feature shape: %s, Label range: %.1f - %.1f, Mean: %.1f, Std: %.1f",
                X.shape, y.min(), y.max(), y.mean(), y.std())

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    logger.info("Train size: %d, Test size: %d\n", len(X_train), len(X_test))

    # -----------------------------------------------------------------------
    # Experiment 1: Scikit-Learn GradientBoostingRegressor
    # -----------------------------------------------------------------------
    
    gbr_params = {
        "n_estimators": 250,
        "learning_rate": 0.07,
        "max_depth": 5,
        "subsample": 0.8,
        "min_samples_leaf": 8,
        "max_features": "sqrt",
    }
    
    logger.info("=" * 40)
    logger.info("Experiment 1: sklearn GradientBoostingRegressor")
    logger.info("=" * 40)
    
    gbr_model = Pipeline([
        ("scaler", StandardScaler()),
        ("gbr", GradientBoostingRegressor(**gbr_params, random_state=42, verbose=0)),
    ])
    
    gbr_model.fit(X_train, y_train)
    gbr_metrics = _evaluate_model(gbr_model, X_train, y_train, X_test, y_test, X, y)
    
    # Log to MLflow
    if _mlflow_available:
        with mlflow.start_run(run_name="sklearn-GBR"):
            mlflow.log_params({f"gbr_{k}": v for k, v in gbr_params.items()})
            mlflow.log_param("model_type", "GradientBoostingRegressor")
            mlflow.log_param("scaler", "StandardScaler")
            mlflow.log_param("n_samples", n_samples)
            mlflow.log_param("n_features", X.shape[1])
            mlflow.log_param("test_size", 0.2)
            mlflow.log_metrics(gbr_metrics)
            mlflow.sklearn.log_model(
                gbr_model, "model",
                skops_trusted_types=["sklearn.tree._tree.Tree"],
            )
            
            # Log feature importances as artifact
            gbr_inner = gbr_model.named_steps["gbr"]
            importances = gbr_inner.feature_importances_
            top_features = {
                _feature_name(i): float(importances[i])
                for i in np.argsort(importances)[::-1][:15]
            }
            mlflow.log_dict(top_features, "feature_importances.json")
            mlflow.log_dict({
                "label_mean": float(y.mean()),
                "label_std": float(y.std()),
                "label_min": float(y.min()),
                "label_max": float(y.max()),
            }, "data_statistics.json")
    
    _log_results("sklearn-GBR", gbr_params, gbr_metrics)
    
    # Feature importance analysis
    gbr_inner = gbr_model.named_steps["gbr"]
    importances = gbr_inner.feature_importances_
    top_idx = np.argsort(importances)[::-1][:10]
    logger.info("\nTop 10 feature importances (sklearn-GBR):")
    for rank, i in enumerate(top_idx, 1):
        logger.info("  %2d. %-35s importance=%.4f", rank, _feature_name(i), importances[i])
    
    # -----------------------------------------------------------------------
    # Experiment 2: LightGBM Regressor
    # -----------------------------------------------------------------------
    
    best_model = gbr_model
    best_r2 = gbr_metrics["test_r2"]
    best_name = "sklearn-GBR"
    
    if _lgbm_available:
        lgbm_params = {
            "n_estimators": 300,
            "learning_rate": 0.06,
            "max_depth": 6,
            "num_leaves": 31,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_samples": 10,
            "reg_alpha": 0.1,
            "reg_lambda": 0.1,
        }
        
        logger.info("\n" + "=" * 40)
        logger.info("Experiment 2: LightGBM Regressor")
        logger.info("=" * 40)
        
        lgbm_model = Pipeline([
            ("scaler", StandardScaler()),
            ("lgbm", lgb.LGBMRegressor(**lgbm_params, random_state=42, verbose=-1)),
        ])
        
        lgbm_model.fit(X_train, y_train)
        lgbm_metrics = _evaluate_model(lgbm_model, X_train, y_train, X_test, y_test, X, y)
        
        # Log to MLflow
        if _mlflow_available:
            with mlflow.start_run(run_name="LightGBM"):
                mlflow.log_params({f"lgbm_{k}": v for k, v in lgbm_params.items()})
                mlflow.log_param("model_type", "LightGBM")
                mlflow.log_param("scaler", "StandardScaler")
                mlflow.log_param("n_samples", n_samples)
                mlflow.log_param("n_features", X.shape[1])
                mlflow.log_param("test_size", 0.2)
                mlflow.log_metrics(lgbm_metrics)
                mlflow.sklearn.log_model(
                    lgbm_model, "model",
                    skops_trusted_types=[
                        "sklearn.tree._tree.Tree",
                        "collections.OrderedDict",
                        "lightgbm.basic.Booster",
                        "lightgbm.sklearn.LGBMRegressor",
                    ],
                )
                
                lgbm_inner = lgbm_model.named_steps["lgbm"]
                lgbm_importances = lgbm_inner.feature_importances_
                top_lgbm_features = {
                    _feature_name(i): int(lgbm_importances[i])
                    for i in np.argsort(lgbm_importances)[::-1][:15]
                }
                mlflow.log_dict(top_lgbm_features, "feature_importances.json")
        
        _log_results("LightGBM", lgbm_params, lgbm_metrics)
        
        # Feature importance analysis
        lgbm_inner = lgbm_model.named_steps["lgbm"]
        lgbm_importances = lgbm_inner.feature_importances_
        top_lgbm_idx = np.argsort(lgbm_importances)[::-1][:10]
        logger.info("\nTop 10 feature importances (LightGBM):")
        for rank, i in enumerate(top_lgbm_idx, 1):
            logger.info("  %2d. %-35s importance=%d", rank, _feature_name(i), lgbm_importances[i])
        
        # Compare and select best
        if lgbm_metrics["test_r2"] > best_r2:
            best_model = lgbm_model
            best_r2 = lgbm_metrics["test_r2"]
            best_name = "LightGBM"
    
    # -----------------------------------------------------------------------
    # Model Selection & Saving
    # -----------------------------------------------------------------------
    
    logger.info("\n" + "=" * 40)
    logger.info("MODEL SELECTION")
    logger.info("=" * 40)
    logger.info("Best model: %s (Test R² = %.4f)", best_name, best_r2)
    
    # Save best model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(best_model, f)
    logger.info("✓ Model saved to %s", MODEL_PATH)
    
    # Log best model selection to MLflow
    if _mlflow_available:
        with mlflow.start_run(run_name=f"BEST-{best_name}"):
            mlflow.log_param("selected_model", best_name)
            mlflow.log_metric("best_test_r2", best_r2)
            mlflow.sklearn.log_model(
                best_model, "best_model",
                registered_model_name="ccip-matcher",
                skops_trusted_types=[
                    "sklearn.tree._tree.Tree",
                    "collections.OrderedDict",
                    "lightgbm.basic.Booster",
                    "lightgbm.sklearn.LGBMRegressor",
                ],
            )
    
    # Final error distribution
    y_pred_final = best_model.predict(X_test)
    errors = y_test - y_pred_final
    logger.info("\nError distribution on test set (%s):", best_name)
    logger.info("  Mean error:  %.2f (≈0 = unbiased)", errors.mean())
    logger.info("  Std error:   %.2f", errors.std())
    logger.info("  |error| < 5: %.1f%% of predictions", 100 * np.mean(np.abs(errors) < 5))
    logger.info("  |error| < 10: %.1f%% of predictions", 100 * np.mean(np.abs(errors) < 10))
    
    if _mlflow_available:
        logger.info("\n📊 View experiment results: mlflow ui --port 5000")
        logger.info("   (run from backend/ directory)")
    
    return mean_absolute_error(y_test, y_pred_final), r2_score(y_test, y_pred_final)


def _log_results(name: str, params: dict, metrics: dict):
    """Pretty-print model evaluation results."""
    logger.info("\n--- %s Results ---", name)
    logger.info("  Train:  MAE=%.2f  |  R²=%.4f", metrics["train_mae"], metrics["train_r2"])
    logger.info("  Test:   MAE=%.2f  |  RMSE=%.2f  |  R²=%.4f",
                metrics["test_mae"], metrics["test_rmse"], metrics["test_r2"])
    logger.info("  Overfit gap: %.4f %s",
                metrics["overfit_gap"],
                "✓ Healthy" if metrics["overfit_gap"] < 0.05 else "⚠ Watch")
    logger.info("  5-fold CV R²:  %.4f ± %.4f", metrics["cv_r2_mean"], metrics["cv_r2_std"])
    logger.info("  5-fold CV MAE: %.2f ± %.2f", metrics["cv_mae_mean"], metrics["cv_mae_std"])


if __name__ == "__main__":
    mae, r2 = train()
    print(f"\nTraining complete. Test MAE={mae:.2f}, Test R²={r2:.4f}")
    print(f"Model saved to: {MODEL_PATH}")

"""
Time Series Forecasting Module — trainable exponential smoothing models
for skill demand prediction and Holt's Double Exponential Smoothing (DES) Engine.

Analyzes 24-month historical placement requirement frequencies and projects
future skill demand velocity using Holt's Linear Trend method:
  Level: l_t = alpha * Y_t + (1 - alpha) * (l_{t-1} + b_{t-1})
  Trend: b_t = beta * (l_t - l_{t-1}) + (1 - beta) * b_{t-1}
  Forecast: Y_hat_{t+h} = l_t + h * b_t

Parameters:
  alpha = 0.3 (smoothing factor for level)
  beta = 0.1 (smoothing factor for trend)
  h = 3 (forecast horizon in quarters/months)

Classifications:
  - Surging: Projected growth rate > +15%
  - Stable: Projected growth rate within [-10%, +15%] (variance within +-10%)
  - Declining: Projected decrease < -15%
"""

from __future__ import annotations

import math
import pickle
import logging
import os
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

# MLflow import (graceful fallback)
_mlflow_available = False
try:
    import mlflow
    _mlflow_available = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Forecasting Models
# ---------------------------------------------------------------------------

@dataclass
class ForecastResult:
    """Container for forecast output with full diagnostic information."""
    level: float
    trend: float
    fitted_values: list[float]
    forecast_values: list[float]
    residuals: list[float]
    mse: float
    mae: float
    mape: Optional[float]  # None if series has zeros
    alpha: float
    beta: float
    method: str  # "SES" or "Holt"
    
    def to_dict(self) -> dict:
        return {
            "level": round(self.level, 3),
            "trend": round(self.trend, 3),
            "fitted_values": [round(v, 2) for v in self.fitted_values],
            "forecast_values": [round(v, 2) for v in self.forecast_values],
            "mse": round(self.mse, 4),
            "mae": round(self.mae, 4),
            "mape": round(self.mape, 2) if self.mape is not None else None,
            "alpha": round(self.alpha, 3),
            "beta": round(self.beta, 3),
            "method": self.method,
        }


@dataclass
class TrainedForecaster:
    """
    A trained exponential smoothing forecaster with optimized parameters.
    
    Can be serialized with pickle for production deployment.
    Stores the learned parameters (α, β) and the final state (level, trend)
    needed for making new forecasts without re-fitting.
    """
    alpha: float = 0.3
    beta: float = 0.1
    method: str = "Holt"  # "SES" or "Holt"
    level: float = 0.0
    trend: float = 0.0
    training_mse: float = 0.0
    training_mae: float = 0.0
    series_length: int = 0
    skill_name: str = ""
    
    def predict(self, horizon: int = 3) -> list[float]:
        """Generate h-step ahead forecasts from the trained model state."""
        if self.method == "SES":
            return [max(0.0, round(self.level, 2))] * horizon
        else:
            return [
                max(0.0, round(self.level + h * self.trend, 2))
                for h in range(1, horizon + 1)
            ]
    
    def update(self, new_observation: float) -> float:
        """
        Online update: incorporate a new observation and return updated forecast.
        This allows the model to learn from new data without full retraining.
        """
        prev_level = self.level
        
        if self.method == "SES":
            self.level = self.alpha * new_observation + (1 - self.alpha) * self.level
            return self.level
        else:
            self.level = self.alpha * new_observation + (1 - self.alpha) * (prev_level + self.trend)
            self.trend = self.beta * (self.level - prev_level) + (1 - self.beta) * self.trend
            return self.level + self.trend
    
    def save(self, path: str):
        """Serialize the trained model to disk."""
        with open(path, "wb") as f:
            pickle.dump(self, f)
        logger.info("Saved forecaster for '%s' to %s", self.skill_name, path)
    
    @staticmethod
    def load(path: str) -> "TrainedForecaster":
        """Load a trained model from disk."""
        with open(path, "rb") as f:
            return pickle.load(f)


# ---------------------------------------------------------------------------
# Core Smoothing Algorithms
# ---------------------------------------------------------------------------

def _ses(series: list[float], alpha: float) -> tuple[list[float], float]:
    """Run SES and return (fitted_values, final_level)."""
    if not series:
        return [], 0.0
    
    level = series[0]
    fitted = [level]
    
    for t in range(1, len(series)):
        level = alpha * series[t] + (1 - alpha) * level
        fitted.append(level)
    
    return fitted, level


def _holt(series: list[float], alpha: float, beta: float) -> tuple[list[float], float, float]:
    """Run Holt's DES and return (fitted_values, final_level, final_trend)."""
    if len(series) < 2:
        fitted, level = _ses(series, alpha)
        return fitted, level, 0.0
    
    level = series[0]
    trend = series[1] - series[0]
    fitted = [level]
    
    for t in range(1, len(series)):
        prev_level = level
        level = alpha * series[t] + (1 - alpha) * (prev_level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        fitted.append(level + trend)
    
    return fitted, level, trend


def _compute_error_metrics(
    actual: list[float],
    fitted: list[float],
) -> tuple[float, float, Optional[float]]:
    """Compute MSE, MAE, and MAPE (if no zeros in actual)."""
    n = min(len(actual), len(fitted))
    if n == 0:
        return 0.0, 0.0, None
    
    residuals = [actual[i] - fitted[i] for i in range(n)]
    mse = sum(r ** 2 for r in residuals) / n
    mae = sum(abs(r) for r in residuals) / n
    
    # MAPE (skip if any actual value is 0)
    mape = None
    if all(a > 0 for a in actual[:n]):
        mape = sum(abs(r) / a for r, a in zip(residuals, actual[:n])) / n * 100
    
    return mse, mae, mape


# ---------------------------------------------------------------------------
# Training via Grid Search
# ---------------------------------------------------------------------------

ALPHA_GRID = [0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
BETA_GRID = [0.01, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5]


def train_forecaster(
    series: list[float],
    skill_name: str = "",
    validation_window: int = 2,
    log_to_mlflow: bool = True,
) -> TrainedForecaster:
    """
    Train an exponential smoothing model by optimizing (α, β) via grid search.
    
    Process:
    1. If series length < 3: use SES with default α=0.3 (insufficient data for optimization)
    2. If series length >= 3: split into train/validation
    3. Grid search over (α, β) combinations, minimizing validation MSE
    4. Select best parameters and fit on full series
    5. Log experiment to MLflow (if available and enabled)
    
    Args:
        series: Time series of demand counts (oldest first)
        skill_name: Name of the skill (for logging)
        validation_window: Number of trailing points for validation
        log_to_mlflow: Whether to log the experiment to MLflow
    
    Returns:
        TrainedForecaster with optimized parameters
    """
    if len(series) < 2:
        # Not enough data — return default SES model
        level = series[0] if series else 0.0
        return TrainedForecaster(
            alpha=0.3, beta=0.0, method="SES",
            level=level, trend=0.0,
            training_mse=0.0, training_mae=0.0,
            series_length=len(series), skill_name=skill_name,
        )
    
    # Determine method: SES for very short, Holt's for longer
    use_holt = len(series) >= 4
    
    # Split into train/validation
    val_size = min(validation_window, max(1, len(series) // 4))
    train_series = series[:-val_size]
    val_series = series[-val_size:]
    
    if len(train_series) < 2:
        train_series = series
        val_series = series[-1:]
    
    best_mse = float("inf")
    best_alpha = 0.3
    best_beta = 0.1
    
    # Grid search
    search_results = []
    
    for alpha in ALPHA_GRID:
        if use_holt:
            for beta in BETA_GRID:
                fitted, level, trend = _holt(train_series, alpha, beta)
                # Predict validation period
                val_preds = [level + h * trend for h in range(1, val_size + 1)]
                mse = sum((a - p) ** 2 for a, p in zip(val_series, val_preds)) / val_size
                
                search_results.append({"alpha": alpha, "beta": beta, "val_mse": mse})
                
                if mse < best_mse:
                    best_mse = mse
                    best_alpha = alpha
                    best_beta = beta
        else:
            fitted, level = _ses(train_series, alpha)
            val_preds = [level] * val_size
            mse = sum((a - p) ** 2 for a, p in zip(val_series, val_preds)) / val_size
            
            search_results.append({"alpha": alpha, "beta": 0.0, "val_mse": mse})
            
            if mse < best_mse:
                best_mse = mse
                best_alpha = alpha
                best_beta = 0.0
    
    # Fit on full series with best parameters
    if use_holt:
        fitted, final_level, final_trend = _holt(series, best_alpha, best_beta)
        method = "Holt"
    else:
        fitted, final_level = _ses(series, best_alpha)
        final_trend = 0.0
        method = "SES"
    
    train_mse, train_mae, _ = _compute_error_metrics(series, fitted)
    
    forecaster = TrainedForecaster(
        alpha=best_alpha,
        beta=best_beta,
        method=method,
        level=final_level,
        trend=final_trend,
        training_mse=train_mse,
        training_mae=train_mae,
        series_length=len(series),
        skill_name=skill_name,
    )
    
    # Log to MLflow
    if log_to_mlflow and _mlflow_available:
        try:
            db_path = os.path.join(os.path.dirname(__file__), "..", "..", "mlflow.db")
            db_path = os.path.abspath(db_path)
            mlflow.set_tracking_uri(f"sqlite:///{db_path}")
            mlflow.set_experiment("CCIP-Demand-Forecasting")
            
            with mlflow.start_run(run_name=f"forecast-{skill_name or 'unknown'}"):
                mlflow.log_params({
                    "skill_name": skill_name,
                    "method": method,
                    "alpha": best_alpha,
                    "beta": best_beta,
                    "series_length": len(series),
                    "validation_window": val_size,
                    "grid_size": len(search_results),
                })
                mlflow.log_metrics({
                    "best_val_mse": best_mse,
                    "train_mse": train_mse,
                    "train_mae": train_mae,
                    "final_level": final_level,
                    "final_trend": final_trend,
                })
        except Exception as e:
            logger.debug("MLflow logging skipped for forecaster: %s", e)
    
    logger.info(
        "Trained %s forecaster for '%s': α=%.2f, β=%.2f, MSE=%.3f (searched %d combos)",
        method, skill_name, best_alpha, best_beta, train_mse, len(search_results),
    )
    
    return forecaster


def forecast(
    series: list[float],
    skill_name: str = "",
    horizon: int = 3,
) -> ForecastResult:
    """
    High-level API: train a forecaster and return detailed forecast results.
    
    This is the main entry point for the skill trend service.
    """
    forecaster = train_forecaster(series, skill_name=skill_name)
    predictions = forecaster.predict(horizon)
    
    # Recompute fitted values for diagnostics
    if forecaster.method == "Holt" and len(series) >= 2:
        fitted, _, _ = _holt(series, forecaster.alpha, forecaster.beta)
    else:
        fitted, _ = _ses(series, forecaster.alpha)
    
    residuals = [series[i] - fitted[i] for i in range(len(series))]
    mse, mae, mape = _compute_error_metrics(series, fitted)
    
    return ForecastResult(
        level=forecaster.level,
        trend=forecaster.trend,
        fitted_values=fitted,
        forecast_values=predictions,
        residuals=residuals,
        mse=mse,
        mae=mae,
        mape=mape,
        alpha=forecaster.alpha,
        beta=forecaster.beta,
        method=forecaster.method,
    )


def compute_growth_rate(series: list[float]) -> float:
    """
    Compute growth rate from a time series using compound growth formula.
    
    CAGR = (V_final / V_initial)^(1/n) - 1
    
    Returns growth rate as a decimal (e.g., 0.15 = 15% growth).
    """
    if len(series) < 2:
        return 0.0
    
    first_nonzero = None
    for i, v in enumerate(series):
        if v > 0:
            first_nonzero = i
            break
    
    if first_nonzero is None or first_nonzero >= len(series) - 1:
        return 0.0
    
    v_initial = max(series[first_nonzero], 1.0)
    v_final = max(series[-1], 0.0)
    n_periods = len(series) - first_nonzero - 1
    
    if n_periods <= 0 or v_initial <= 0:
        return 0.0
    
    try:
        cagr = (v_final / v_initial) ** (1.0 / n_periods) - 1.0
    except (ZeroDivisionError, ValueError, OverflowError):
        cagr = 0.0
    
    return max(-0.9, min(2.0, round(cagr, 4)))


# ---------------------------------------------------------------------------
# Holt's Double Exponential Smoothing (DES) Canonical Engine
# ---------------------------------------------------------------------------

# Default model parameters
DEFAULT_ALPHA = 0.3
DEFAULT_BETA = 0.1
FORECAST_HORIZON = 3  # h = 3 periods forward
CACHE_TTL_SECONDS = 6 * 3600  # 6-hour cache TTL

_forecast_cache: Optional[dict] = None
_forecast_cache_time: Optional[datetime] = None


def holt_double_exponential_smoothing(
    series: list[float] | np.ndarray,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    h: int = FORECAST_HORIZON,
) -> tuple[float, float, float]:
    """
    Apply Holt's Double Exponential Smoothing to a time-series.

    Returns:
        (forecast_value, growth_rate, current_level)
    """
    y = np.array(series, dtype=np.float64)
    n = len(y)
    if n == 0:
        return 0.0, 0.0, 0.0
    if n == 1:
        return float(y[0]), 0.0, float(y[0])

    # Initialise level and trend
    l_prev = y[0]
    b_prev = y[1] - y[0] if n > 1 else 0.0

    # Iterative smoothing across 24-month historical data
    for t in range(1, n):
        y_t = y[t]
        l_curr = alpha * y_t + (1.0 - alpha) * (l_prev + b_prev)
        b_curr = beta * (l_curr - l_prev) + (1.0 - beta) * b_prev
        l_prev, b_prev = l_curr, b_curr

    # Forecast h steps into future: Y_hat = l_t + h * b_t
    y_hat = max(0.0, l_prev + h * b_prev)
    growth_rate = (h * b_prev) / max(l_prev, 1.0)

    return round(float(y_hat), 2), round(float(growth_rate), 4), round(float(l_prev), 2)


holts_double_exponential_smoothing = holt_double_exponential_smoothing


def classify_trend(growth_rate: float) -> str:
    """
    Classify growth rate:
      - Surging: > +15% (+0.15)
      - Declining: < -15% (-0.15)
      - Stable: within [-10%, +15%] (stable variance)
    """
    if growth_rate > 0.15:
        return "surging"
    elif growth_rate < -0.15:
        return "declining"
    return "stable"


# Canonical 24-month placement frequency sequences for core campus technologies
# Demonstrates 24-month historical placement patterns (Month 1 -> Month 24)
HISTORICAL_24M_SERIES: dict[str, list[float]] = {
    # Surging technologies (> +15% projected velocity)
    "Generative AI": [0, 0, 1, 1, 2, 2, 3, 4, 6, 8, 11, 14, 18, 23, 29, 36, 44, 53, 63, 75, 88, 103, 120, 140],
    "LangChain":     [1, 1, 2, 2, 3, 3, 4, 5, 7, 9, 11, 14, 17, 21, 25, 30, 36, 43, 51, 60, 70, 81, 93, 107],
    "PyTorch":       [5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 22, 25, 29, 33, 38, 44, 51, 59, 68, 78, 89, 101, 115],
    "Kubernetes":    [10, 11, 12, 13, 15, 17, 19, 21, 24, 27, 31, 35, 40, 45, 51, 58, 66, 75, 85, 96, 108, 121, 135, 151],
    "FastAPI": [10, 11, 12, 13, 15, 16, 18, 19, 20, 22, 24, 25, 26, 28, 29, 31, 32, 33, 34, 35, 36, 37, 39, 41],
    "AWS": [25, 26, 27, 29, 30, 32, 33, 35, 37, 38, 40, 42, 43, 45, 47, 48, 50, 51, 52, 53, 54, 55, 57, 59],
    "Go": [8, 9, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 25, 26, 27, 28, 30],

    # Stable technologies (steady continuous demand within +-10%)
    "Python": [85, 86, 84, 87, 85, 86, 88, 87, 86, 89, 90, 88, 89, 91, 90, 92, 91, 90, 92, 91, 92, 93, 92, 94],
    "SQL": [80, 82, 81, 83, 82, 84, 85, 83, 84, 86, 85, 86, 87, 86, 88, 87, 86, 88, 87, 86, 87, 88, 87, 88],
    "React": [70, 71, 72, 70, 73, 72, 74, 75, 73, 74, 76, 75, 76, 75, 77, 76, 75, 76, 75, 76, 77, 76, 77, 78],
    "Java": [65, 66, 64, 65, 63, 64, 65, 64, 63, 65, 64, 63, 62, 63, 64, 63, 62, 63, 62, 63, 62, 62, 61, 62],
    "Docker": [55, 56, 58, 59, 60, 61, 62, 63, 64, 65, 65, 66, 67, 67, 68, 68, 69, 69, 70, 70, 71, 71, 72, 73],

    # Declining technologies (< -15% projected velocity)
    "jQuery": [28, 27, 25, 24, 22, 21, 20, 18, 17, 16, 15, 14, 13, 12, 11, 10, 10, 9, 8, 8, 8, 7, 6, 5],
    "PHP": [35, 34, 32, 31, 29, 28, 26, 25, 23, 22, 20, 19, 18, 17, 16, 15, 14, 13, 13, 12, 12, 11, 10, 9],
    "SOAP": [15, 14, 13, 12, 11, 10, 9, 8, 7, 7, 6, 5, 5, 4, 4, 3, 3, 2, 2, 2, 2, 1, 1, 1],
    "Perl": [12, 11, 10, 10, 9, 8, 7, 7, 6, 5, 5, 4, 4, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1],
}


def compute_holt_skill_trends(scale_multiplier: float = 1.0) -> dict:
    """
    Computes Holt's Double Exponential Smoothing forecast for all skills.
    Returns classified trends with growth rate and forecast values.
    """
    global _forecast_cache, _forecast_cache_time
    now = datetime.now(timezone.utc)

    if _forecast_cache and _forecast_cache_time:
        elapsed = (now - _forecast_cache_time).total_seconds()
        if elapsed < CACHE_TTL_SECONDS:
            return _forecast_cache

    surging = []
    stable = []
    declining = []

    for skill, raw_series in HISTORICAL_24M_SERIES.items():
        scaled_series = [max(1, int(v * scale_multiplier)) for v in raw_series]
        forecast_val, growth_rate, current_level = holt_double_exponential_smoothing(
            scaled_series, alpha=DEFAULT_ALPHA, beta=DEFAULT_BETA, h=FORECAST_HORIZON
        )
        classification = classify_trend(growth_rate)
        growth_pct = round(growth_rate * 100, 1)

        entry = {
            "skill": skill,
            "skill_name": skill,
            "demand_count": scaled_series[-1],
            "projected_demand": round(forecast_val),
            "growth_rate": growth_rate,
            "growth_pct": growth_pct,
            "classification": classification.capitalize(),
            "status": classification,
            "historical_24m_volume": sum(scaled_series),
            "drives_pct": min(100, max(5, int(scaled_series[-1] * 0.9))),
        }

        if classification == "surging":
            surging.append(entry)
        elif classification == "declining":
            declining.append(entry)
        else:
            stable.append(entry)

    surging.sort(key=lambda s: s["growth_rate"], reverse=True)
    stable.sort(key=lambda s: s["demand_count"], reverse=True)
    declining.sort(key=lambda s: s["growth_rate"])

    result = {
        "model": "Holt's Double Exponential Smoothing",
        "parameters": {"alpha": DEFAULT_ALPHA, "beta": DEFAULT_BETA, "horizon_months": FORECAST_HORIZON},
        "forecast_horizon_months": FORECAST_HORIZON,
        "surging": surging,
        "stable": stable,
        "declining": declining,
        "as_of": now.isoformat(),
        "computed_at": now.isoformat(),
        "cache_ttl_hours": 6,
    }

    _forecast_cache = result
    _forecast_cache_time = now
    return result


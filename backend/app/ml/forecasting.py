"""
Time Series Forecasting Module — trainable exponential smoothing models
for skill demand prediction.

This module provides trainable forecasting models that learn optimal
smoothing parameters from historical data via grid search optimization.

Mathematical Foundation:
  - Simple Exponential Smoothing (SES):
      L_t = α · y_t + (1 - α) · L_{t-1}
      Forecast: ŷ_{t+h} = L_t

  - Holt's Double Exponential Smoothing (DES):
      L_t = α · y_t + (1 - α) · (L_{t-1} + T_{t-1})
      T_t = β · (L_t - L_{t-1}) + (1 - β) · T_{t-1}
      Forecast: ŷ_{t+h} = L_t + h · T_t

Training Process:
  - Grid search over (α, β) parameter space
  - Minimizes MSE on held-out validation window
  - Model serialization via pickle for production deployment
  - Tracks training metrics via MLflow (if available)

Industry Alignment:
  HP's supply chain uses similar exponential smoothing models for
  inventory demand forecasting. The parameters learned here (α for
  level reactivity, β for trend sensitivity) directly parallel
  parameters tuned in supply chain forecasting systems.
"""

from __future__ import annotations

import math
import pickle
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

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

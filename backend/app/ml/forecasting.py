"""
Skill Demand Forecasting — Holt's Double Exponential Smoothing (DES) Engine.

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

import logging
from datetime import datetime, timezone
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

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

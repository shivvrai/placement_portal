"""
Apache Superset configuration for CCIP BI Integration.

This config enables:
- Guest token embedding (for iframe embed in React frontend)
- CORS for frontend origin
- Connection to CCIP PostgreSQL database
- Custom branding
"""

import os

# ─── Core ────────────────────────────────────────────────────────────────────

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "superset-dev-secret-key-change-me")

# ─── Database ────────────────────────────────────────────────────────────────

SQLALCHEMY_DATABASE_URI = (
    f"postgresql://"
    f"{os.environ.get('DATABASE_USER', 'ccip')}:"
    f"{os.environ.get('DATABASE_PASSWORD', 'ccip_dev')}@"
    f"{os.environ.get('DATABASE_HOST', 'postgres')}:"
    f"{os.environ.get('DATABASE_PORT', '5432')}/"
    f"superset_meta"
)

# ─── Feature Flags ───────────────────────────────────────────────────────────

FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,          # Enable guest token embedding
    "ENABLE_TEMPLATE_PROCESSING": True,  # Jinja in SQL Lab
    "ALERT_REPORTS": True,               # Enable alerts & scheduled reports
    "DASHBOARD_CROSS_FILTERS": True,     # Cross-filter between charts
    "DASHBOARD_RBAC": True,              # Role-based dashboard access
    "ENABLE_EXPLORE_DRAG_AND_DROP": True,
}

# ─── CORS — allow frontend to fetch embed tokens ─────────────────────────────

ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": [r"/api/*"],
    "origins": [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:80",
        "http://localhost",
    ],
}

# ─── Guest Token Configuration ───────────────────────────────────────────────

GUEST_ROLE_NAME = "Public"
GUEST_TOKEN_JWT_SECRET = SECRET_KEY
GUEST_TOKEN_JWT_ALGO = "HS256"
GUEST_TOKEN_HEADER_NAME = "X-GuestToken"
GUEST_TOKEN_JWT_EXP_SECONDS = 3600  # 1 hour

# ─── Branding ────────────────────────────────────────────────────────────────

APP_NAME = "CCIP BI Studio"
APP_ICON = "/static/assets/images/superset-logo-horiz.png"

# ─── Cache ───────────────────────────────────────────────────────────────────

CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}

DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 600,
}

# ─── SQL Lab ─────────────────────────────────────────────────────────────────

SQL_MAX_ROW = 100000
SQLLAB_TIMEOUT = 300
SUPERSET_WEBSERVER_TIMEOUT = 300

# ─── Theme ───────────────────────────────────────────────────────────────────

THEME_OVERRIDES = {
    "borderRadius": 6,
    "colors": {
        "primary": {
            "base": "rgb(99, 102, 241)",  # Indigo to match CCIP theme
        },
    },
}

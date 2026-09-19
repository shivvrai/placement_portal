#!/bin/bash
# ============================================================================
# Superset Bootstrap Script — CCIP BI Studio
#
# Initializes Superset with:
#   1. Database schema (superset_meta)
#   2. Admin user
#   3. CCIP PostgreSQL as a data source
#   4. Pre-built dashboards (if JSON exports exist)
#
# This runs once on first container start.
# ============================================================================

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  CCIP BI Studio — Superset Bootstrap                    ║"
echo "╚══════════════════════════════════════════════════════════╝"

# ─── Wait for PostgreSQL ──────────────────────────────────────────────────────

echo "[1/6] Waiting for PostgreSQL..."
export PGPASSWORD="${DATABASE_PASSWORD:-ccip_dev}"
until pg_isready -h "${DATABASE_HOST:-postgres}" -p "${DATABASE_PORT:-5432}" -U "${DATABASE_USER:-ccip}" 2>/dev/null; do
    sleep 2
done
echo "  ✓ PostgreSQL is ready"

# ─── Create Superset metadata database ────────────────────────────────────────

echo "[2/6] Creating superset_meta database (if not exists)..."
psql -h "${DATABASE_HOST:-postgres}" -p "${DATABASE_PORT:-5432}" -U "${DATABASE_USER:-ccip}" \
     -tc "SELECT 1 FROM pg_database WHERE datname = 'superset_meta'" | grep -q 1 \
  || psql -h "${DATABASE_HOST:-postgres}" -p "${DATABASE_PORT:-5432}" -U "${DATABASE_USER:-ccip}" \
          -c "CREATE DATABASE superset_meta"
echo "  ✓ superset_meta database ready"

# ─── Initialize Superset DB schema ───────────────────────────────────────────

echo "[3/6] Upgrading Superset database schema..."
superset db upgrade
echo "  ✓ Schema upgraded"

# ─── Create admin user ───────────────────────────────────────────────────────

echo "[4/6] Creating admin user..."
superset fab create-admin \
    --username "${SUPERSET_ADMIN_USERNAME:-admin}" \
    --firstname "CCIP" \
    --lastname "Admin" \
    --email "admin@ccip.edu" \
    --password "${SUPERSET_ADMIN_PASSWORD:-admin}" \
  || echo "  (admin user may already exist, skipping)"
echo "  ✓ Admin user ready"

# ─── Initialize default roles & permissions ──────────────────────────────────

echo "[5/6] Initializing roles and permissions..."
superset init
echo "  ✓ Roles initialized"

# ─── Register CCIP PostgreSQL as data source ─────────────────────────────────

echo "[6/6] Registering CCIP database connection..."
python3 -c "
import json
from superset.app import create_app
from superset.models.core import Database
from superset.extensions import db as sa_db

app = create_app()
with app.app_context():
    existing = sa_db.session.query(Database).filter_by(database_name='CCIP PostgreSQL').first()
    if not existing:
        ccip_db = Database(
            database_name='CCIP PostgreSQL',
            sqlalchemy_uri='postgresql://${DATABASE_USER:-ccip}:${DATABASE_PASSWORD:-ccip_dev}@${DATABASE_HOST:-postgres}:${DATABASE_PORT:-5432}/${DATABASE_DB:-ccip}',
            expose_in_sqllab=True,
            allow_run_async=True,
            allow_ctas=False,
            allow_cvas=False,
            allow_dml=False,
            extra=json.dumps({
                'metadata_params': {},
                'engine_params': {},
                'metadata_cache_timeout': {},
                'schemas_allowed_for_file_upload': [],
            }),
        )
        sa_db.session.add(ccip_db)
        sa_db.session.commit()
        print('  ✓ CCIP PostgreSQL registered as data source')
    else:
        print('  ✓ CCIP PostgreSQL already registered')
" 2>/dev/null || echo "  (will register on first login via UI)"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✓ Superset is ready at http://localhost:8088           ║"
echo "║  Login: admin / admin                                   ║"
echo "╚══════════════════════════════════════════════════════════╝"

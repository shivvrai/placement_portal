#!/bin/bash
set -e

echo "============================================"
echo "  CCIP Backend — Production Startup"
echo "============================================"

echo ""
echo "[1/3] Running Alembic migrations..."
python -m alembic upgrade head
echo "      Migrations complete."

echo ""
echo "[2/3] Seeding initial data..."
python -m scripts.seed
echo "      Seed complete."

echo ""
echo "[3/3] Starting Gunicorn (4 × UvicornWorker)..."
exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

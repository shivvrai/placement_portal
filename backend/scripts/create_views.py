#!/usr/bin/env python3
"""
Create/update analytics SQL views in the database.

These views power both Apache Superset (direct SQL) and Power BI (OData feed).
Idempotent — safe to run multiple times (uses CREATE OR REPLACE VIEW).

Usage:
    python -m scripts.create_views          # from backend/
    python scripts/create_views.py          # direct
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend root to path so 'app' package resolves
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def create_views():
    """Read and execute the analytics_views.sql file against the database."""
    from app.core.database import engine

    sql_file = Path(__file__).resolve().parent.parent / "sql" / "analytics_views.sql"
    if not sql_file.exists():
        print(f"[ERROR] SQL file not found: {sql_file}")
        sys.exit(1)

    sql_content = sql_file.read_text(encoding="utf-8")

    # Split into individual statements (separated by semicolons)
    statements = [
        stmt.strip()
        for stmt in sql_content.split(";")
        if stmt.strip() and not stmt.strip().startswith("--")
    ]

    print(f"[INFO] Found {len(statements)} SQL statements in {sql_file.name}")

    from sqlalchemy import text

    async with engine.begin() as conn:
        for i, stmt in enumerate(statements, 1):
            # Extract view name for logging
            view_name = "unknown"
            for line in stmt.split("\n"):
                if "CREATE OR REPLACE VIEW" in line.upper():
                    parts = line.split()
                    idx = [p.upper() for p in parts].index("VIEW")
                    if idx + 1 < len(parts):
                        view_name = parts[idx + 1]
                    break

            try:
                await conn.execute(text(stmt))
                print(f"  [{i}/{len(statements)}] ✓ {view_name}")
            except Exception as e:
                print(f"  [{i}/{len(statements)}] ✗ {view_name}: {e}")

    print("[INFO] Analytics views created/updated successfully.")


if __name__ == "__main__":
    asyncio.run(create_views())

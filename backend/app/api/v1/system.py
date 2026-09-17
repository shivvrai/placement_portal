"""
System API — audit log viewer for TPO / Admin.

Routes:
  GET  /api/v1/system/audit-logs    — paginated audit trail with filters
"""

import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import RoleChecker
from app.models.user import User
from app.models.system import AuditLog

router = APIRouter(prefix="/system", tags=["System & Audit"])

_tpo_admin = RoleChecker(["tpo", "admin"])


# ─── Response helper ─────────────────────────────────────────────────────────

def _log_to_dict(log: AuditLog) -> dict:
    return {
        "id": str(log.id),
        "event_type": log.action,
        "resource_type": log.entity_type,
        "resource_id": log.entity_id,
        "actor_id": str(log.user_id) if log.user_id else None,
        "details": log.details or {},
        "ip_address": log.ip_address,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


# ─── Audit log endpoint ──────────────────────────────────────────────────────

@router.get("/audit-logs", summary="Paginated TPO activity & audit trail")
async def get_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by exact event_type e.g. DRIVE_CREATE"),
    actor_id: Optional[str] = Query(None, description="Filter by actor UUID (partial ok)"),
    date_from: Optional[datetime] = Query(None, description="ISO datetime lower bound"),
    date_to: Optional[datetime] = Query(None, description="ISO datetime upper bound"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns paginated AuditLog records, newest first.

    Filters:
    - event_type  : exact match (e.g. DRIVE_CREATE, UMS_SYNC_TRIGGERED)
    - actor_id    : filter to a specific user's actions
    - date_from   : only logs after this datetime
    - date_to     : only logs before this datetime
    """
    conditions = []

    if event_type:
        conditions.append(AuditLog.action == event_type)

    if actor_id:
        try:
            aid = uuid.UUID(actor_id)
            conditions.append(AuditLog.user_id == aid)
        except ValueError:
            pass  # ignore malformed UUID

    if date_from:
        conditions.append(AuditLog.created_at >= date_from)

    if date_to:
        conditions.append(AuditLog.created_at <= date_to)

    # Count total matching rows
    count_stmt = select(AuditLog)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    # Fetch page
    stmt = (
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if conditions:
        stmt = stmt.where(and_(*conditions))

    result = await db.execute(stmt)
    logs = result.scalars().all()

    total_pages = max(1, (total + page_size - 1) // page_size)

    return {
        "data": [_log_to_dict(log) for log in logs],
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }

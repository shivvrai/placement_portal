"""
Audit Trail — writes immutable audit rows to the AuditLog table.

Usage:
    from app.core.audit import record_audit_event

    await record_audit_event(
        db=db,
        actor_id=current_user.id,
        event_type="DRIVE_CREATE",
        resource_type="PlacementDrive",
        resource_id=str(drive.id),
        details={"company": drive.company_name, "title": drive.title},
        ip_address=request.client.host if request else None,
    )

IMPORTANT:
- Call db.flush() inside this helper, NOT db.commit().
- The outer endpoint's commit will persist both the main record and the audit row atomically.
- This helper never raises — write failures are printed to stderr.
"""

import sys
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import AuditLog


# ─── Allowed event types ───────────────────────────────────────────────────────
AUDIT_EVENTS = [
    "DRIVE_CREATE",
    "DRIVE_UPDATE",
    "DRIVE_CANCEL",
    "APPLICATION_STATUS_CHANGE",
    "OFFER_RECORDED",
    "UMS_SYNC_TRIGGERED",
    "SKILL_VERIFIED",
    "STUDENT_PROFILE_UPDATE",
    "SHORTLIST_GENERATED",
    "ACCREDITATION_REPORT_EXPORTED",
    "OFFER_LETTER_UPLOADED",
    "OFFER_ACCEPTED",
    "OFFER_DECLINED",
]

# ─── Event → color mapping (used by frontend drawer) ─────────────────────────
EVENT_COLORS = {
    "DRIVE_CREATE": "green",
    "DRIVE_UPDATE": "yellow",
    "DRIVE_CANCEL": "red",
    "APPLICATION_STATUS_CHANGE": "red",
    "OFFER_RECORDED": "green",
    "UMS_SYNC_TRIGGERED": "blue",
    "SKILL_VERIFIED": "green",
    "STUDENT_PROFILE_UPDATE": "yellow",
    "SHORTLIST_GENERATED": "blue",
    "ACCREDITATION_REPORT_EXPORTED": "blue",
    "OFFER_LETTER_UPLOADED": "blue",
    "OFFER_ACCEPTED": "green",
    "OFFER_DECLINED": "red",
}


async def record_audit_event(
    db: AsyncSession,
    actor_id: uuid.UUID,
    event_type: str,
    resource_type: str,
    resource_id: str,
    details: dict,
    ip_address: Optional[str] = None,
) -> None:
    """
    Writes one immutable AuditLog row to the database.

    Parameters
    ----------
    db            : AsyncSession — the current request's DB session.
    actor_id      : UUID of the user performing the action.
    event_type    : One of AUDIT_EVENTS strings above.
    resource_type : ORM model name, e.g. "PlacementDrive", "Application".
    resource_id   : String representation of the affected record's PK.
    details       : Arbitrary JSON-serialisable dict (old value, new value, etc.)
    ip_address    : Optional client IP from request.client.host.
    """
    try:
        log = AuditLog(
            id=uuid.uuid4(),
            user_id=actor_id,
            action=event_type,
            entity_type=resource_type,
            entity_id=str(resource_id),
            details=details,
            ip_address=ip_address,
        )
        db.add(log)
        await db.flush()   # flush only — the endpoint's own commit handles persistence
    except Exception as exc:
        print(f"[AUDIT] Failed to write audit log: {exc}", file=sys.stderr)

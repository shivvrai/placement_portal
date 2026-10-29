"""
SQLAlchemy ORM models — Intelligence & System domain.
Tables: audit_logs, used_reset_tokens
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.db_types import UUIDType, JSONB


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[str | None] = mapped_column(String(50))
    details = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class UsedResetToken(Base):
    __tablename__ = "used_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

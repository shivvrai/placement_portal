"""
SQLAlchemy ORM models — Drive Announcements.
Table: drive_announcements
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType


def utcnow():
    return datetime.now(timezone.utc)


class DriveAnnouncement(Base):
    __tablename__ = "drive_announcements"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    drive_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("placement_drives.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    urgency: Mapped[str] = mapped_column(String(20), default="normal")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    drive = relationship("PlacementDrive", backref="announcements")
    author = relationship("User")

    __table_args__ = (
        CheckConstraint(
            "urgency IN ('normal', 'important', 'urgent')",
            name="ck_announcement_urgency",
        ),
    )

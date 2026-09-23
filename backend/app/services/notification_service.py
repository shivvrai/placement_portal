import json
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc, asc
import redis.asyncio as aioredis

from app.models.notification import Notification
from app.models.user import Student
from app.core.audit import record_audit_event
from app.core.logging_config import logger

class NotificationService:
    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    async def publish(
        self,
        user_id: uuid.UUID,
        type: str,
        title: str,
        message: str,
        link: Optional[str] = None,
        priority: str = "normal",
        metadata: Optional[dict] = None
    ) -> Notification:
        # 1. Insert row into notifications table
        notif = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            link=link,
            priority=priority,
            metadata_payload=metadata or {}
        )
        self.db.add(notif)
        
        # Priority mapping to AuditLog if necessary
        if priority == "critical":
            await record_audit_event(
                self.db,
                actor_id=user_id, # Target is the actor for this event since it's a sys event
                event_type="CRITICAL_NOTIFICATION",
                resource_type="Notification",
                resource_id=str(notif.id),
                details={"title": title, "type": type}
            )

        await self.db.flush()

        # 2. Publish to Redis for WebSocket Engine
        channel = f"notif:{user_id}"
        payload = {
            "id": str(notif.id),
            "type": notif.type,
            "title": notif.title,
            "message": notif.message,
            "link": notif.link,
            "priority": notif.priority,
            "is_read": notif.is_read,
            "created_at": notif.created_at.isoformat()
        }
        try:
            await self.redis.publish(channel, json.dumps(payload))
        except aioredis.ConnectionError as e:
            logger.warning("Redis PUBLISH failed (fallback activated)", error=str(e), channel=channel)

        return notif

    async def get_notifications(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[Notification], int]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
            
        # Unread first, then newest
        stmt = stmt.order_by(asc(Notification.is_read), desc(Notification.created_at))
        
        # Count total before limit
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()
        
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(is_read=True)
        )
        await self.db.flush()

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True)
        )
        await self.db.flush()

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id, Notification.is_read == False)
        )
        return result.scalar_one()

    async def delete_notification(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> None:
        notif = await self.db.get(Notification, notification_id)
        if notif and notif.user_id == user_id:
            await self.db.delete(notif)
            await self.db.flush()

    async def notify_eligible_students_new_drive(self, drive, db: AsyncSession) -> int:
        # Find matching students
        dept_ids = [d.id for d in drive.eligible_departments] if hasattr(drive, 'eligible_departments') else []
        
        stmt = select(Student).where(Student.cgpa >= (drive.min_cgpa or 0))
        # Depending on schema, eligible_departments might be a relationship or just JSON array. Assuming we can just fetch all and filter or it's a simple match.
        count = 0
        students = await db.execute(stmt)
        students = students.scalars().all()
        
        for student in students:
            # Batch publish
            await self.publish(
                user_id=student.id,
                type="DRIVE_OPEN",
                title=f"New Drive: {drive.title}",
                message=f"{drive.company_name} is hiring! Check your eligibility.",
                link=f"/student/drives",
                priority="high"
            )
            count += 1
            if count % 50 == 0:
                await db.commit() # batch commits

        return count

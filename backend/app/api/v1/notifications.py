import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from typing import Any

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])
settings = get_settings()

redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_notification_service(db: AsyncSession = Depends(get_db)):
    return NotificationService(db, redis_client)

@router.get("")
async def get_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    items, total = await service.get_notifications(current_user.id, unread_only, page, page_size)
    data = []
    for notif in items:
        data.append({
            "id": notif.id,
            "type": notif.type,
            "title": notif.title,
            "message": notif.message,
            "link": notif.link,
            "priority": notif.priority,
            "is_read": notif.is_read,
            "created_at": notif.created_at
        })
    return {"data": data, "total": total, "page": page, "page_size": page_size}

@router.post("/{id}/read")
async def mark_read(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
    db: AsyncSession = Depends(get_db)
):
    await service.mark_read(id, current_user.id)
    await db.commit()
    return {"success": True}

@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
    db: AsyncSession = Depends(get_db)
):
    await service.mark_all_read(current_user.id)
    await db.commit()
    return {"success": True}

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    count = await service.get_unread_count(current_user.id)
    return {"count": count}

@router.delete("/{id}")
async def delete_notification(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
    db: AsyncSession = Depends(get_db)
):
    await service.delete_notification(id, current_user.id)
    await db.commit()
    return {"success": True}

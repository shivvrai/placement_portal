"""
API router — In-App Notification Center.
Prefix: /notifications
"""

import json
import uuid
from typing import Optional, List, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.models.notification import Notification
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])
settings = get_settings()

try:
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None


async def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    client = redis_client
    if client is None:
        try:
            client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception:
            client = None
    return NotificationService(db, client)


# ─── Schemas ──────────────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    message: str
    link: Optional[str] = None
    priority: Optional[str] = "normal"
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    unread_count: int


# ─── Helper Functions ─────────────────────────────────────────────────────────

async def create_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    message: str,
    type: str = "info",
    link: Optional[str] = None,
    priority: str = "normal",
) -> Notification:
    """Helper utility to inject notifications into a user's feed with real-time publish."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        link=link,
        priority=priority,
        is_read=False,
    )
    db.add(notif)
    await db.flush()

    try:
        r = redis_client or aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        channel = f"notif:{user_id}"
        payload = {
            "id": str(notif.id),
            "type": notif.type,
            "title": notif.title,
            "message": notif.message,
            "link": notif.link,
            "priority": notif.priority,
            "is_read": notif.is_read,
            "created_at": notif.created_at.isoformat() if notif.created_at else None,
        }
        await r.publish(channel, json.dumps(payload))
    except Exception:
        pass

    return notif


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("", summary="Get notifications (paginated)")
async def get_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
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
            "created_at": notif.created_at,
        })
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/mine", response_model=NotificationListResponse, summary="Get my notifications")
async def get_my_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns latest notifications for the authenticated user, newest first,
    along with total count of unread notifications.
    """
    count_res = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    unread_count = count_res.scalar() or 0

    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)

    query = query.order_by(desc(Notification.created_at)).limit(limit)
    res = await db.execute(query)
    items = res.scalars().all()

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        unread_count=unread_count,
    )


@router.get("/unread-count", summary="Get unread notification count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    count = await service.get_unread_count(current_user.id)
    return {"count": count}


@router.patch("/{notification_id}/read", response_model=NotificationResponse, summary="Mark notification as read (PATCH)")
async def mark_notification_read_patch(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Marks a single notification as read (PATCH format).
    """
    res = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = res.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notif.is_read = True
    await db.commit()
    await db.refresh(notif)
    return NotificationResponse.model_validate(notif)


@router.post("/{notification_id}/read", summary="Mark notification as read (POST)")
async def mark_read_post(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
    db: AsyncSession = Depends(get_db),
):
    await service.mark_read(notification_id, current_user.id)
    await db.commit()
    return {"success": True}


@router.patch("/read-all", summary="Mark all notifications as read (PATCH)")
async def mark_all_notifications_read_patch(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Marks all unread notifications for current user as read (PATCH format).
    """
    stmt = (
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    await db.commit()

    return {
        "message": "All notifications marked as read",
        "updated_count": result.rowcount,
    }


@router.post("/read-all", summary="Mark all notifications as read (POST)")
async def mark_all_read_post(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
    db: AsyncSession = Depends(get_db),
):
    await service.mark_all_read(current_user.id)
    await db.commit()
    return {"success": True}


@router.delete("/{notification_id}", summary="Delete a notification")
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
    db: AsyncSession = Depends(get_db),
):
    await service.delete_notification(notification_id, current_user.id)
    await db.commit()
    return {"success": True}

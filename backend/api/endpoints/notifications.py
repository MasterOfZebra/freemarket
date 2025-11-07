"""
API endpoints for user notifications and events.

Provides REST endpoints for managing user notifications with real-time updates.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.notification_service import get_notification_service
from backend.models import EventType
from backend.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
def get_user_notifications(
    current_user=Depends(get_current_user_optional),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    db: Session = Depends(get_db)
):
    """
    Get user's notifications/events.

    Query parameters:
    - limit: Max notifications to return (1-100)
    - offset: Pagination offset
    - unread_only: Return only unread notifications
    - event_type: Filter by specific event type
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    notification_service = get_notification_service(db)

    # Parse event type filter
    event_types = None
    if event_type:
        try:
            event_types = [EventType(event_type)]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

    notifications = notification_service.get_user_events(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
        event_types=event_types
    )

    return {
        "notifications": notifications,
        "limit": limit,
        "offset": offset,
        "unread_only": unread_only
    }


@router.get("/unread-count")
def get_unread_notification_count(
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get count of unread notifications by type.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    notification_service = get_notification_service(db)
    counts = notification_service.get_unread_count(current_user.id)

    return {
        "counts": counts,
        "user_id": current_user.id
    }


@router.put("/{event_id}/read")
def mark_notification_read(
    event_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Mark a specific notification as read.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    notification_service = get_notification_service(db)
    success = notification_service.mark_event_read(event_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found or already read")

    return {"status": "marked_read", "event_id": event_id}


@router.put("/mark-all-read")
def mark_all_notifications_read(
    current_user=Depends(get_current_user_optional),
    event_type: Optional[str] = Query(None, description="Mark only specific event type as read"),
    db: Session = Depends(get_db)
):
    """
    Mark all user's notifications as read.

    Query parameters:
    - event_type: Mark only specific event type as read (optional)
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    notification_service = get_notification_service(db)

    # Parse event type filter
    event_types = None
    if event_type:
        try:
            event_types = [EventType(event_type)]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

    count = notification_service.mark_all_read(current_user.id, event_types)

    return {
        "status": "marked_read",
        "count": count,
        "event_type": event_type
    }


@router.delete("/{event_id}")
def delete_notification(
    event_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Delete a specific notification.

    Note: Only read notifications can be deleted by regular users.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # For now, only allow deleting read notifications
    # In the future, we might allow users to delete any notification
    notification_service = get_notification_service(db)

    # Check if event exists and belongs to user
    events = notification_service.get_user_events(current_user.id, limit=1, offset=0)
    event = next((e for e in events if e["id"] == event_id), None)

    if not event:
        raise HTTPException(status_code=404, detail="Notification not found")

    if not event["is_read"]:
        raise HTTPException(status_code=400, detail="Cannot delete unread notification")

    # Delete the event
    try:
        from backend.models import UserEvent
        db.query(UserEvent).filter(
            UserEvent.id == event_id,
            UserEvent.user_id == current_user.id
        ).delete()
        db.commit()

        return {"status": "deleted", "event_id": event_id}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")


# Admin endpoints (would need admin auth)
@router.delete("/admin/cleanup")
def cleanup_old_notifications(
    days_old: int = Query(30, ge=7, le=365, description="Delete events older than this many days"),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: Delete old read notifications for cleanup.

    Requires admin privileges.
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    notification_service = get_notification_service(db)
    deleted_count = notification_service.delete_old_events(days_old)

    return {
        "status": "cleanup_completed",
        "deleted_count": deleted_count,
        "days_old": days_old
    }


# WebSocket endpoint for real-time notifications (would be in separate file)
# @router.websocket("/ws/notifications")
# async def notification_websocket(
#     websocket: WebSocket,
#     token: str = Query(...),
#     current_user=Depends(get_current_user_optional)
# ):
#     # Implementation would go here
#     pass
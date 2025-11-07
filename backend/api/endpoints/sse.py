"""
Server-Sent Events (SSE) endpoints for real-time notifications.

Provides streaming endpoints for clients that can't maintain WebSocket connections.
"""
import json
import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.notification_service import get_notification_service
from backend.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sse", tags=["sse"])


@router.get("/notifications")
async def notification_stream(
    current_user=Depends(get_current_user_optional),
    last_event_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events stream for user notifications.

    Alternative to WebSocket for real-time notifications.
    Clients can reconnect using last_event_id for continuity.

    Usage:
    - Connect: GET /api/sse/notifications
    - Handle events in JavaScript: new EventSource('/api/sse/notifications')
    """
    if not current_user:
        return StreamingResponse(
            content=iter(["event: error\ndata: Authentication required\n\n"]),
            media_type="text/event-stream"
        )

    async def event_generator():
        """Generate SSE events for user notifications"""
        try:
            notification_service = get_notification_service(db)

            # Send initial data
            initial_events = notification_service.get_user_events(
                user_id=current_user.id,
                limit=10,
                unread_only=False
            )

            for event in initial_events:
                event_data = {
                    "type": "notification",
                    "data": event
                }
                yield f"event: notification\nid: {event['id']}\ndata: {json.dumps(event_data)}\n\n"
                await asyncio.sleep(0.1)  # Small delay to prevent overwhelming client

            # Send unread count
            unread_counts = notification_service.get_unread_count(current_user.id)
            yield f"event: unread_count\ndata: {json.dumps(unread_counts)}\n\n"

            # Keep connection alive with ping events
            ping_count = 0
            while True:
                ping_count += 1
                yield f"event: ping\ndata: {{\"count\": {ping_count}}}\n\n"
                await asyncio.sleep(30)  # Ping every 30 seconds

        except Exception as e:
            logger.error(f"SSE stream error for user {current_user.id}: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        }
    )


@router.get("/user-status")
async def user_status_stream():
    """
    SSE stream for user online/offline status.

    This would need to be integrated with WebSocket connection tracking.
    For now, returns a basic ping stream.
    """
    async def status_generator():
        """Generate status update events"""
        try:
            while True:
                # In a real implementation, this would check Redis for user status
                status_data = {
                    "online_users": 0,  # Would be populated from Redis
                    "timestamp": asyncio.get_event_loop().time()
                }
                yield f"event: status\ndata: {json.dumps(status_data)}\n\n"
                await asyncio.sleep(60)  # Update every minute

        except Exception as e:
            logger.error(f"Status SSE stream error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        status_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

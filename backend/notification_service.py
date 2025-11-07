"""
Notification service for user events and real-time updates.

Handles event creation, Redis Streams broadcasting, and notification management.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from .database import get_db
from .models import UserEvent, EventType, User
from .config import REDIS_URL

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class NotificationService:
    """
    Service for managing user notifications and events.
    """

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.redis_client: Optional[redis.Redis] = None

        if REDIS_AVAILABLE and REDIS_URL:
            try:
                self.redis_client = redis.from_url(REDIS_URL)
                logger.info("Connected to Redis for notifications")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")

    async def create_event(
        self,
        user_id: int,
        event_type: EventType,
        related_id: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> Optional[UserEvent]:
        """
        Create a new user event/notification.

        Args:
            user_id: User to notify
            event_type: Type of event
            related_id: ID of related object (optional)
            payload: Additional event data

        Returns:
            Created UserEvent or None if failed
        """
        try:
            event = UserEvent(
                user_id=user_id,
                event_type=event_type,
                related_id=related_id,
                payload=payload or {}
            )

            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)

            logger.info(f"Created event {event.id} for user {user_id}: {event_type.value}")

            # Broadcast to Redis Streams
            await self._broadcast_event(event)

            return event

        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            self.db.rollback()
            return None

    async def _broadcast_event(self, event: UserEvent):
        """
        Broadcast event to Redis Streams for real-time delivery.
        """
        if not self.redis_client:
            return

        try:
            event_data = {
                "id": event.id,
                "user_id": event.user_id,
                "event_type": event.event_type.value,
                "related_id": event.related_id,
                "payload": event.payload,
                "created_at": event.created_at.isoformat() if event.created_at else None
            }

            # Add to user-specific stream
            stream_key = f"user_events:{event.user_id}"
            await self.redis_client.xadd(stream_key, event_data)

            # Also add to global stream for monitoring
            await self.redis_client.xadd("user_events_global", event_data)

            logger.debug(f"Broadcasted event {event.id} to Redis Streams")

        except Exception as e:
            logger.error(f"Failed to broadcast event to Redis: {e}")

    def get_user_events(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        event_types: Optional[List[EventType]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user's events/notifications.

        Args:
            user_id: User ID
            limit: Max events to return
            offset: Pagination offset
            unread_only: Return only unread events
            event_types: Filter by specific event types

        Returns:
            List of event dictionaries
        """
        try:
            query = self.db.query(UserEvent).filter(UserEvent.user_id == user_id)

            if unread_only:
                query = query.filter(UserEvent.is_read == False)

            if event_types:
                query = query.filter(UserEvent.event_type.in_(event_types))

            events = query.order_by(
                desc(UserEvent.created_at)
            ).offset(offset).limit(limit).all()

            return [event.to_dict() for event in events]

        except Exception as e:
            logger.error(f"Failed to get user events: {e}")
            return []

    def mark_event_read(self, event_id: int, user_id: int) -> bool:
        """
        Mark a specific event as read.

        Args:
            event_id: Event ID
            user_id: User ID (for security)

        Returns:
            True if marked successfully
        """
        try:
            event = self.db.query(UserEvent).filter(
                and_(
                    UserEvent.id == event_id,
                    UserEvent.user_id == user_id
                )
            ).first()

            if event and not event.is_read:
                event.is_read = True
                event.read_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"Marked event {event_id} as read for user {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to mark event as read: {e}")
            self.db.rollback()
            return False

    def mark_all_read(self, user_id: int, event_types: Optional[List[EventType]] = None) -> int:
        """
        Mark all user's events as read.

        Args:
            user_id: User ID
            event_types: Specific event types to mark (None = all)

        Returns:
            Number of events marked as read
        """
        try:
            query = self.db.query(UserEvent).filter(
                and_(
                    UserEvent.user_id == user_id,
                    UserEvent.is_read == False
                )
            )

            if event_types:
                query = query.filter(UserEvent.event_type.in_(event_types))

            count = query.update({
                "is_read": True,
                "read_at": datetime.utcnow()
            })

            if count > 0:
                self.db.commit()
                logger.info(f"Marked {count} events as read for user {user_id}")

            return count

        except Exception as e:
            logger.error(f"Failed to mark all events as read: {e}")
            self.db.rollback()
            return 0

    def get_unread_count(self, user_id: int, event_types: Optional[List[EventType]] = None) -> Dict[str, int]:
        """
        Get unread event counts by type.

        Args:
            user_id: User ID
            event_types: Specific types to count (None = all types)

        Returns:
            Dict mapping event type to count
        """
        try:
            query = self.db.query(
                UserEvent.event_type,
                func.count(UserEvent.id)
            ).filter(
                and_(
                    UserEvent.user_id == user_id,
                    UserEvent.is_read == False
                )
            ).group_by(UserEvent.event_type)

            if event_types:
                query = query.filter(UserEvent.event_type.in_(event_types))

            results = query.all()

            counts = {event_type.value: count for event_type, count in results}
            counts["total"] = sum(counts.values())

            return counts

        except Exception as e:
            logger.error(f"Failed to get unread counts: {e}")
            return {"total": 0}

    def delete_old_events(self, days_old: int = 30) -> int:
        """
        Delete old read events for cleanup.

        Args:
            days_old: Delete events older than this many days

        Returns:
            Number of events deleted
        """
        try:
            from sqlalchemy import text

            # Delete read events older than specified days
            deleted = self.db.execute(text("""
                DELETE FROM user_events
                WHERE is_read = true
                  AND created_at < NOW() - INTERVAL ':days days'
            """), {"days": days_old})

            count = deleted.rowcount
            self.db.commit()

            if count > 0:
                logger.info(f"Deleted {count} old read events")

            return count

        except Exception as e:
            logger.error(f"Failed to delete old events: {e}")
            self.db.rollback()
            return 0

    # Convenience methods for common events
    async def notify_message_received(self, recipient_id: int, exchange_id: str, sender_id: int):
        """Notify user about new message"""
        await self.create_event(
            user_id=recipient_id,
            event_type=EventType.MESSAGE_RECEIVED,
            related_id=sender_id,  # sender_id as related_id
            payload={"exchange_id": exchange_id, "sender_id": sender_id}
        )

    async def notify_offer_matched(self, user_id: int, match_id: int, exchange_type: str):
        """Notify user about new offer match"""
        await self.create_event(
            user_id=user_id,
            event_type=EventType.OFFER_MATCHED,
            related_id=match_id,
            payload={"exchange_type": exchange_type}
        )

    async def notify_exchange_created(self, user_id: int, exchange_id: str):
        """Notify user about exchange creation"""
        await self.create_event(
            user_id=user_id,
            event_type=EventType.EXCHANGE_CREATED,
            payload={"exchange_id": exchange_id}
        )

    async def notify_exchange_completed(self, user_id: int, exchange_id: str):
        """Notify user about exchange completion"""
        await self.create_event(
            user_id=user_id,
            event_type=EventType.EXCHANGE_COMPLETED,
            payload={"exchange_id": exchange_id}
        )

    async def notify_review_received(self, user_id: int, review_id: int, rating: int):
        """Notify user about received review"""
        await self.create_event(
            user_id=user_id,
            event_type=EventType.REVIEW_RECEIVED,
            related_id=review_id,
            payload={"rating": rating}
        )


# Global service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service(db: Session = None) -> NotificationService:
    """Get global notification service instance"""
    global _notification_service
    if _notification_service is None or db:
        _notification_service = NotificationService(db)
    return _notification_service

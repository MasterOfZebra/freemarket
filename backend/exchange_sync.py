"""
Redis Stream for real-time exchange synchronization.

Broadcasts exchange events to connected clients for UI updates.
"""
import json
import logging
import asyncio
from typing import Optional, Dict, Any

from .config import REDIS_URL
from .database import get_db
from .exchange_history_service import get_exchange_history_service

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class ExchangeSyncService:
    """
    Service for real-time synchronization of exchange events.
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.stream_name = "exchange_events"

    async def connect(self):
        """Connect to Redis"""
        if not REDIS_AVAILABLE or not REDIS_URL:
            logger.warning("Redis not available for exchange sync")
            return False

        try:
            self.redis_client = redis.from_url(REDIS_URL)
            logger.info("Exchange sync service connected to Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to connect Exchange sync service to Redis: {e}")
            return False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()

    async def publish_event(self, event_type: str, exchange_id: str, data: Dict[str, Any]):
        """
        Publish exchange event to Redis Stream.

        Args:
            event_type: Type of event (created, confirmed, completed, etc.)
            exchange_id: Exchange identifier
            data: Event data payload
        """
        if not self.redis_client:
            return

        try:
            event_data = {
                "event_type": event_type,
                "exchange_id": exchange_id,
                "timestamp": asyncio.get_event_loop().time(),
                "data": data
            }

            await self.redis_client.xadd(
                self.stream_name,
                event_data,
                maxlen=1000  # Keep last 1000 events
            )

            logger.debug(f"Published exchange event: {event_type} for {exchange_id}")

        except Exception as e:
            logger.error(f"Failed to publish exchange event: {e}")

    async def get_recent_events(self, exchange_id: Optional[str] = None, limit: int = 50):
        """
        Get recent exchange events from stream.

        Args:
            exchange_id: Filter by specific exchange (optional)
            limit: Max events to return

        Returns:
            List of recent events
        """
        if not self.redis_client:
            return []

        try:
            # Read from stream
            stream_data = await self.redis_client.xrevrange(
                self.stream_name,
                count=limit
            )

            events = []
            for message_id, message_data in stream_data:
                event = {
                    "id": message_id,
                    **message_data
                }

                # Filter by exchange_id if specified
                if exchange_id and event.get("exchange_id") != exchange_id:
                    continue

                events.append(event)

            return events

        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            return []

    def notify_exchange_created(self, exchange_id: str, participants: list):
        """Notify about exchange creation"""
        asyncio.create_task(self.publish_event(
            "created",
            exchange_id,
            {
                "participants": participants,
                "action": "exchange_created"
            }
        ))

    def notify_exchange_confirmed(self, exchange_id: str, confirmer_id: int):
        """Notify about exchange confirmation"""
        asyncio.create_task(self.publish_event(
            "confirmed",
            exchange_id,
            {
                "confirmer_id": confirmer_id,
                "action": "exchange_confirmed"
            }
        ))

    def notify_exchange_completed(self, exchange_id: str, participants: list):
        """Notify about exchange completion"""
        asyncio.create_task(self.publish_event(
            "completed",
            exchange_id,
            {
                "participants": participants,
                "action": "exchange_completed"
            }
        ))

    def notify_exchange_cancelled(self, exchange_id: str, cancelled_by: int):
        """Notify about exchange cancellation"""
        asyncio.create_task(self.publish_event(
            "cancelled",
            exchange_id,
            {
                "cancelled_by": cancelled_by,
                "action": "exchange_cancelled"
            }
        ))

    def notify_message_sent(self, exchange_id: str, sender_id: int, message_count: int):
        """Notify about new message in exchange"""
        asyncio.create_task(self.publish_event(
            "message_sent",
            exchange_id,
            {
                "sender_id": sender_id,
                "message_count": message_count,
                "action": "new_message"
            }
        ))


# Global service instance
_exchange_sync_service: Optional[ExchangeSyncService] = None


def get_exchange_sync_service() -> ExchangeSyncService:
    """Get global exchange sync service instance"""
    global _exchange_sync_service
    if _exchange_sync_service is None:
        _exchange_sync_service = ExchangeSyncService()
    return _exchange_sync_service


# Integration with exchange endpoints
async def notify_exchange_event(event_type: str, exchange_id: str, **kwargs):
    """
    Convenience function to notify about exchange events.

    Args:
        event_type: Type of event
        exchange_id: Exchange identifier
        **kwargs: Additional event data
    """
    sync_service = get_exchange_sync_service()
    await sync_service.publish_event(event_type, exchange_id, kwargs)


# FastAPI lifespan integration
async def start_exchange_sync():
    """Start exchange sync service during app startup"""
    sync_service = get_exchange_sync_service()
    await sync_service.connect()
    logger.info("Exchange sync service started")


async def stop_exchange_sync():
    """Stop exchange sync service during app shutdown"""
    sync_service = get_exchange_sync_service()
    await sync_service.disconnect()
    logger.info("Exchange sync service stopped")


# Lifespan context manager for FastAPI
async def exchange_sync_lifespan():
    """Context manager for exchange sync service lifespan"""
    await start_exchange_sync()

    yield

    await stop_exchange_sync()

"""
Redis Stream processor for user reports.

Handles asynchronous processing of moderation reports using Redis Streams.
"""
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from .config import REDIS_URL
from .moderation_service import get_moderation_service
from .database import get_db

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class ReportProcessor:
    """
    Redis Stream processor for handling user reports asynchronously.
    """

    def __init__(self, consumer_group: str = "moderation_workers", consumer_name: str = "worker_1"):
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.redis_client: Optional[redis.Redis] = None
        self.stream_name = "reports_stream"
        self.running = False

    async def connect(self):
        """Connect to Redis"""
        if not REDIS_AVAILABLE or not REDIS_URL:
            logger.warning("Redis not available for report processing")
            return False

        try:
            self.redis_client = redis.from_url(REDIS_URL)

            # Create consumer group if it doesn't exist
            try:
                await self.redis_client.xgroup_create(
                    self.stream_name,
                    self.consumer_group,
                    id="0",
                    mkstream=True
                )
                logger.info(f"Created consumer group {self.consumer_group}")
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

            logger.info("Report processor connected to Redis")
            return True

        except Exception as e:
            logger.error(f"Failed to connect Report processor to Redis: {e}")
            return False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()

    async def process_reports(self):
        """Main report processing loop"""
        if not self.redis_client:
            logger.error("Redis client not initialized")
            return

        logger.info(f"Starting report processing loop for {self.consumer_group}:{self.consumer_name}")

        try:
            while self.running:
                try:
                    # Read pending messages from stream
                    messages = await self.redis_client.xreadgroup(
                        groupname=self.consumer_group,
                        consumername=self.consumer_name,
                        streams={self.stream_name: ">"},  # Read new messages
                        count=10,  # Process up to 10 messages at once
                        block=5000  # Block for 5 seconds if no messages
                    )

                    for stream_name, message_list in messages:
                        for message_id, message_data in message_list:
                            await self.process_message(message_id, message_data)

                            # Acknowledge message
                            await self.redis_client.xack(
                                self.stream_name,
                                self.consumer_group,
                                message_id
                            )

                except asyncio.TimeoutError:
                    # Normal timeout, continue loop
                    continue

                except Exception as e:
                    logger.error(f"Error in report processing loop: {e}")
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Report processing loop error: {e}")

        finally:
            logger.info("Report processing loop stopped")

    async def process_message(self, message_id: str, message_data: Dict[str, Any]):
        """
        Process a single report message.

        Args:
            message_id: Redis message ID
            message_data: Message payload
        """
        try:
            # Parse message
            event_type = message_data.get("event_type")
            report_data = message_data.get("report_data", {})

            logger.info(f"Processing report message {message_id}: {event_type}")

            if event_type == "report_created":
                await self._handle_report_created(report_data)
            elif event_type == "auto_moderation_check":
                await self._handle_auto_moderation(report_data)
            else:
                logger.warning(f"Unknown event type: {event_type}")

        except Exception as e:
            logger.error(f"Failed to process report message {message_id}: {e}")

    async def _handle_report_created(self, report_data: Dict[str, Any]):
        """
        Handle newly created report.

        Args:
            report_data: Report creation data
        """
        try:
            # Get moderation service with DB session
            db = next(get_db())
            moderation_service = get_moderation_service(db)

            # Check for auto-moderation triggers
            report_id = report_data.get("report_id")
            if report_id:
                report = db.query(moderation_service.Report).filter(
                    moderation_service.Report.id == report_id
                ).first()

                if report:
                    moderation_service._check_auto_moderation(report)

            logger.info(f"Processed report creation: {report_id}")

        except Exception as e:
            logger.error(f"Failed to handle report creation: {e}")

    async def _handle_auto_moderation(self, report_data: Dict[str, Any]):
        """
        Handle auto-moderation triggers.

        Args:
            report_data: Auto-moderation data
        """
        try:
            # Implement auto-moderation logic
            target_user_id = report_data.get("target_user_id")
            active_reports = report_data.get("active_reports", 0)

            if active_reports >= 5:
                # Severe auto-moderation: temporary ban
                logger.warning(f"Severe auto-moderation triggered for user {target_user_id}")

                # This would trigger admin notification and potential auto-ban
                # For now, just log the event

            elif active_reports >= 3:
                # Moderate auto-moderation: flag for review
                logger.warning(f"Moderate auto-moderation triggered for user {target_user_id}")

        except Exception as e:
            logger.error(f"Failed to handle auto-moderation: {e}")

    async def add_report_to_stream(self, event_type: str, report_data: Dict[str, Any]):
        """
        Add report event to Redis Stream.

        Args:
            event_type: Type of event
            report_data: Event data
        """
        if not self.redis_client:
            return

        try:
            message_data = {
                "event_type": event_type,
                "report_data": report_data,
                "timestamp": asyncio.get_event_loop().time()
            }

            await self.redis_client.xadd(
                self.stream_name,
                message_data
            )

            logger.debug(f"Added {event_type} to reports stream")

        except Exception as e:
            logger.error(f"Failed to add report to stream: {e}")

    async def start(self):
        """Start the report processor"""
        self.running = True

        if not await self.connect():
            logger.error("Failed to start Report processor")
            return

        try:
            await self.process_reports()
        finally:
            await self.disconnect()

    async def stop(self):
        """Stop the report processor"""
        self.running = False
        await self.disconnect()


# Global processor instance
_report_processor: Optional[ReportProcessor] = None


def get_report_processor() -> ReportProcessor:
    """Get global report processor instance"""
    global _report_processor
    if _report_processor is None:
        _report_processor = ReportProcessor()
    return _report_processor


# Integration with moderation service
async def queue_report_for_processing(report_id: int, event_type: str = "report_created"):
    """
    Queue a report for asynchronous processing.

    Args:
        report_id: Report ID
        event_type: Type of processing event
    """
    processor = get_report_processor()
    await processor.add_report_to_stream(event_type, {"report_id": report_id})


# FastAPI lifespan integration
async def start_report_processor():
    """Start report processor during app startup"""
    processor = get_report_processor()
    asyncio.create_task(processor.start())
    logger.info("Report processor started in background")


async def stop_report_processor():
    """Stop report processor during app shutdown"""
    processor = get_report_processor()
    await processor.stop()
    logger.info("Report processor stopped")


# Lifespan context manager for FastAPI
@asynccontextmanager
async def report_processor_lifespan():
    """Async context manager for report processor lifespan"""
    await start_report_processor()
    try:
        yield
    finally:
        await stop_report_processor()

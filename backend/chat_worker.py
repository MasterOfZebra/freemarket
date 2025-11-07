"""
Redis Pub/Sub worker for cross-instance chat message broadcasting.

Listens to Redis channels and forwards messages to connected WebSocket clients.
"""
import json
import logging
import asyncio
from typing import Optional, Dict, Any

from .config import REDIS_URL
from .api.endpoints.chat import manager  # Import connection manager

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class ChatPubSubWorker:
    """
    Redis Pub/Sub worker for chat message broadcasting across server instances.
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.PubSub] = None
        self.running = False

    async def connect(self):
        """Connect to Redis"""
        if not REDIS_AVAILABLE or not REDIS_URL:
            logger.warning("Redis not available for chat Pub/Sub worker")
            return False

        try:
            self.redis_client = redis.from_url(REDIS_URL)
            self.pubsub = self.redis_client.pubsub()

            # Subscribe to chat channels pattern
            await self.pubsub.psubscribe("chat:*")

            logger.info("Chat Pub/Sub worker connected to Redis")
            return True

        except Exception as e:
            logger.error(f"Failed to connect Chat Pub/Sub worker to Redis: {e}")
            return False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.punsubscribe("chat:*")
            await self.pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("Chat Pub/Sub worker disconnected")

    async def process_messages(self):
        """Main message processing loop"""
        if not self.pubsub:
            logger.error("PubSub not initialized")
            return

        logger.info("Starting chat message processing loop")

        try:
            while self.running:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        self.pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=1.0
                    )

                    if message:
                        await self.handle_message(message)

                except asyncio.TimeoutError:
                    # Normal timeout, continue loop
                    continue

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Chat message processing loop error: {e}")

        finally:
            logger.info("Chat message processing loop stopped")

    async def handle_message(self, message: Dict[str, Any]):
        """
        Handle incoming Redis message and forward to WebSocket clients.

        Message format from Redis:
        {
            'type': 'pmessage',
            'pattern': 'chat:*',
            'channel': b'chat:mutual_1_2_10_15',
            'data': b'{"type": "message", ...}'
        }
        """
        try:
            channel = message.get('channel', b'').decode('utf-8')
            data = message.get('data', b'')

            if not channel.startswith('chat:'):
                return

            # Extract exchange_id from channel
            exchange_id = channel[5:]  # Remove 'chat:' prefix

            # Parse message data
            try:
                message_data = json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Failed to parse message data: {e}")
                return

            # Forward to WebSocket connections
            await manager.broadcast_to_exchange(exchange_id, message_data)

            logger.debug(f"Forwarded message to exchange {exchange_id}")

        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")

    async def start(self):
        """Start the Pub/Sub worker"""
        self.running = True

        if not await self.connect():
            logger.error("Failed to start Chat Pub/Sub worker")
            return

        try:
            await self.process_messages()
        finally:
            await self.disconnect()

    async def stop(self):
        """Stop the Pub/Sub worker"""
        self.running = False
        await self.disconnect()


# Global worker instance
_chat_worker: Optional[ChatPubSubWorker] = None


def get_chat_worker() -> ChatPubSubWorker:
    """Get global chat worker instance"""
    global _chat_worker
    if _chat_worker is None:
        _chat_worker = ChatPubSubWorker()
    return _chat_worker


# FastAPI lifespan integration
async def start_chat_worker():
    """Start chat worker during app startup"""
    worker = get_chat_worker()
    asyncio.create_task(worker.start())
    logger.info("Chat Pub/Sub worker started in background")


async def stop_chat_worker():
    """Stop chat worker during app shutdown"""
    worker = get_chat_worker()
    await worker.stop()
    logger.info("Chat Pub/Sub worker stopped")


# Lifespan context manager for FastAPI
async def chat_lifespan():
    """Context manager for chat worker lifespan"""
    await start_chat_worker()

    yield

    await stop_chat_worker()

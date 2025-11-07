"""
Chat service for exchange conversations.

Handles message persistence, Redis Pub/Sub broadcasting, and participant validation.
"""
import json
import logging
from typing import List, Dict, Optional, Set, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from .database import get_db
from .models import ExchangeMessage, MessageType, User, ListingItem
from .config import REDIS_URL

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class ChatService:
    """
    Service for managing exchange chats and real-time messaging.
    """

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.redis_client = None

        if REDIS_AVAILABLE and REDIS_URL:
            try:
                self.redis_client = redis.from_url(REDIS_URL)
                logger.info("Connected to Redis for chat Pub/Sub")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")

    def validate_exchange_participant(self, exchange_id: str, user_id: int) -> bool:
        """
        Validate that user is a participant in the exchange.

        Args:
            exchange_id: Format "mutual_X_Y_A_B"
            user_id: User ID to check

        Returns:
            True if user is participant, False otherwise
        """
        try:
            # Parse exchange_id
            parts = exchange_id.split("_")
            if len(parts) != 5 or parts[0] != "mutual":
                return False

            user_a_id, user_b_id = int(parts[1]), int(parts[2])

            # Check if user is one of the participants
            if user_id not in [user_a_id, user_b_id]:
                return False

            # Additional validation: check if exchange items exist and belong to correct users
            item_a_id, item_b_id = int(parts[3]), int(parts[4])

            item_a = self.db.query(ListingItem).filter(
                ListingItem.id == item_a_id,
                ListingItem.is_archived == False
            ).first()

            item_b = self.db.query(ListingItem).filter(
                ListingItem.id == item_b_id,
                ListingItem.is_archived == False
            ).first()

            if not item_a or not item_b:
                return False

            # Verify ownership
            if item_a.listing.user_id != user_a_id or item_b.listing.user_id != user_b_id:
                return False

            return True

        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid exchange_id format: {exchange_id}")
            return False

    def get_exchange_participants(self, exchange_id: str) -> List[int]:
        """
        Get list of participant user IDs for an exchange.

        Args:
            exchange_id: Exchange identifier

        Returns:
            List of user IDs who can participate in the chat
        """
        try:
            parts = exchange_id.split("_")
            if len(parts) >= 3:
                return [int(parts[1]), int(parts[2])]  # user_a_id, user_b_id
        except (ValueError, IndexError):
            pass
        return []

    def save_message(self, exchange_id: str, sender_id: int, message_text: str,
                    message_type: MessageType = MessageType.TEXT) -> Optional[ExchangeMessage]:
        """
        Save a chat message to database.

        Args:
            exchange_id: Exchange identifier
            sender_id: Sender user ID
            message_text: Message content
            message_type: Type of message

        Returns:
            Saved ExchangeMessage or None if failed
        """
        try:
            # Validate participant
            if not self.validate_exchange_participant(exchange_id, sender_id):
                logger.warning(f"Unauthorized message attempt: user {sender_id} for exchange {exchange_id}")
                return None

            # Create message with delivery timestamp
            from datetime import datetime
            message = ExchangeMessage(
                exchange_id=exchange_id,
                sender_id=sender_id,
                message_text=message_text,
                message_type=message_type,
                delivered_at=datetime.utcnow()  # Mark as delivered when saved
            )

            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)

            logger.info(f"Saved message {message.id} for exchange {exchange_id}")
            return message

        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            self.db.rollback()
            return None

    def get_chat_history(self, exchange_id: str, user_id: int, limit: int = 50,
                        offset: int = 0, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get chat history for an exchange.

        Args:
            exchange_id: Exchange identifier
            user_id: Requesting user (for authorization)
            limit: Max messages to return
            offset: Pagination offset
            use_cache: Whether to use Redis cache for recent messages

        Returns:
            List of message dictionaries
        """
        # Validate access
        if not self.validate_exchange_participant(exchange_id, user_id):
            return []

        # Try cache first for recent messages (offset=0 and reasonable limit)
        if use_cache and offset == 0 and limit <= 50:
            cached_messages = self.get_cached_messages(exchange_id)
            if cached_messages:
                # Mark messages as read for this user
                self.mark_exchange_read(exchange_id, user_id)
                return cached_messages

        try:
            messages = self.db.query(ExchangeMessage).filter(
                ExchangeMessage.exchange_id == exchange_id
            ).order_by(
                ExchangeMessage.created_at.desc()
            ).offset(offset).limit(limit).all()

            # Reverse to get chronological order
            messages.reverse()

            message_dicts = [msg.to_dict() for msg in messages]

            # Mark messages as read for this user
            self.mark_exchange_read(exchange_id, user_id)

            # Cache recent messages for fast recovery
            if offset == 0 and limit >= 20:  # Cache when getting recent messages
                self.cache_recent_messages(exchange_id, message_dicts)

            return message_dicts

        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return []

    def broadcast_message(self, exchange_id: str, message_data: Dict[str, Any]):
        """
        Broadcast message to all participants via Redis Pub/Sub.

        Args:
            exchange_id: Exchange identifier
            message_data: Message data to broadcast
        """
        if not self.redis_client:
            logger.warning("Redis not available for message broadcasting")
            return

        try:
            # Get participants
            participants = self.get_exchange_participants(exchange_id)

            # Publish to exchange channel
            channel = f"chat:{exchange_id}"
            message_json = json.dumps(message_data)

            self.redis_client.publish(channel, message_json)

            logger.debug(f"Broadcasted message to {len(participants)} participants on channel {channel}")

        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")

    def get_unread_count(self, user_id: int) -> Dict[str, int]:
        """
        Get unread message counts per exchange for user.

        Args:
            user_id: User ID

        Returns:
            Dict mapping exchange_id to unread count
        """
        try:
            # Get all exchanges where user is participant
            user_exchanges = self.db.execute("""
                SELECT DISTINCT em.exchange_id
                FROM exchange_messages em
                WHERE em.exchange_id LIKE :pattern
                  AND (split_part(em.exchange_id, '_', 2)::int = :user_id
                       OR split_part(em.exchange_id, '_', 3)::int = :user_id)
            """, {"pattern": f"mutual_%_{user_id}_%", "user_id": user_id}).fetchall()

            result = {}

            for (exchange_id,) in user_exchanges:
                # Count unread messages from other participants
                unread_count = self.db.query(ExchangeMessage).filter(
                    and_(
                        ExchangeMessage.exchange_id == exchange_id,
                        ExchangeMessage.sender_id != user_id,
                        ExchangeMessage.is_read == False
                    )
                ).count()

                if unread_count > 0:
                    result[exchange_id] = unread_count

            return result

        except Exception as e:
            logger.error(f"Failed to get unread counts: {e}")
            return {}

    def mark_exchange_read(self, exchange_id: str, user_id: int):
        """
        Mark all messages in exchange as read for user.

        Args:
            exchange_id: Exchange identifier
            user_id: User ID
        """
        if not self.validate_exchange_participant(exchange_id, user_id):
            return

        try:
            from datetime import datetime

            # Mark messages from others as read with timestamp
            updated = self.db.query(ExchangeMessage).filter(
                and_(
                    ExchangeMessage.exchange_id == exchange_id,
                    ExchangeMessage.sender_id != user_id,
                    ExchangeMessage.is_read == False
                )
            ).update({
                "is_read": True,
                "read_at": datetime.utcnow()
            })

            if updated > 0:
                self.db.commit()
                logger.info(f"Marked {updated} messages as read for user {user_id} in exchange {exchange_id}")

        except Exception as e:
            logger.error(f"Failed to mark exchange as read: {e}")
            self.db.rollback()

    def cache_recent_messages(self, exchange_id: str, messages: List[Dict[str, Any]]):
        """
        Cache recent messages in Redis for fast recovery.

        Args:
            exchange_id: Exchange identifier
            messages: List of message dictionaries
        """
        if not self.redis_client:
            return

        try:
            cache_key = f"chat_recent:{exchange_id}"
            # Keep last 50 messages for 24 hours
            cache_data = {
                "messages": messages[-50:],  # Last 50 messages
                "cached_at": datetime.utcnow().isoformat(),
                "exchange_id": exchange_id
            }

            self.redis_client.setex(
                cache_key,
                86400,  # 24 hours TTL
                json.dumps(cache_data)
            )

            logger.debug(f"Cached {len(messages)} recent messages for exchange {exchange_id}")

        except Exception as e:
            logger.error(f"Failed to cache messages: {e}")

    def get_cached_messages(self, exchange_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached recent messages from Redis.

        Args:
            exchange_id: Exchange identifier

        Returns:
            Cached messages or None if not available
        """
        if not self.redis_client:
            return None

        try:
            cache_key = f"chat_recent:{exchange_id}"
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Retrieved {len(data.get('messages', []))} cached messages for exchange {exchange_id}")
                return data.get("messages", [])

        except Exception as e:
            logger.error(f"Failed to get cached messages: {e}")

        return None


# Global service instance
_chat_service: Optional[ChatService] = None


def get_chat_service(db: Session = None) -> ChatService:
    """Get global chat service instance"""
    global _chat_service
    if _chat_service is None or db:
        _chat_service = ChatService(db)
    return _chat_service

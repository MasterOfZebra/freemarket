"""
Exchange history service for tracking exchange lifecycle events.

Provides audit trail and user exchange history management.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from .database import get_db
from .models import ExchangeHistory, ExchangeEventType, User, ListingItem

logger = logging.getLogger(__name__)


class ExchangeHistoryService:
    """
    Service for managing exchange history and lifecycle events.
    """

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    def log_event(
        self,
        exchange_id: str,
        event_type: ExchangeEventType,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[ExchangeHistory]:
        """
        Log an exchange lifecycle event.

        Args:
            exchange_id: Exchange identifier
            event_type: Type of event
            user_id: User who triggered the event (optional)
            details: Additional event details

        Returns:
            Created ExchangeHistory or None if failed
        """
        try:
            event = ExchangeHistory(
                exchange_id=exchange_id,
                event_type=event_type,
                user_id=user_id,
                details=details or {}
            )

            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)

            logger.info(f"Logged exchange event: {exchange_id} - {event_type.value}")

            return event

        except Exception as e:
            logger.error(f"Failed to log exchange event: {e}")
            self.db.rollback()
            return None

    def get_exchange_history(self, exchange_id: str) -> List[Dict[str, Any]]:
        """
        Get complete history of an exchange.

        Args:
            exchange_id: Exchange identifier

        Returns:
            List of history events
        """
        try:
            events = self.db.query(ExchangeHistory).filter(
                ExchangeHistory.exchange_id == exchange_id
            ).order_by(
                ExchangeHistory.created_at
            ).all()

            return [event.to_dict() for event in events]

        except Exception as e:
            logger.error(f"Failed to get exchange history: {e}")
            return []

    def get_user_exchange_history(
        self,
        user_id: int,
        status_filter: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get user's exchange history with filtering.

        Args:
            user_id: User ID
            status_filter: Filter by status (active, completed, cancelled)
            limit: Max exchanges to return
            offset: Pagination offset

        Returns:
            Dict with exchanges and metadata
        """
        try:
            # Get exchange IDs where user participated
            # Parse exchange_id format: mutual_X_Y_A_B
            user_exchanges_query = self.db.query(
                ExchangeHistory.exchange_id,
                func.max(ExchangeHistory.created_at).label('last_activity'),
                func.array_agg(ExchangeHistory.event_type.distinct()).label('event_types')
            ).filter(
                or_(
                    ExchangeHistory.exchange_id.like(f"mutual_{user_id}_%"),
                    ExchangeHistory.exchange_id.like(f"mutual_%_{user_id}_%")
                )
            ).group_by(ExchangeHistory.exchange_id)

            if status_filter:
                if status_filter == "active":
                    # Exchanges with created but not completed/cancelled
                    user_exchanges_query = user_exchanges_query.filter(
                        and_(
                            ~ExchangeHistory.event_type.in_([ExchangeEventType.COMPLETED, ExchangeEventType.CANCELLED])
                        )
                    )
                elif status_filter == "completed":
                    user_exchanges_query = user_exchanges_query.filter(
                        ExchangeHistory.event_type == ExchangeEventType.COMPLETED
                    )
                elif status_filter == "cancelled":
                    user_exchanges_query = user_exchanges_query.filter(
                        ExchangeHistory.event_type == ExchangeEventType.CANCELLED
                    )

            user_exchanges = user_exchanges_query.order_by(
                desc('last_activity')
            ).offset(offset).limit(limit).all()

            exchanges = []

            for exchange_id, last_activity, event_types in user_exchanges:
                # Get latest event for this exchange
                latest_event = self.db.query(ExchangeHistory).filter(
                    ExchangeHistory.exchange_id == exchange_id
                ).order_by(
                    desc(ExchangeHistory.created_at)
                ).first()

                # Get participants
                participants = self._get_exchange_participants(exchange_id)

                # Get status
                status = self._determine_exchange_status(event_types)

                # Get other participant info
                other_participant = None
                for pid in participants:
                    if pid != user_id:
                        other_user = self.db.query(User).filter(User.id == pid).first()
                        if other_user:
                            other_participant = {
                                "id": other_user.id,
                                "full_name": other_user.full_name,
                                "rating": self._get_user_rating_simple(pid)
                            }
                            break

                exchange_data = {
                    "exchange_id": exchange_id,
                    "status": status,
                    "participants": participants,
                    "other_participant": other_participant,
                    "last_activity": last_activity.isoformat() if last_activity else None,
                    "latest_event": latest_event.to_dict() if latest_event else None,
                    "event_types": [et.value for et in event_types] if event_types else []
                }

                exchanges.append(exchange_data)

            return {
                "user_id": user_id,
                "exchanges": exchanges,
                "total": len(exchanges),  # Simplified - would need proper count query
                "limit": limit,
                "offset": offset,
                "filter": status_filter
            }

        except Exception as e:
            logger.error(f"Failed to get user exchange history: {e}")
            return {
                "user_id": user_id,
                "exchanges": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "error": str(e)
            }

    def _get_exchange_participants(self, exchange_id: str) -> List[int]:
        """
        Extract participant IDs from exchange_id.

        Args:
            exchange_id: Format "mutual_X_Y_A_B"

        Returns:
            List of participant user IDs
        """
        try:
            parts = exchange_id.split("_")
            if len(parts) >= 4:
                return [int(parts[1]), int(parts[2])]  # user_a_id, user_b_id
        except (ValueError, IndexError):
            pass
        return []

    def _determine_exchange_status(self, event_types: List[ExchangeEventType]) -> str:
        """
        Determine exchange status from event types.

        Args:
            event_types: List of event types in this exchange

        Returns:
            Status string
        """
        if ExchangeEventType.CANCELLED in event_types:
            return "cancelled"
        elif ExchangeEventType.COMPLETED in event_types:
            return "completed"
        elif ExchangeEventType.CONFIRMED in event_types:
            return "confirmed"
        elif ExchangeEventType.CREATED in event_types:
            return "active"
        else:
            return "unknown"

    def _get_user_rating_simple(self, user_id: int) -> Dict[str, Any]:
        """
        Get simplified user rating for history display.

        Args:
            user_id: User ID

        Returns:
            Basic rating info
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    "avg": user.rating_avg or 0.0,
                    "count": user.rating_count or 0
                }
        except Exception as e:
            logger.warning(f"Failed to get user rating: {e}")

        return {"avg": 0.0, "count": 0}


# Global service instance
_exchange_history_service: Optional[ExchangeHistoryService] = None


def get_exchange_history_service(db: Session = None) -> ExchangeHistoryService:
    """Get global exchange history service instance"""
    global _exchange_history_service
    if _exchange_history_service is None or db:
        _exchange_history_service = ExchangeHistoryService(db)
    return _exchange_history_service

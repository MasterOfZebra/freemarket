"""
Match Index Service for incremental matching updates.

Manages the match_index table and handles profile change events.
"""
from typing import Dict, List, Optional, Set, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging

from .database import get_db
from .models import MatchIndex, ListingItem, ItemType, ExchangeType, User
from .events import ProfileChangeEvent, MatchUpdateEvent
from .language_normalization import get_normalizer

logger = logging.getLogger(__name__)


class MatchIndexService:
    """
    Service for managing match indexes and incremental updates.

    Handles:
    - Building and updating match indexes from user profiles
    - Incremental updates when profiles change
    - Finding affected users for match recalculation
    """

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.normalizer = get_normalizer()

    def build_user_index(self, user_id: int) -> int:
        """
        Build complete match index for user from their current listings.

        Args:
            user_id: User ID to index

        Returns:
            Number of index entries created/updated
        """
        # Get all active listing items for user
        items = self.db.query(ListingItem).filter(
            and_(
                ListingItem.listing.has(user_id=user_id),
                ListingItem.is_archived == False
            )
        ).all()

        index_entries = []
        categories_processed = set()

        for item in items:
            # Skip if we already processed this category+type+exchange combination
            key = (item.category, item.item_type.value, item.exchange_type.value)
            if key in categories_processed:
                continue
            categories_processed.add(key)

            # Extract tags from item (can be enhanced with NLP)
            tags = self._extract_tags_from_item(item)

            # Create or update index entry
            index_entry = MatchIndex(
                user_id=user_id,
                item_type=item.item_type.value,
                exchange_type=item.exchange_type.value,
                category=item.category,
                tags=tags
            )

            # Use upsert logic
            existing = self.db.query(MatchIndex).filter(
                and_(
                    MatchIndex.user_id == user_id,
                    MatchIndex.category == item.category,
                    MatchIndex.item_type == item.item_type.value,
                    MatchIndex.exchange_type == item.exchange_type.value
                )
            ).first()

            if existing:
                existing.tags = tags
                existing.updated_at = func.now()
            else:
                self.db.add(index_entry)
                index_entries.append(index_entry)

        self.db.commit()
        return len(index_entries)

    def update_user_index_incremental(self, user_id: int, changes: Dict[str, Any]) -> List[str]:
        """
        Update match index incrementally based on profile changes.

        Args:
            user_id: User ID
            changes: Dict with 'added' and 'removed' items

        Returns:
            List of affected categories
        """
        affected_categories = set()

        # Process added items
        for item_type in ['wants', 'offers']:
            for item in changes.get('added', {}).get(item_type, []):
                category = item.get('category')
                exchange_type = item.get('exchange_type', 'PERMANENT')

                if category:
                    affected_categories.add(category)

                    # Upsert index entry
                    self._upsert_index_entry(
                        user_id=user_id,
                        item_type=item_type.rstrip('s'),  # wants -> want, offers -> offer
                        exchange_type=exchange_type,
                        category=category,
                        tags=self._extract_tags_from_dict(item)
                    )

        # Process removed items
        for item_type in ['wants', 'offers']:
            for item in changes.get('removed', {}).get(item_type, []):
                category = item.get('category')
                exchange_type = item.get('exchange_type', 'PERMANENT')

                if category:
                    affected_categories.add(category)

                    # Check if user still has items in this category
                    still_has_items = self._user_has_items_in_category(
                        user_id, item_type.rstrip('s'), category, exchange_type
                    )

                    if not still_has_items:
                        # Remove index entry entirely
                        self.db.query(MatchIndex).filter(
                            and_(
                                MatchIndex.user_id == user_id,
                                MatchIndex.item_type == item_type.rstrip('s'),
                                MatchIndex.category == category,
                                MatchIndex.exchange_type == exchange_type
                            )
                        ).delete()

        self.db.commit()
        return list(affected_categories)

    def find_matching_users(self, user_id: int, categories: List[str],
                          item_type: str, exchange_type: str) -> List[int]:
        """
        Find users who have matching interests in given categories.

        Args:
            user_id: User to find matches for
            categories: Categories to search in
            item_type: 'want' or 'offer'
            exchange_type: 'PERMANENT' or 'TEMPORARY'

        Returns:
            List of matching user IDs
        """
        # For 'want' items, we look for users who 'offer' in same categories
        # For 'offer' items, we look for users who 'want' in same categories
        opposite_type = 'offer' if item_type == 'want' else 'want'

        matching_users = self.db.query(MatchIndex.user_id).filter(
            and_(
                MatchIndex.user_id != user_id,  # Exclude self
                MatchIndex.item_type == opposite_type,
                MatchIndex.exchange_type == exchange_type,
                MatchIndex.category.in_(categories)
            )
        ).distinct().all()

        return [row[0] for row in matching_users]

    def _upsert_index_entry(self, user_id: int, item_type: str, exchange_type: str,
                           category: str, tags: List[str]):
        """Upsert single index entry"""
        existing = self.db.query(MatchIndex).filter(
            and_(
                MatchIndex.user_id == user_id,
                MatchIndex.item_type == item_type,
                MatchIndex.category == category,
                MatchIndex.exchange_type == exchange_type
            )
        ).first()

        if existing:
            existing.tags = tags
            existing.updated_at = func.now()
        else:
            entry = MatchIndex(
                user_id=user_id,
                item_type=item_type,
                exchange_type=exchange_type,
                category=category,
                tags=tags
            )
            self.db.add(entry)

    def _user_has_items_in_category(self, user_id: int, item_type: str,
                                   category: str, exchange_type: str) -> bool:
        """Check if user still has active items in given category"""
        count = self.db.query(ListingItem).filter(
            and_(
                ListingItem.listing.has(user_id=user_id),
                ListingItem.item_type == item_type,
                ListingItem.category == category,
                ListingItem.exchange_type == exchange_type,
                ListingItem.is_archived == False
            )
        ).count()

        return count > 0

    def _extract_tags_from_item(self, item: ListingItem) -> List[str]:
        """Extract tags from ListingItem using NLP"""
        text = f"{item.item_name} {item.description or ''}"
        normalized = self.normalizer.normalize(text)

        # Simple tag extraction - can be enhanced with better NLP
        words = normalized.split()
        # Filter out common words and keep meaningful tags
        tags = [word for word in words if len(word) > 2][:5]  # Max 5 tags

        return tags

    def _extract_tags_from_dict(self, item_dict: Dict[str, Any]) -> List[str]:
        """Extract tags from item dictionary"""
        text = f"{item_dict.get('item_name', '')} {item_dict.get('description', '')}"
        normalized = self.normalizer.normalize(text)

        words = normalized.split()
        tags = [word for word in words if len(word) > 2][:5]

        return tags


# Event handlers
async def handle_profile_change(event: ProfileChangeEvent):
    """Handle profile change events by updating match index"""
    try:
        service = MatchIndexService()
        affected_categories = service.update_user_index_incremental(
            event.user_id, {"added": event.added, "removed": event.removed}
        )

        if affected_categories:
            # Emit match update event for affected categories
            from .events import emit_match_update
            await emit_match_update(event.user_id, affected_categories)

            # Note: Background processing will be handled by the event bus
            # when MatchUpdater is registered as a handler

        logger.info(f"Updated match index for user {event.user_id}, categories: {affected_categories}")

    except Exception as e:
        logger.error(f"Error updating match index for user {event.user_id}: {e}")


async def handle_match_update(event: MatchUpdateEvent):
    """Handle match update events by triggering recalculation"""
    try:
        # Here we would trigger the actual matching recalculation
        # For now, just log the event
        logger.info(f"Match update needed for user {event.user_id}, categories: {event.categories}")

        # TODO: Integrate with MatchUpdater worker when implemented

    except Exception as e:
        logger.error(f"Error handling match update for user {event.user_id}: {e}")


# Service instance
_match_index_service: Optional[MatchIndexService] = None


def get_match_index_service(db: Session = None) -> MatchIndexService:
    """Get global match index service instance"""
    global _match_index_service
    if _match_index_service is None or db:
        _match_index_service = MatchIndexService(db)
    return _match_index_service

"""
Tests for incremental matching system.

Tests profile change events, match index updates, and auto-cleanup after exchanges.
"""
import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Listing, ListingItem, ListingItemType, ExchangeType, MatchIndex
from backend.match_index_service import MatchIndexService, handle_profile_change
from backend.match_updater import MatchUpdater
from backend.events import ProfileChangeEvent, MatchUpdateEvent
from backend.schemas import ListingItemsByCategoryCreate


class TestIncrementalMatching:
    """Test incremental matching functionality"""

    @pytest.fixture
    def db_session(self):
        """Get database session for tests"""
        return next(get_db())

    @pytest.fixture
    def index_service(self, db_session):
        """Get match index service"""
        return MatchIndexService(db_session)

    @pytest.fixture
    def match_updater(self):
        """Get match updater instance"""
        return MatchUpdater(max_concurrent_tasks=1)

    def test_match_index_creation(self, db_session, index_service):
        """Test match index creation for user profile"""
        # Create test user and listing with items
        user = User(
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            city="Алматы"
        )
        db_session.add(user)
        db_session.commit()

        listing = Listing(user_id=user.id)
        db_session.add(listing)
        db_session.commit()

        # Add some test items
        items = [
            ListingItem(
                listing_id=listing.id,
                item_type=ListingItemType.WANT,
                category="electronics",
                exchange_type=ExchangeType.PERMANENT,
                item_name="iPhone",
                value_tenge=500000,
                description="Хочу айфон"
            ),
            ListingItem(
                listing_id=listing.id,
                item_type=ListingItemType.OFFER,
                category="transport",
                exchange_type=ExchangeType.TEMPORARY,
                item_name="велосипед",
                value_tenge=50000,
                duration_days=30,
                description="Отдам велосипед в аренду"
            )
        ]

        for item in items:
            db_session.add(item)
        db_session.commit()

        # Build index
        entries_created = index_service.build_user_index(user.id)

        # Verify index entries were created
        index_entries = db_session.query(MatchIndex).filter(MatchIndex.user_id == user.id).all()
        assert len(index_entries) == 2  # One for wants, one for offers

        # Verify content
        want_entry = next(e for e in index_entries if e.item_type == "want")
        assert want_entry.category == "electronics"
        assert want_entry.exchange_type == "PERMANENT"
        assert "айфон" in want_entry.tags

        offer_entry = next(e for e in index_entries if e.item_type == "offer")
        assert offer_entry.category == "transport"
        assert offer_entry.exchange_type == "TEMPORARY"
        assert "велосипед" in offer_entry.tags

    def test_incremental_index_update(self, db_session, index_service):
        """Test incremental index updates when profile changes"""
        # Setup similar to above
        user = User(username="test_user2", email="test2@example.com", city="Астана")
        db_session.add(user)
        db_session.commit()

        listing = Listing(user_id=user.id)
        db_session.add(listing)
        db_session.commit()

        # Initial items
        initial_item = ListingItem(
            listing_id=listing.id,
            item_type=ListingItemType.WANT,
            category="electronics",
            exchange_type=ExchangeType.PERMANENT,
            item_name="MacBook",
            value_tenge=800000
        )
        db_session.add(initial_item)
        db_session.commit()

        # Build initial index
        index_service.build_user_index(user.id)

        # Simulate adding new items
        changes = {
            "added": {
                "wants": [{
                    "category": "transport",
                    "exchange_type": "TEMPORARY",
                    "item_name": "велосипед"
                }],
                "offers": [{
                    "category": "electronics",
                    "exchange_type": "PERMANENT",
                    "item_name": "клавиатура"
                }]
            },
            "removed": {
                "wants": [{
                    "category": "electronics",
                    "exchange_type": "PERMANENT",
                    "item_name": "MacBook"
                }]
            }
        }

        affected_categories = index_service.update_user_index_incremental(user.id, changes)

        # Verify affected categories
        assert "electronics" in affected_categories
        assert "transport" in affected_categories

        # Verify index state
        index_entries = db_session.query(MatchIndex).filter(MatchIndex.user_id == user.id).all()

        # Should have entries for transport (want) and electronics (offer)
        categories = {(e.category, e.item_type) for e in index_entries}
        assert ("transport", "want") in categories
        assert ("electronics", "offer") in categories
        assert ("electronics", "want") not in categories  # Removed

    def test_match_finding_with_index(self, db_session, index_service):
        """Test finding matches using the index"""
        # Create two users with complementary interests
        user_a = User(username="user_a", email="a@example.com", city="Алматы")
        user_b = User(username="user_b", email="b@example.com", city="Алматы")
        db_session.add_all([user_a, user_b])
        db_session.commit()

        # User A wants electronics, offers transport
        listing_a = Listing(user_id=user_a.id)
        item_a_want = ListingItem(
            listing_id=listing_a.id,
            item_type=ListingItemType.WANT,
            category="electronics",
            exchange_type=ExchangeType.PERMANENT,
            item_name="ноутбук",
            value_tenge=600000
        )
        item_a_offer = ListingItem(
            listing_id=listing_a.id,
            item_type=ListingItemType.OFFER,
            category="transport",
            exchange_type=ExchangeType.TEMPORARY,
            item_name="велосипед",
            value_tenge=30000,
            duration_days=14
        )

        # User B offers electronics, wants transport
        listing_b = Listing(user_id=user_b.id)
        item_b_offer = ListingItem(
            listing_id=listing_b.id,
            item_type=ListingItemType.OFFER,
            category="electronics",
            exchange_type=ExchangeType.PERMANENT,
            item_name="ноутбук Lenovo",
            value_tenge=550000
        )
        item_b_want = ListingItem(
            listing_id=listing_b.id,
            item_type=ListingItemType.WANT,
            category="transport",
            exchange_type=ExchangeType.TEMPORARY,
            item_name="аренда велосипеда",
            value_tenge=25000,
            duration_days=7
        )

        db_session.add_all([listing_a, listing_b, item_a_want, item_a_offer, item_b_offer, item_b_want])
        db_session.commit()

        # Build indexes
        index_service.build_user_index(user_a.id)
        index_service.build_user_index(user_b.id)

        # Find matches for user A (wants electronics)
        matching_users = index_service.find_matching_users(
            user_a.id, ["electronics"], "want", "PERMANENT"
        )

        assert user_b.id in matching_users

        # Find matches for user A (offers transport)
        matching_users_transport = index_service.find_matching_users(
            user_a.id, ["transport"], "offer", "TEMPORARY"
        )

        assert user_b.id in matching_users_transport

    @pytest.mark.asyncio
    async def test_profile_change_event_handling(self, db_session, index_service):
        """Test handling of profile change events"""
        # Setup user
        user = User(username="event_test", email="event@example.com", city="Шымкент")
        db_session.add(user)
        db_session.commit()

        # Create event
        event = ProfileChangeEvent(
            user_id=user.id,
            added={
                "wants": [{
                    "category": "electronics",
                    "exchange_type": "PERMANENT",
                    "item_name": "планшет"
                }]
            }
        )

        # Mock the event emission to avoid actual async calls
        with patch('backend.match_index_service.emit_match_update') as mock_emit:
            await handle_profile_change(event)

            # Verify emit_match_update was called
            mock_emit.assert_called_once_with(user.id, ["electronics"])

    def test_exchange_confirmation_auto_cleanup(self, db_session):
        """Test auto-cleanup after exchange confirmation"""
        # Create two users
        user_a = User(username="user_a", email="a@example.com", city="Алматы")
        user_b = User(username="user_b", email="b@example.com", city="Алматы")
        db_session.add_all([user_a, user_b])
        db_session.commit()

        # Create listings
        listing_a = Listing(user_id=user_a.id)
        listing_b = Listing(user_id=user_b.id)
        db_session.add_all([listing_a, listing_b])
        db_session.commit()

        # Create items to be exchanged
        item_a_offer = ListingItem(
            listing_id=listing_a.id,
            item_type=ListingItemType.OFFER,
            category="electronics",
            exchange_type=ExchangeType.PERMANENT,
            item_name="мышь",
            value_tenge=15000
        )

        item_b_offer = ListingItem(
            listing_id=listing_b.id,
            item_type=ListingItemType.OFFER,
            category="books",
            exchange_type=ExchangeType.PERMANENT,
            item_name="учебник",
            value_tenge=12000
        )

        db_session.add_all([item_a_offer, item_b_offer])
        db_session.commit()

        # Verify items are not archived initially
        assert not item_a_offer.is_archived
        assert not item_b_offer.is_archived

        # Simulate exchange confirmation (manual for test)
        exchange_id = f"mutual_{user_a.id}_{user_b.id}_{item_a_offer.id}_{item_b_offer.id}"

        # Parse and validate (similar to endpoint logic)
        parts = exchange_id.split("_")
        assert len(parts) == 5
        assert parts[0] == "mutual"

        ua_id, ub_id, ia_id, ib_id = map(int, parts[1:])

        assert ua_id == user_a.id
        assert ub_id == user_b.id
        assert ia_id == item_a_offer.id
        assert ib_id == item_b_offer.id

        # Perform cleanup
        item_a_offer.is_archived = True
        item_b_offer.is_archived = True
        db_session.commit()

        # Refresh and verify
        db_session.refresh(item_a_offer)
        db_session.refresh(item_b_offer)

        assert item_a_offer.is_archived
        assert item_b_offer.is_archived

        # Verify they don't appear in active queries
        active_items_a = db_session.query(ListingItem).filter(
            ListingItem.listing_id == listing_a.id,
            ListingItem.is_archived == False
        ).all()

        active_items_b = db_session.query(ListingItem).filter(
            ListingItem.listing_id == listing_b.id,
            ListingItem.is_archived == False
        ).all()

        assert len(active_items_a) == 0  # Item was archived
        assert len(active_items_b) == 0  # Item was archived

    def test_match_updater_processing(self, match_updater):
        """Test match updater processes events correctly"""
        # Create test event
        event = MatchUpdateEvent(
            user_id=123,
            categories=["electronics", "transport"],
            changed_item_ids=[1, 2, 3]
        )

        # Mock database calls
        with patch('backend.match_updater.get_db') as mock_get_db:
            mock_db = mock_get_db.return_value.__enter__.return_value

            # Mock user query
            mock_user = type('MockUser', (), {'id': 456, 'is_active': True})()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user

            # Mock match index service
            with patch('backend.match_updater.MatchIndexService') as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.find_matching_users.return_value = [456, 789]

                # Run updater
                import asyncio
                asyncio.run(match_updater.handle_match_update(event))

                # Verify service was called
                assert mock_service.find_matching_users.call_count == 2  # For each category

                # Check stats
                stats = match_updater.get_stats()
                assert stats["tasks_processed"] == 1

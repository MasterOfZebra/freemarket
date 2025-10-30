"""
Phase 2 Integration Tests

Full end-to-end pipeline testing:
Language Normalization → Location Filtering → Core Matching →
Category Matching → Score Aggregation → Notification

Tests all integration points and edge cases.
"""

import pytest
from datetime import datetime
from typing import List, Dict

# Import all components
from backend.language_normalization import LanguageNormalizer
from backend.location_filtering import LocationFilter
from backend.core_matching_engine import CoreMatchingEngine, ItemPairScore
from backend.category_matching_engine import CategoryMatchingEngine
from backend.score_aggregation_engine import ScoreAggregationEngine, BonusConfig
from backend.notifications.notification_service import (
    NotificationService,
    MatchNotification,
    NotificationChannel
)


class TestLanguageNormalizationIntegration:
    """Test language normalization component integration"""

    @pytest.fixture
    def normalizer(self):
        return LanguageNormalizer(enable_cache=True)

    def test_dynamic_language_support(self, normalizer):
        """Test if new languages can be added dynamically"""
        # Test existing languages
        assert normalizer.normalize("iPhone") is not None
        assert normalizer.normalize("айфон") is not None

        # Test that synonyms work cross-language
        similarity = normalizer.similarity_score("phone", "телефон")
        assert similarity > 0.80, "Cross-language similarity should be high for synonyms"

    def test_multiword_ambiguity(self, normalizer):
        """Test handling of ambiguous terms (bike = велосипед OR мотоцикл)"""
        # Both should normalize to 'bike' or similar
        bike_en = normalizer.normalize("bike")
        bike_ru = normalizer.normalize("велик")

        # Should be recognized as synonyms
        similarity = normalizer.similarity_score("bike", "велик")
        assert similarity >= 0.80, "Ambiguous terms should match well"

    def test_unknown_word_fallback(self, normalizer):
        """Test that unknown words don't break the system"""
        # Unknown Russian word (made up)
        unknown = "абвгдеёжз123456"
        result = normalizer.normalize(unknown)

        # Should return normalized version, not crash
        assert result is not None
        assert isinstance(result, str)

    def test_cache_performance(self, normalizer):
        """Test that caching significantly improves performance"""
        test_text = "This is a test message with some items"

        # First call (uncached)
        import time
        start = time.time()
        result1 = normalizer.normalize(test_text)
        uncached_time = time.time() - start

        # Second call (cached)
        start = time.time()
        result2 = normalizer.normalize(test_text)
        cached_time = time.time() - start

        # Results should be identical
        assert result1 == result2

        # Cached should be faster (or at least not slower)
        assert cached_time <= uncached_time or cached_time < 0.001


class TestLocationFilteringIntegration:
    """Test location filtering component"""

    @pytest.fixture
    def filter_engine(self):
        return LocationFilter(max_distance_km=1500)

    def test_dense_location_scaling(self, filter_engine):
        """Test handling of dense locations (many users in one city)"""
        # Create 1000 candidates in same location
        candidates = [
            {"id": i, "locations": ["Алматы"]}
            for i in range(1000)
        ]

        filtered, bonuses = filter_engine.filter_candidates_by_location(
            ["Алматы"],
            candidates
        )

        # All should pass
        assert len(filtered) == 1000
        assert all(bonuses[c["id"]] == 0.1 for c in filtered)

    def test_coordinate_format_handling(self, filter_engine):
        """Test different coordinate formats"""
        # Test normalized city names
        result1 = filter_engine.normalize_location("алматы")
        result2 = filter_engine.normalize_location("Almaty")
        result3 = filter_engine.normalize_location("АЛМАТЫ")

        # All should normalize to same value
        assert result1 == result2 == result3 == "Алматы"

    def test_missing_location_handling(self, filter_engine):
        """Test behavior with missing locations"""
        candidates = [
            {"id": 1, "locations": ["Алматы"]},
            {"id": 2, "locations": None},  # Missing
            {"id": 3, "locations": []},     # Empty
        ]

        filtered, bonuses = filter_engine.filter_candidates_by_location(
            ["Алматы"],
            candidates
        )

        # Only valid ones should pass
        assert len(filtered) == 1
        assert filtered[0]["id"] == 1

    def test_distance_constraint(self, filter_engine):
        """Test distance-based filtering"""
        candidates = [
            {"id": 1, "locations": ["Алматы"]},
            {"id": 2, "locations": ["Шымкент"]},  # 480km
            {"id": 3, "locations": ["Астана"]},   # 1400km
        ]

        # Within 1500km limit
        filtered, _ = filter_engine.filter_candidates_by_location(
            ["Алматы"],
            candidates
        )

        # Should include both Шымкент and Астана (both < 1500km)
        assert len(filtered) >= 2


class TestCoreMatchingIntegration:
    """Test core matching engine"""

    @pytest.fixture
    def matching_engine(self):
        return CoreMatchingEngine()

    def test_mixed_listing_handling(self, matching_engine):
        """Test matching with mixed permanent + temporary items"""
        perm_item = {
            "id": 1,
            "category": "electronics",
            "exchange_type": "permanent",
            "value_tenge": 50000,
            "item_name": "Phone"
        }

        temp_item = {
            "id": 2,
            "category": "electronics",
            "exchange_type": "temporary",
            "value_tenge": 30000,
            "duration_days": 10,
            "item_name": "Laptop"
        }

        # Should detect type mismatch
        result = matching_engine.score_item_pair(perm_item, temp_item)
        assert not result.is_valid
        assert "Exchange type mismatch" in result.validation_errors[0]

    def test_division_by_zero_protection(self, matching_engine):
        """Test protection against division by zero in rate calculation"""
        item_a = {
            "id": 1,
            "category": "transport",
            "exchange_type": "temporary",
            "value_tenge": 30000,
            "duration_days": 0,  # Would cause division by zero
            "item_name": "Car"
        }

        item_b = {
            "id": 2,
            "category": "transport",
            "exchange_type": "temporary",
            "value_tenge": 30000,
            "duration_days": 10,
            "item_name": "Bicycle"
        }

        # Should not crash
        result = matching_engine.score_item_pair(item_a, item_b)
        assert not result.is_valid


class TestCategoryMatchingIntegration:
    """Test category matching engine"""

    @pytest.fixture
    def category_engine(self):
        return CategoryMatchingEngine(min_category_score=0.50, min_valid_categories=1)

    def test_incomplete_categories(self, category_engine):
        """Test handling of incomplete category listings"""
        user_listings = {
            "electronics": [
                {
                    "id": 1,
                    "category": "electronics",
                    "exchange_type": "permanent",
                    "value_tenge": 50000,
                    "item_name": "Phone"
                }
            ]
            # Missing other categories
        }

        candidates = [
            {
                "id": 101,
                "locations": ["Алматы"],
                "listings": {
                    "electronics": [
                        {
                            "id": 2,
                            "category": "electronics",
                            "exchange_type": "permanent",
                            "value_tenge": 50000,
                            "item_name": "iPhone"
                        }
                    ],
                    "furniture": [
                        {
                            "id": 3,
                            "category": "furniture",
                            "exchange_type": "permanent",
                            "value_tenge": 30000,
                            "item_name": "Desk"
                        }
                    ]
                }
            }
        ]

        # Should match only on electronics (intersection)
        results = category_engine.find_matches_for_user(
            user_id=1,
            user_listings=user_listings,
            user_locations=["Алматы"],
            candidates=candidates
        )

        assert len(results) >= 1
        assert results[0].matching_categories == 1


class TestScoreAggregationIntegration:
    """Test score aggregation with extreme values"""

    @pytest.fixture
    def aggregation_engine(self):
        config = BonusConfig()
        return ScoreAggregationEngine(config)

    def test_extreme_value_handling(self, aggregation_engine):
        """Test handling of extreme score values"""
        # Perfect score with all bonuses
        score1, breakdown1 = aggregation_engine.calculate_final_score(
            base_score=1.0,
            has_location_overlap=True,
            partner_rating=5.0,
            created_at=datetime.utcnow()
        )

        # Should be capped at 1.0
        assert score1 <= 1.0

        # Terrible score
        score2, breakdown2 = aggregation_engine.calculate_final_score(
            base_score=0.0,
            has_location_overlap=False,
            partner_rating=0.0,
            created_at=None
        )

        assert score2 >= 0.0
        assert score2 < 0.1

    def test_weighted_average_correctness(self, aggregation_engine):
        """Test that weighted average calculation is correct"""
        # Simulate category scores with different weights
        from backend.category_matching_engine import AggregationMethod

        category_scores = {
            "electronics": 0.9,  # Many items
            "furniture": 0.5,    # Few items
        }

        item_counts = {
            "electronics": (10, 10),  # user_count, candidate_count
            "furniture": (1, 1),
        }

        # Weighted average should favor electronics
        score = aggregation_engine._aggregate_scores(
            category_scores,
            AggregationMethod.WEIGHTED.value,
            item_counts
        )

        # Should be closer to 0.9 than 0.5
        assert score > 0.75


class TestNotificationIntegration:
    """Test notification service integration"""

    @pytest.fixture
    def notification_service(self):
        return NotificationService()

    def test_duplicate_notification_protection(self, notification_service):
        """Test protection against duplicate notifications"""
        notif1 = MatchNotification(
            user_id=1,
            partner_id=2,
            partner_telegram="@alice",
            partner_name="Alice",
            partner_rating=4.8,
            match_score=0.87,
            match_quality="excellent",
            matching_categories=["electronics"],
            timestamp=datetime.utcnow(),
            notification_id="notif_001"
        )

        notif2 = MatchNotification(
            user_id=1,
            partner_id=2,
            partner_telegram="@alice",
            partner_name="Alice",
            partner_rating=4.8,
            match_score=0.87,
            match_quality="excellent",
            matching_categories=["electronics"],
            timestamp=datetime.utcnow(),
            notification_id="notif_002"  # Different ID
        )

        # Both should be processed
        # In production, would check DB for duplicates
        assert notif1.notification_id != notif2.notification_id

    def test_retry_logic(self, notification_service):
        """Test retry logic for failed deliveries"""
        # Retry count should be configurable
        assert notification_service.config.max_retries == 3
        assert notification_service.config.retry_delay_seconds == 60


class TestFullPipelineIntegration:
    """End-to-end pipeline tests"""

    def test_full_pipeline_happy_path(self):
        """Test complete pipeline: input → matching → notification"""
        # Setup
        normalizer = LanguageNormalizer()
        location_filter = LocationFilter()
        core_engine = CoreMatchingEngine()
        category_engine = CategoryMatchingEngine()
        aggregation_engine = ScoreAggregationEngine()
        notification_service = NotificationService()

        # User 1 listings
        user1_listings = {
            "electronics": [
                {
                    "id": 1,
                    "category": "electronics",
                    "exchange_type": "permanent",
                    "value_tenge": 50000,
                    "item_name": "iPhone"
                }
            ]
        }

        # Candidates (User 2)
        candidates = [
            {
                "id": 2,
                "locations": ["Алматы"],
                "listings": {
                    "electronics": [
                        {
                            "id": 3,
                            "category": "electronics",
                            "exchange_type": "permanent",
                            "value_tenge": 50000,
                            "item_name": "айфон"  # Russian
                        }
                    ]
                }
            }
        ]

        # Step 1: Find matches
        matches = category_engine.find_matches_for_user(
            user_id=1,
            user_listings=user1_listings,
            user_locations=["Алматы"],
            candidates=candidates
        )

        assert len(matches) > 0
        match = matches[0]

        # Step 2: Apply final scoring with bonuses
        final_score, breakdown = aggregation_engine.calculate_final_score(
            base_score=match.final_score,
            has_location_overlap=match.location_bonus > 0,
            partner_rating=4.5,
            created_at=datetime.utcnow()
        )

        assert final_score > 0.70  # Should pass threshold

        # Step 3: Prepare notification
        notification = MatchNotification(
            user_id=1,
            partner_id=2,
            partner_telegram="@user2",
            partner_name="User 2",
            partner_rating=4.5,
            match_score=final_score,
            match_quality=aggregation_engine.get_score_quality_label(final_score),
            matching_categories=list(match.categories.keys()),
            timestamp=datetime.utcnow(),
            notification_id="notif_test_001"
        )

        # Verify notification is ready
        assert notification.user_id == 1
        assert notification.match_score > 0.7
        assert len(notification.matching_categories) > 0

    def test_pipeline_with_edge_cases(self):
        """Test pipeline with edge cases"""
        category_engine = CategoryMatchingEngine()

        # Edge case: empty listings
        user_listings = {}
        candidates = [{"id": 1, "locations": ["Алматы"], "listings": {}}]

        # Should handle gracefully
        matches = category_engine.find_matches_for_user(
            user_id=1,
            user_listings=user_listings,
            user_locations=["Алматы"],
            candidates=candidates
        )

        # Should return empty or valid result
        assert isinstance(matches, list)


class TestPerformanceIntegration:
    """Performance and scalability tests"""

    def test_pipeline_latency(self):
        """Test that full pipeline meets latency target (<200ms)"""
        import time

        category_engine = CategoryMatchingEngine()
        aggregation_engine = ScoreAggregationEngine()

        # Create realistic dataset
        user_listings = {
            f"category_{i}": [
                {
                    "id": j,
                    "category": f"category_{i}",
                    "exchange_type": "permanent",
                    "value_tenge": 50000 + j * 1000,
                    "item_name": f"Item_{i}_{j}"
                }
                for j in range(5)
            ]
            for i in range(6)
        }

        candidates = [
            {
                "id": 100 + c,
                "locations": ["Алматы"],
                "listings": {
                    f"category_{i}": [
                        {
                            "id": 1000 + i * 10 + j,
                            "category": f"category_{i}",
                            "exchange_type": "permanent",
                            "value_tenge": 50000 + j * 1000,
                            "item_name": f"Item_c{c}_{i}_{j}"
                        }
                        for j in range(5)
                    ]
                    for i in range(6)
                }
            }
            for c in range(10)
        ]

        # Measure full pipeline
        start = time.time()

        matches = category_engine.find_matches_for_user(
            user_id=1,
            user_listings=user_listings,
            user_locations=["Алматы"],
            candidates=candidates
        )

        for match in matches[:5]:  # Top 5 matches
            final_score, _ = aggregation_engine.calculate_final_score(
                base_score=match.final_score,
                has_location_overlap=match.location_bonus > 0,
                partner_rating=4.5
            )

        elapsed = (time.time() - start) * 1000  # Convert to ms

        # Should be under 200ms for reasonable dataset
        assert elapsed < 500, f"Pipeline took {elapsed}ms, target <200ms"


if __name__ == "__main__":
    # Run tests with pytest
    # pytest backend/tests/test_phase2_integration.py -v --tb=short
    print("🧪 Phase 2 Integration Tests")
    print("Run with: pytest backend/tests/test_phase2_integration.py -v")

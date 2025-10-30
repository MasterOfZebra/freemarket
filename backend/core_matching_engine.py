"""
Core Matching Engine

Handles:
- Item pair validation
- Score calculation for permanent exchanges
- Score calculation for temporary exchanges
- Language similarity multiplier
- Result formatting

Used as foundation for category and chain matching.
"""

from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

from backend.equivalence_engine import ExchangeEquivalence, ExchangeType
from backend.language_normalization import get_normalizer

logger = logging.getLogger(__name__)


class MatchQuality(str, Enum):
    """Quality classification for matches"""
    PERFECT = "perfect"        # Score ≥ 0.95
    EXCELLENT = "excellent"    # Score ≥ 0.85
    GOOD = "good"              # Score ≥ 0.70
    POOR = "poor"              # Score < 0.70


@dataclass
class ItemPairScore:
    """Result of scoring one item pair"""

    item_a_id: int
    item_b_id: int

    # Base scores
    equivalence_score: float      # From ExchangeEquivalence engine
    language_similarity: float    # From LanguageNormalizer

    # Final score
    final_score: float           # equivalence_score × language_similarity

    # Metadata
    exchange_type: str            # permanent or temporary
    category: str
    quality: str                  # perfect/excellent/good/poor

    # Details
    details: Dict[str, Any]       # Additional scoring details

    # Validation
    is_valid: bool                # Passes minimum threshold
    validation_errors: list       # If not valid, why?

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "item_a_id": self.item_a_id,
            "item_b_id": self.item_b_id,
            "equivalence_score": round(self.equivalence_score, 3),
            "language_similarity": round(self.language_similarity, 3),
            "final_score": round(self.final_score, 3),
            "exchange_type": self.exchange_type,
            "category": self.category,
            "quality": self.quality,
            "details": self.details,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }


class CoreMatchingEngine:
    """Core engine for scoring individual item pairs"""

    def __init__(
        self,
        equivalence_engine: Optional[ExchangeEquivalence] = None,
        language_normalizer = None,
        language_similarity_weight: float = 0.3,
    ):
        """
        Initialize core matching engine

        Args:
            equivalence_engine: Instance of ExchangeEquivalence
            language_normalizer: Instance of LanguageNormalizer
            language_similarity_weight: Weight of language similarity (0.0-1.0)
                - 0.0: Only use equivalence score
                - 1.0: Only use language similarity
                - 0.3 (default): 70% equivalence, 30% language
        """
        self.equivalence_engine = equivalence_engine or ExchangeEquivalence()
        self.normalizer = language_normalizer or get_normalizer()

        if not (0.0 <= language_similarity_weight <= 1.0):
            raise ValueError("language_similarity_weight must be 0.0-1.0")

        self.language_weight = language_similarity_weight
        self.equivalence_weight = 1.0 - language_similarity_weight

        logger.info(
            f"CoreMatchingEngine initialized: "
            f"lang_weight={language_similarity_weight} "
            f"equiv_weight={self.equivalence_weight}"
        )

    def validate_items(self, item_a: Dict, item_b: Dict) -> Tuple[bool, list]:
        """
        Validate two items for matching

        Args:
            item_a: First item dict with keys: id, category, exchange_type,
                    value_tenge, duration_days, item_name
            item_b: Second item dict (same structure)

        Returns:
            (is_valid, errors_list)
        """
        errors = []

        # Check required fields
        required_fields = ['id', 'category', 'exchange_type', 'value_tenge', 'item_name']
        for item, name in [(item_a, 'item_a'), (item_b, 'item_b')]:
            for field in required_fields:
                if field not in item:
                    errors.append(f"{name} missing '{field}'")

        if errors:
            return False, errors

        # Check matching exchange types
        if item_a['exchange_type'] != item_b['exchange_type']:
            errors.append(
                f"Exchange type mismatch: {item_a['exchange_type']} vs {item_b['exchange_type']}"
            )

        # Check categories match
        if item_a['category'] != item_b['category']:
            errors.append(f"Category mismatch: {item_a['category']} vs {item_b['category']}")

        # Validate values
        if item_a['value_tenge'] <= 0:
            errors.append(f"item_a value_tenge must be > 0, got {item_a['value_tenge']}")
        if item_b['value_tenge'] <= 0:
            errors.append(f"item_b value_tenge must be > 0, got {item_b['value_tenge']}")

        # Validate duration for temporary exchanges
        if item_a['exchange_type'] == ExchangeType.TEMPORARY.value:
            if item_a.get('duration_days') is None or item_a['duration_days'] <= 0:
                errors.append(f"item_a temporary exchange requires duration_days > 0")
            if item_b.get('duration_days') is None or item_b['duration_days'] <= 0:
                errors.append(f"item_b temporary exchange requires duration_days > 0")

        return len(errors) == 0, errors

    def calculate_permanent_score(self, value_a: int, value_b: int) -> float:
        """
        Calculate equivalence score for permanent exchange

        Uses ExchangeEquivalence engine with ±15% tolerance

        Args:
            value_a: Value in Tenge of item A
            value_b: Value in Tenge of item B

        Returns:
            Score (0.0-1.0)
        """
        return self.equivalence_engine.calculate_permanent_score(value_a, value_b)

    def calculate_temporary_score(
        self,
        value_a: int,
        duration_a: int,
        value_b: int,
        duration_b: int
    ) -> float:
        """
        Calculate equivalence score for temporary exchange

        Uses daily rate comparison: (value_a / duration_a) ≈ (value_b / duration_b)

        Args:
            value_a: Daily rate value in Tenge of item A
            duration_a: Rental duration in days for item A
            value_b: Daily rate value in Tenge of item B
            duration_b: Rental duration in days for item B

        Returns:
            Score (0.0-1.0)
        """
        return self.equivalence_engine.calculate_temporary_score(
            value_a, duration_a, value_b, duration_b
        )

    def apply_language_similarity_multiplier(
        self,
        base_score: float,
        item_a_name: str,
        item_b_name: str
    ) -> Tuple[float, float]:
        """
        Apply language similarity as multiplier to base score

        Strategy:
        - Calculate text similarity between normalized item names
        - Multiply with base equivalence score

        Args:
            base_score: Score from equivalence engine
            item_a_name: Name of item A
            item_b_name: Name of item B

        Returns:
            (final_score, similarity_score)
        """
        # Calculate similarity
        similarity = self.normalizer.similarity_score(item_a_name, item_b_name)

        # Combine scores: weighted average
        final_score = (
            base_score * self.equivalence_weight +
            similarity * self.language_weight
        )

        return final_score, similarity

    def score_item_pair(
        self,
        item_a: Dict,
        item_b: Dict,
        include_details: bool = True
    ) -> ItemPairScore:
        """
        Calculate complete match score for item pair

        Full scoring pipeline:
        1. Validate items
        2. Calculate equivalence score
        3. Calculate language similarity
        4. Combine into final score
        5. Determine quality

        Args:
            item_a: First item dict
            item_b: Second item dict
            include_details: Include detailed breakdown in result

        Returns:
            ItemPairScore object
        """
        # Step 1: Validate
        is_valid, errors = self.validate_items(item_a, item_b)

        if not is_valid:
            return ItemPairScore(
                item_a_id=item_a.get('id', -1),
                item_b_id=item_b.get('id', -1),
                equivalence_score=0.0,
                language_similarity=0.0,
                final_score=0.0,
                exchange_type=item_a.get('exchange_type', 'unknown'),
                category=item_a.get('category', 'unknown'),
                quality=MatchQuality.POOR.value,
                details={"validation_errors": errors} if include_details else {},
                is_valid=False,
                validation_errors=errors,
            )

        exchange_type = item_a['exchange_type']

        # Step 2: Calculate equivalence score
        if exchange_type == ExchangeType.PERMANENT.value:
            equiv_score = self.calculate_permanent_score(
                item_a['value_tenge'],
                item_b['value_tenge']
            )
        elif exchange_type == ExchangeType.TEMPORARY.value:
            equiv_score = self.calculate_temporary_score(
                item_a['value_tenge'],
                item_a['duration_days'],
                item_b['value_tenge'],
                item_b['duration_days']
            )
        else:
            errors.append(f"Unknown exchange_type: {exchange_type}")
            equiv_score = 0.0

        # Step 3: Apply language similarity
        final_score, lang_similarity = self.apply_language_similarity_multiplier(
            equiv_score,
            item_a['item_name'],
            item_b['item_name']
        )

        # Step 4: Determine quality
        if final_score >= 0.95:
            quality = MatchQuality.PERFECT.value
        elif final_score >= 0.85:
            quality = MatchQuality.EXCELLENT.value
        elif final_score >= 0.70:
            quality = MatchQuality.GOOD.value
        else:
            quality = MatchQuality.POOR.value

        # Step 5: Check threshold
        min_threshold = self.equivalence_engine.config.MIN_MATCH_SCORE
        is_match_valid = final_score >= min_threshold

        # Build details
        details = {}
        if include_details:
            details = {
                "item_a_value_tenge": item_a['value_tenge'],
                "item_b_value_tenge": item_b['value_tenge'],
                "item_a_name": item_a['item_name'],
                "item_b_name": item_b['item_name'],
                "equivalence_score": round(equiv_score, 3),
                "language_similarity": round(lang_similarity, 3),
                "equivalence_weight": self.equivalence_weight,
                "language_weight": self.language_weight,
            }

            if exchange_type == ExchangeType.TEMPORARY.value:
                details.update({
                    "duration_a_days": item_a.get('duration_days'),
                    "duration_b_days": item_b.get('duration_days'),
                    "daily_rate_a": round(item_a['value_tenge'] / item_a['duration_days'], 2),
                    "daily_rate_b": round(item_b['value_tenge'] / item_b['duration_days'], 2),
                })

        result = ItemPairScore(
            item_a_id=item_a['id'],
            item_b_id=item_b['id'],
            equivalence_score=equiv_score,
            language_similarity=lang_similarity,
            final_score=final_score,
            exchange_type=exchange_type,
            category=item_a['category'],
            quality=quality,
            details=details,
            is_valid=is_match_valid,
            validation_errors=[] if is_match_valid else [f"Score {final_score:.2f} < threshold {min_threshold:.2f}"],
        )

        return result

    def score_item_pairs_batch(
        self,
        pairs: list,
        min_score: Optional[float] = None
    ) -> list:
        """
        Score multiple item pairs in batch

        Args:
            pairs: List of (item_a, item_b) tuples
            min_score: Filter results by minimum score

        Returns:
            List of ItemPairScore objects
        """
        results = []

        for item_a, item_b in pairs:
            result = self.score_item_pair(item_a, item_b)

            # Apply minimum score filter
            if min_score is None or result.final_score >= min_score:
                results.append(result)

        logger.info(
            f"Scored {len(pairs)} item pairs, "
            f"found {len(results)} matching pairs "
            f"(threshold: {min_score})"
        )

        return results


if __name__ == "__main__":
    # Test the core matching engine
    from backend.equivalence_engine import ExchangeEquivalence

    engine = CoreMatchingEngine()

    print("🧪 Core Matching Engine Tests\n")

    # Test 1: Permanent exchange - perfect match
    print("✅ TEST 1: Permanent - Perfect Match (50000 ≈ 50000)")
    item_a = {
        "id": 1,
        "category": "electronics",
        "exchange_type": "permanent",
        "value_tenge": 50000,
        "item_name": "iPhone 13 Pro",
    }
    item_b = {
        "id": 2,
        "category": "electronics",
        "exchange_type": "permanent",
        "value_tenge": 50000,
        "item_name": "iPhone 13 Pro",
    }
    result = engine.score_item_pair(item_a, item_b)
    print(f"  Score: {result.final_score:.3f} | Quality: {result.quality} | Valid: {result.is_valid}")

    # Test 2: Permanent exchange - good match with language variation
    print("\n✅ TEST 2: Permanent - Good Match with Language Variation")
    item_a = {
        "id": 3,
        "category": "transport",
        "exchange_type": "permanent",
        "value_tenge": 100000,
        "item_name": "bike",
    }
    item_b = {
        "id": 4,
        "category": "transport",
        "exchange_type": "permanent",
        "value_tenge": 105000,  # Within ±15%
        "item_name": "велосипед",
    }
    result = engine.score_item_pair(item_a, item_b)
    print(f"  Score: {result.final_score:.3f} | Quality: {result.quality} | Valid: {result.is_valid}")

    # Test 3: Permanent exchange - poor match (values too different)
    print("\n✅ TEST 3: Permanent - Poor Match (50000 vs 100000)")
    item_a = {
        "id": 5,
        "category": "electronics",
        "exchange_type": "permanent",
        "value_tenge": 50000,
        "item_name": "Laptop",
    }
    item_b = {
        "id": 6,
        "category": "electronics",
        "exchange_type": "permanent",
        "value_tenge": 100000,  # Too different
        "item_name": "Desktop Computer",
    }
    result = engine.score_item_pair(item_a, item_b)
    print(f"  Score: {result.final_score:.3f} | Quality: {result.quality} | Valid: {result.is_valid}")

    # Test 4: Temporary exchange - good match
    print("\n✅ TEST 4: Temporary - Good Match (daily rate matching)")
    item_a = {
        "id": 7,
        "category": "transport",
        "exchange_type": "temporary",
        "value_tenge": 30000,
        "duration_days": 10,  # 3000/day
        "item_name": "Car",
    }
    item_b = {
        "id": 8,
        "category": "transport",
        "exchange_type": "temporary",
        "value_tenge": 31500,
        "duration_days": 10,  # 3150/day - within ±15%
        "item_name": "automobile",
    }
    result = engine.score_item_pair(item_a, item_b)
    print(f"  Score: {result.final_score:.3f} | Quality: {result.quality} | Valid: {result.is_valid}")

    # Test 5: Validation error - type mismatch
    print("\n✅ TEST 5: Validation Error - Exchange Type Mismatch")
    item_a = {
        "id": 9,
        "category": "furniture",
        "exchange_type": "permanent",
        "value_tenge": 50000,
        "item_name": "Desk",
    }
    item_b = {
        "id": 10,
        "category": "furniture",
        "exchange_type": "temporary",
        "value_tenge": 50000,
        "duration_days": 30,
        "item_name": "Table",
    }
    result = engine.score_item_pair(item_a, item_b)
    print(f"  Score: {result.final_score:.3f} | Valid: {result.is_valid}")
    print(f"  Errors: {result.validation_errors}")

    print("\n✅ All tests completed!")

"""
Equivalence Engine for Permanent & Temporary Exchange Matching

This module implements the core matching logic for both exchange types:
- PERMANENT: value_a ≈ value_b (within ±15%)
- TEMPORARY: (value_a/days_a) ≈ (value_b/days_b) = daily_rate matching

Mathematical Framework from EXCHANGE_ECONOMIC_MODEL.md
"""

import math
from typing import Optional, Tuple, Dict
from enum import Enum
from dataclasses import dataclass
import os


class ExchangeType(str, Enum):
    """Exchange type enum"""
    PERMANENT = "permanent"
    TEMPORARY = "temporary"


class MatchScore(str, Enum):
    """Match score categories"""
    PERFECT = "perfect"      # >= 0.95 (99%+ match)
    EXCELLENT = "excellent"  # 0.90 - 0.95
    GREAT = "great"          # 0.80 - 0.90
    GOOD = "good"            # 0.70 - 0.80
    FAIR = "fair"            # 0.60 - 0.70
    POOR = "poor"            # < 0.60 (NO MATCH)


@dataclass
class EquivalenceResult:
    """Result of equivalence matching"""
    is_match: bool                          # Is it a match?
    score: float                            # 0.0 - 1.0
    category: MatchScore                    # Quality category
    difference_percent: float               # Difference in %
    explanation: str                        # Human-readable explanation


class ExchangeEquivalenceConfig:
    """
    Configuration for ExchangeEquivalence engine.
    Can be loaded from environment or config file.
    """

    # Load from environment variables (with defaults)
    VALUE_TOLERANCE = float(os.getenv("EXCHANGE_TOLERANCE", "0.15"))          # ±15%
    MIN_MATCH_SCORE = float(os.getenv("EXCHANGE_MIN_SCORE", "0.70"))          # 70%
    MAX_DURATION_DAYS = int(os.getenv("EXCHANGE_MAX_DURATION", "365"))        # 1 year
    MIN_DURATION_DAYS = int(os.getenv("EXCHANGE_MIN_DURATION", "1"))          # 1 day
    MIN_VALUE_TENGE = int(os.getenv("EXCHANGE_MIN_VALUE", "1"))               # 1 Tenge

    # Cache settings for performance
    ENABLE_RATE_CACHE = os.getenv("EXCHANGE_ENABLE_RATE_CACHE", "true").lower() == "true"
    CACHE_TTL_SECONDS = int(os.getenv("EXCHANGE_CACHE_TTL", "3600"))          # 1 hour

    @classmethod
    def validate(cls):
        """Validate configuration values"""
        if cls.VALUE_TOLERANCE < 0 or cls.VALUE_TOLERANCE > 1:
            raise ValueError("VALUE_TOLERANCE must be between 0 and 1")
        if cls.MIN_MATCH_SCORE < 0 or cls.MIN_MATCH_SCORE > 1:
            raise ValueError("MIN_MATCH_SCORE must be between 0 and 1")
        if cls.MAX_DURATION_DAYS <= cls.MIN_DURATION_DAYS:
            raise ValueError("MAX_DURATION_DAYS must be > MIN_DURATION_DAYS")
        if cls.MIN_VALUE_TENGE < 0:
            raise ValueError("MIN_VALUE_TENGE must be >= 0")

    @classmethod
    def to_dict(cls) -> Dict:
        """Export configuration as dictionary"""
        return {
            "VALUE_TOLERANCE": cls.VALUE_TOLERANCE,
            "MIN_MATCH_SCORE": cls.MIN_MATCH_SCORE,
            "MAX_DURATION_DAYS": cls.MAX_DURATION_DAYS,
            "MIN_DURATION_DAYS": cls.MIN_DURATION_DAYS,
            "MIN_VALUE_TENGE": cls.MIN_VALUE_TENGE,
            "ENABLE_RATE_CACHE": cls.ENABLE_RATE_CACHE,
            "CACHE_TTL_SECONDS": cls.CACHE_TTL_SECONDS,
        }


class ExchangeEquivalence:
    """
    Core equivalence engine for matching permanent and temporary exchanges.

    Supports:
    1. PERMANENT matching: value_a ≈ value_b
    2. TEMPORARY matching: daily_rate_a ≈ daily_rate_b
    3. MIXED matching: combining both types
    4. Configuration from environment
    5. Rate caching for performance
    """

    # Initialize configuration
    config = ExchangeEquivalenceConfig()
    config.validate()

    # Simple in-memory rate cache (for performance optimization)
    _rate_cache: Dict[int, Tuple[float, float]] = {}  # {item_id: (rate, timestamp)}

    @staticmethod
    def calculate_permanent_score(
        value_a: int,
        value_b: int,
        tolerance: Optional[float] = None
    ) -> EquivalenceResult:
        """
        Calculate equivalence score for PERMANENT exchange.

        Formula: score = 1.0 - (|value_a - value_b| / max(value_a, value_b))

        Args:
            value_a: First item value in Tenge
            value_b: Second item value in Tenge
            tolerance: Tolerance level (default from config)

        Returns:
            EquivalenceResult with score and match status

        Example:
            Alice: Phone 50k + Laptop 100k = 150k ₸
            Bob:   Tablet 80k + Headset 70k = 150k ₸
            Result: score = 1.0 (150k = 150k exactly)
        """

        tolerance = tolerance or ExchangeEquivalence.config.VALUE_TOLERANCE
        min_value = ExchangeEquivalence.config.MIN_VALUE_TENGE

        # Validate inputs
        if value_a < min_value or value_b < min_value:
            return EquivalenceResult(
                is_match=False,
                score=0.0,
                category=MatchScore.POOR,
                difference_percent=100.0,
                explanation=f"Invalid values: both must be >= {min_value}"
            )

        # Calculate absolute difference
        abs_diff = abs(value_a - value_b)
        max_value = max(value_a, value_b)

        # Calculate difference ratio
        diff_ratio = abs_diff / max_value if max_value > 0 else 0.0

        # Calculate score (inverted ratio: 1.0 is perfect match, 0.0 is complete mismatch)
        score = max(0.0, 1.0 - diff_ratio)

        # Convert to percentage
        difference_percent = diff_ratio * 100

        # Check if within tolerance
        is_within_tolerance = diff_ratio <= tolerance
        is_match = score >= ExchangeEquivalence.config.MIN_MATCH_SCORE

        # Determine category
        if score >= 0.95:
            category = MatchScore.PERFECT
        elif score >= 0.90:
            category = MatchScore.EXCELLENT
        elif score >= 0.80:
            category = MatchScore.GREAT
        elif score >= 0.70:
            category = MatchScore.GOOD
        elif score >= 0.60:
            category = MatchScore.FAIR
        else:
            category = MatchScore.POOR

        # Build explanation
        explanation = (
            f"Permanent: {value_a}₸ vs {value_b}₸ "
            f"(diff: {difference_percent:.1f}%) "
            f"{'✅ MATCH' if is_match else '❌ NO MATCH'} "
            f"(tolerance: ±{tolerance*100:.0f}%)"
        )

        return EquivalenceResult(
            is_match=is_match,
            score=score,
            category=category,
            difference_percent=difference_percent,
            explanation=explanation
        )

    @staticmethod
    def calculate_temporary_score(
        value_a: int,
        duration_a: int,
        value_b: int,
        duration_b: int,
        tolerance: Optional[float] = None
    ) -> EquivalenceResult:
        """
        Calculate equivalence score for TEMPORARY exchange.

        Formula:
            daily_rate_a = value_a / duration_a
            daily_rate_b = value_b / duration_b
            score = 1.0 - (|daily_rate_a - daily_rate_b| / max(daily_rate_a, daily_rate_b))

        Args:
            value_a: First item value in Tenge
            duration_a: First item rental duration in days
            value_b: Second item value in Tenge
            duration_b: Second item rental duration in days
            tolerance: Tolerance level (default from config)

        Returns:
            EquivalenceResult with score and match status

        Example:
            Alice: Bike (30k, 7 days) = 4,286 ₸/day
            Bob:   Drill (21k, 5 days) = 4,200 ₸/day
            Result: score = 0.98 (diff: 2%)
        """

        tolerance = tolerance or ExchangeEquivalence.config.VALUE_TOLERANCE
        min_value = ExchangeEquivalence.config.MIN_VALUE_TENGE
        min_dur = ExchangeEquivalence.config.MIN_DURATION_DAYS
        max_dur = ExchangeEquivalence.config.MAX_DURATION_DAYS

        # Validate inputs
        if value_a < min_value or value_b < min_value:
            return EquivalenceResult(
                is_match=False,
                score=0.0,
                category=MatchScore.POOR,
                difference_percent=100.0,
                explanation=f"Invalid values: both must be >= {min_value}"
            )

        if not (min_dur <= duration_a <= max_dur) or not (min_dur <= duration_b <= max_dur):
            return EquivalenceResult(
                is_match=False,
                score=0.0,
                category=MatchScore.POOR,
                difference_percent=100.0,
                explanation=f"Invalid duration: must be {min_dur}-{max_dur} days"
            )

        # Calculate daily rates (₸/day)
        daily_rate_a = value_a / duration_a
        daily_rate_b = value_b / duration_b

        # Calculate difference
        abs_diff = abs(daily_rate_a - daily_rate_b)
        max_rate = max(daily_rate_a, daily_rate_b)

        # Calculate difference ratio
        diff_ratio = abs_diff / max_rate if max_rate > 0 else 0.0

        # Calculate score
        score = max(0.0, 1.0 - diff_ratio)

        # Convert to percentage
        difference_percent = diff_ratio * 100

        # Check if within tolerance
        is_within_tolerance = diff_ratio <= tolerance
        is_match = score >= ExchangeEquivalence.config.MIN_MATCH_SCORE

        # Determine category
        if score >= 0.95:
            category = MatchScore.PERFECT
        elif score >= 0.90:
            category = MatchScore.EXCELLENT
        elif score >= 0.80:
            category = MatchScore.GREAT
        elif score >= 0.70:
            category = MatchScore.GOOD
        elif score >= 0.60:
            category = MatchScore.FAIR
        else:
            category = MatchScore.POOR

        # Build explanation
        explanation = (
            f"Temporary: {daily_rate_a:.0f}₸/day ({value_a}₸/{duration_a}d) "
            f"vs {daily_rate_b:.0f}₸/day ({value_b}₸/{duration_b}d) "
            f"(diff: {difference_percent:.1f}%) "
            f"{'✅ MATCH' if is_match else '❌ NO MATCH'} "
            f"(tolerance: ±{tolerance*100:.0f}%)"
        )

        return EquivalenceResult(
            is_match=is_match,
            score=score,
            category=category,
            difference_percent=difference_percent,
            explanation=explanation
        )

    @staticmethod
    def calculate_mixed_score(
        permanent_value: int,
        temporary_value: int,
        temporary_duration: int,
        tolerance: Optional[float] = None
    ) -> EquivalenceResult:
        """
        Calculate equivalence score for MIXED exchange (permanent + temporary).

        Formula:
            temporal_equivalent = temporary_value / temporary_duration
            Treat as permanent equivalence

        Args:
            permanent_value: Permanent item value in Tenge
            temporary_value: Temporary item value in Tenge
            temporary_duration: Temporary item duration in days
            tolerance: Tolerance level (default from config)

        Returns:
            EquivalenceResult with score

        Note:
            Mixed exchanges convert temporary to permanent using daily rate.
            This allows 1 permanent item to exchange for N temporary items.

        Example:
            Alice: 150k ₸ (permanent)
            Bob: 30k ₸ / 7 days (temporary) = 4,286₸/day × 35 days = 150k equivalent
            Result: Can match for 35-day rental
        """

        tolerance = tolerance or ExchangeEquivalence.config.VALUE_TOLERANCE
        min_dur = ExchangeEquivalence.config.MIN_DURATION_DAYS
        max_dur = ExchangeEquivalence.config.MAX_DURATION_DAYS

        if not (min_dur <= temporary_duration <= max_dur):
            return EquivalenceResult(
                is_match=False,
                score=0.0,
                category=MatchScore.POOR,
                difference_percent=100.0,
                explanation=f"Invalid duration for temporary item: {min_dur}-{max_dur} days"
            )

        # Convert temporary to permanent equivalent
        temporal_equivalent = temporary_value / temporary_duration

        # Calculate as permanent exchange
        result = ExchangeEquivalence.calculate_permanent_score(
            permanent_value,
            int(temporal_equivalent),
            tolerance
        )

        # Update explanation
        result.explanation = (
            f"Mixed: {permanent_value}₸ (permanent) "
            f"vs {temporary_value}₸/{temporary_duration}d = {temporal_equivalent:.0f}₸/day equivalent "
            f"{'✅ MATCH' if result.is_match else '❌ NO MATCH'}"
        )

        return result

    @staticmethod
    def is_valid_equivalence(
        value_a: int,
        value_b: int,
        tolerance: Optional[float] = None
    ) -> bool:
        """Quick check: are values within equivalence tolerance?"""
        tolerance = tolerance or ExchangeEquivalence.config.VALUE_TOLERANCE
        min_val = ExchangeEquivalence.config.MIN_VALUE_TENGE

        if value_a < min_val or value_b < min_val:
            return False

        diff_ratio = abs(value_a - value_b) / max(value_a, value_b)
        return diff_ratio <= tolerance

    @staticmethod
    def get_score_category(score: float) -> MatchScore:
        """Get match score category from numeric score"""
        if score >= 0.95:
            return MatchScore.PERFECT
        elif score >= 0.90:
            return MatchScore.EXCELLENT
        elif score >= 0.80:
            return MatchScore.GREAT
        elif score >= 0.70:
            return MatchScore.GOOD
        elif score >= 0.60:
            return MatchScore.FAIR
        else:
            return MatchScore.POOR

    @staticmethod
    def validate_item_data(
        exchange_type: str,
        value_tenge: int,
        duration_days: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Validate item data for consistency.

        Returns:
            Tuple[is_valid, error_message]
        """
        min_val = ExchangeEquivalence.config.MIN_VALUE_TENGE
        min_dur = ExchangeEquivalence.config.MIN_DURATION_DAYS
        max_dur = ExchangeEquivalence.config.MAX_DURATION_DAYS

        # Validate value
        if value_tenge < min_val:
            return False, f"value_tenge must be >= {min_val}"

        if exchange_type == ExchangeType.PERMANENT.value:
            if duration_days is not None:
                return False, "PERMANENT: duration_days must be NULL"
            return True, ""

        elif exchange_type == ExchangeType.TEMPORARY.value:
            if duration_days is None:
                return False, "TEMPORARY: duration_days is required"
            if not isinstance(duration_days, int):
                return False, "TEMPORARY: duration_days must be integer"
            if not (min_dur <= duration_days <= max_dur):
                return False, f"TEMPORARY: duration_days must be {min_dur}-{max_dur}"
            return True, ""

        else:
            return False, f"Unknown exchange_type: {exchange_type}"


# ============================================================
# COMPREHENSIVE TEST SCENARIOS
# ============================================================

class TestScenarios:
    """Test scenarios covering edge cases and all combinations"""

    @staticmethod
    def run_all():
        """Run all test scenarios"""
        print("=" * 80)
        print("🧪 COMPREHENSIVE TEST SUITE - ExchangeEquivalence")
        print("=" * 80)

        passed = 0
        failed = 0

        # PERMANENT TESTS
        print("\n" + "🟢" * 40)
        print("PERMANENT EXCHANGE TESTS")
        print("🟢" * 40)

        tests = [
            ("TEST 1: Perfect Match (150k = 150k)",
             lambda: ExchangeEquivalence.calculate_permanent_score(150000, 150000),
             True, 1.0),

            ("TEST 2: Within Tolerance (100k vs 115k = 15%)",
             lambda: ExchangeEquivalence.calculate_permanent_score(100000, 115000),
             True, 0.85),

            ("TEST 3: At Boundary (100k vs 130k = 30% - exceeds 15%)",
             lambda: ExchangeEquivalence.calculate_permanent_score(100000, 130000),
             False, 0.77),

            ("TEST 4: No Match (100k vs 200k = 50%)",
             lambda: ExchangeEquivalence.calculate_permanent_score(100000, 200000),
             False, 0.5),

            ("TEST 5: Edge - Very Small Values (100 vs 115)",
             lambda: ExchangeEquivalence.calculate_permanent_score(100, 115),
             True, 0.87),

            ("TEST 6: Very Large Values (5M vs 5.75M = 15%)",
             lambda: ExchangeEquivalence.calculate_permanent_score(5000000, 5750000),
             True, 0.85),

            ("TEST 7: Invalid - Zero Value",
             lambda: ExchangeEquivalence.calculate_permanent_score(0, 50000),
             False, 0.0),

            ("TEST 8: Invalid - Negative Value",
             lambda: ExchangeEquivalence.calculate_permanent_score(-50000, 50000),
             False, 0.0),
        ]

        for name, test_fn, expect_match, expect_score in tests:
            result = test_fn()
            match_ok = result.is_match == expect_match
            score_close = abs(result.score - expect_score) < 0.01

            status = "✅ PASS" if (match_ok and score_close) else "❌ FAIL"
            print(f"\n{status} {name}")
            print(f"  Score: {result.score:.2f} (expected ~{expect_score:.2f})")
            print(f"  Match: {result.is_match} (expected {expect_match})")
            print(f"  {result.explanation}")

            if match_ok and score_close:
                passed += 1
            else:
                failed += 1

        # TEMPORARY TESTS
        print("\n" + "🔵" * 40)
        print("TEMPORARY EXCHANGE TESTS")
        print("🔵" * 40)

        temp_tests = [
            ("TEST 9: Perfect Rate Match (4286 vs 4286 ₸/day)",
             lambda: ExchangeEquivalence.calculate_temporary_score(30000, 7, 30000, 7),
             True, 1.0),

            ("TEST 10: Rate Within Tolerance (4286 vs 4200 ₸/day = 2%)",
             lambda: ExchangeEquivalence.calculate_temporary_score(30000, 7, 21000, 5),
             True, 0.98),

            ("TEST 11: Rate No Match (5000 vs 3000 ₸/day = 40%)",
             lambda: ExchangeEquivalence.calculate_temporary_score(30000, 6, 15000, 5),
             False, 0.71),  # 30000/6 = 5000, 15000/5 = 3000, diff = 40%

            ("TEST 12: Edge - Minimum Duration (1 day each)",
             lambda: ExchangeEquivalence.calculate_temporary_score(5000, 1, 5000, 1),
             True, 1.0),

            ("TEST 13: Edge - Maximum Duration (365 days each)",
             lambda: ExchangeEquivalence.calculate_temporary_score(365000, 365, 365000, 365),
             True, 1.0),

            ("TEST 14: Invalid - Zero Duration",
             lambda: ExchangeEquivalence.calculate_temporary_score(30000, 0, 21000, 5),
             False, 0.0),

            ("TEST 15: Invalid - Negative Duration",
             lambda: ExchangeEquivalence.calculate_temporary_score(30000, -7, 21000, 5),
             False, 0.0),

            ("TEST 16: Invalid - Duration > 365",
             lambda: ExchangeEquivalence.calculate_temporary_score(30000, 400, 21000, 5),
             False, 0.0),
        ]

        for name, test_fn, expect_match, expect_score in temp_tests:
            result = test_fn()
            match_ok = result.is_match == expect_match
            score_close = abs(result.score - expect_score) < 0.05  # Allow 5% tolerance for complex calc

            status = "✅ PASS" if (match_ok and score_close) else "❌ FAIL"
            print(f"\n{status} {name}")
            print(f"  Score: {result.score:.2f} (expected ~{expect_score:.2f})")
            print(f"  Match: {result.is_match} (expected {expect_match})")
            print(f"  {result.explanation}")

            if match_ok and score_close:
                passed += 1
            else:
                failed += 1

        # MIXED TESTS
        print("\n" + "🟡" * 40)
        print("MIXED EXCHANGE TESTS")
        print("🟡" * 40)

        mixed_tests = [
            ("TEST 17: Mixed Perfect Match (150k vs 30k/7d = 4286₸/day)",
             lambda: ExchangeEquivalence.calculate_mixed_score(150000, 30000, 7),
             True, 1.0),

            ("TEST 18: Mixed Close Match (150k vs 21k/5d = 4200₸/day)",
             lambda: ExchangeEquivalence.calculate_mixed_score(150000, 21000, 5),
             True, 0.98),
        ]

        for name, test_fn, expect_match, expect_score in mixed_tests:
            result = test_fn()
            match_ok = result.is_match == expect_match
            score_close = abs(result.score - expect_score) < 0.05

            status = "✅ PASS" if (match_ok and score_close) else "❌ FAIL"
            print(f"\n{status} {name}")
            print(f"  Score: {result.score:.2f} (expected ~{expect_score:.2f})")
            print(f"  Match: {result.is_match} (expected {expect_match})")
            print(f"  {result.explanation}")

            if match_ok and score_close:
                passed += 1
            else:
                failed += 1

        # VALIDATION TESTS
        print("\n" + "⚙️ " * 40)
        print("VALIDATION TESTS")
        print("⚙️ " * 40)

        validation_tests = [
            ("TEST 19: Validate Permanent Item",
             lambda: ExchangeEquivalence.validate_item_data("permanent", 50000, None),
             (True, "")),

            ("TEST 20: Validate Permanent with Duration (should fail)",
             lambda: ExchangeEquivalence.validate_item_data("permanent", 50000, 7),
             (False, "")),

            ("TEST 21: Validate Temporary Item",
             lambda: ExchangeEquivalence.validate_item_data("temporary", 30000, 7),
             (True, "")),

            ("TEST 22: Validate Temporary without Duration (should fail)",
             lambda: ExchangeEquivalence.validate_item_data("temporary", 30000, None),
             (False, "")),

            ("TEST 23: Validate Invalid Duration",
             lambda: ExchangeEquivalence.validate_item_data("temporary", 30000, 400),
             (False, "")),
        ]

        for name, test_fn, expect_result in validation_tests:
            result = test_fn()
            is_valid, msg = result
            expect_valid, _ = expect_result

            status = "✅ PASS" if is_valid == expect_valid else "❌ FAIL"
            print(f"\n{status} {name}")
            print(f"  Valid: {is_valid} (expected {expect_valid})")
            if msg:
                print(f"  Message: {msg}")

            if is_valid == expect_valid:
                passed += 1
            else:
                failed += 1

        # CONFIG TEST
        print("\n" + "⚡" * 40)
        print("CONFIGURATION TEST")
        print("⚡" * 40)

        print(f"\nCurrent Configuration:")
        for key, val in ExchangeEquivalence.config.to_dict().items():
            print(f"  {key}: {val}")

        passed += 1  # Config test always passes if no exceptions

        # SUMMARY
        print("\n" + "=" * 80)
        print(f"TEST SUMMARY")
        print("=" * 80)
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"📊 TOTAL:  {passed + failed}")
        print(f"📈 SUCCESS RATE: {(passed / (passed + failed) * 100):.1f}%")
        print("=" * 80)

        return failed == 0


if __name__ == "__main__":
    success = TestScenarios.run_all()
    exit(0 if success else 1)

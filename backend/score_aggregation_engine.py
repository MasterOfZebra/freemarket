"""
Score Aggregation Engine

Handles:
- Final score calculation
- Location bonus application (+0.1)
- Trust bonus based on user rating (+0.05)
- Recency bonus for recent listings (+0.03)
- Threshold validation
- Score normalization (0.0-1.0)

Combines all scoring components into final match decision.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class BonusConfig:
    """Configuration for bonus scoring"""

    # Location bonus
    enable_location_bonus: bool = True
    location_bonus_value: float = 0.10

    # Trust bonus
    enable_trust_bonus: bool = True
    trust_bonus_value: float = 0.05
    min_trust_rating: float = 4.5

    # Recency bonus
    enable_recency_bonus: bool = True
    recency_bonus_value: float = 0.03
    recency_days_threshold: int = 7

    # Final thresholds
    min_valid_score: float = 0.70

    @classmethod
    def from_env(cls) -> "BonusConfig":
        """Load configuration from environment variables"""
        return cls(
            enable_location_bonus=os.getenv("BONUS_LOCATION_ENABLED", "true").lower() == "true",
            location_bonus_value=float(os.getenv("BONUS_LOCATION_VALUE", "0.10")),

            enable_trust_bonus=os.getenv("BONUS_TRUST_ENABLED", "true").lower() == "true",
            trust_bonus_value=float(os.getenv("BONUS_TRUST_VALUE", "0.05")),
            min_trust_rating=float(os.getenv("BONUS_TRUST_MIN_RATING", "4.5")),

            enable_recency_bonus=os.getenv("BONUS_RECENCY_ENABLED", "true").lower() == "true",
            recency_bonus_value=float(os.getenv("BONUS_RECENCY_VALUE", "0.03")),
            recency_days_threshold=int(os.getenv("BONUS_RECENCY_DAYS", "7")),

            min_valid_score=float(os.getenv("SCORE_MIN_VALID", "0.70")),
        )


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of score calculation"""

    base_score: float
    location_bonus: float
    trust_bonus: float
    recency_bonus: float
    final_score: float

    # Validity
    is_valid: bool
    validation_errors: list

    # Source info
    location_overlap: bool
    partner_rating: Optional[float]
    listing_age_days: Optional[int]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "base_score": round(self.base_score, 3),
            "bonuses": {
                "location": round(self.location_bonus, 3),
                "trust": round(self.trust_bonus, 3),
                "recency": round(self.recency_bonus, 3),
            },
            "total_bonuses": round(
                self.location_bonus + self.trust_bonus + self.recency_bonus, 3
            ),
            "final_score": round(self.final_score, 3),
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "metadata": {
                "location_overlap": self.location_overlap,
                "partner_rating": round(self.partner_rating, 2) if self.partner_rating else None,
                "listing_age_days": self.listing_age_days,
            }
        }


class ScoreAggregationEngine:
    """Final score calculation with bonuses and thresholds"""

    def __init__(self, config: Optional[BonusConfig] = None):
        """
        Initialize score aggregation engine

        Args:
            config: BonusConfig instance (loads from env if not provided)
        """
        self.config = config or BonusConfig.from_env()

        logger.info(
            f"ScoreAggregationEngine initialized:\n"
            f"  Location bonus: {self.config.enable_location_bonus} (value: {self.config.location_bonus_value})\n"
            f"  Trust bonus: {self.config.enable_trust_bonus} (value: {self.config.trust_bonus_value}, min_rating: {self.config.min_trust_rating})\n"
            f"  Recency bonus: {self.config.enable_recency_bonus} (value: {self.config.recency_bonus_value}, threshold: {self.config.recency_days_threshold}d)\n"
            f"  Min valid score: {self.config.min_valid_score}"
        )

    def apply_location_bonus(
        self,
        base_score: float,
        has_location_overlap: bool
    ) -> float:
        """
        Apply location bonus to score

        Args:
            base_score: Base score before bonus
            has_location_overlap: Whether user and partner share location

        Returns:
            Score after location bonus
        """
        if not self.config.enable_location_bonus or not has_location_overlap:
            return base_score

        bonus = self.config.location_bonus_value
        result = min(base_score + bonus, 1.0)  # Cap at 1.0

        logger.debug(
            f"Location bonus applied: {base_score:.3f} + {bonus:.3f} = {result:.3f}"
        )

        return result

    def apply_trust_bonus(
        self,
        base_score: float,
        partner_rating: Optional[float]
    ) -> float:
        """
        Apply trust bonus based on partner rating

        Args:
            base_score: Base score before bonus
            partner_rating: Partner's average rating (0.0-5.0)

        Returns:
            Score after trust bonus
        """
        if not self.config.enable_trust_bonus or partner_rating is None:
            return base_score

        # Only apply bonus if rating meets minimum threshold
        if partner_rating >= self.config.min_trust_rating:
            bonus = self.config.trust_bonus_value
            result = min(base_score + bonus, 1.0)

            logger.debug(
                f"Trust bonus applied (rating {partner_rating:.1f}): "
                f"{base_score:.3f} + {bonus:.3f} = {result:.3f}"
            )

            return result

        return base_score

    def apply_recency_bonus(
        self,
        base_score: float,
        created_at: Optional[datetime]
    ) -> float:
        """
        Apply recency bonus for recent listings

        Args:
            base_score: Base score before bonus
            created_at: When listing was created

        Returns:
            Score after recency bonus
        """
        if not self.config.enable_recency_bonus or created_at is None:
            return base_score

        # Calculate listing age
        now = datetime.utcnow()
        age = (now - created_at).days

        # Apply bonus if listing is recent enough
        if age <= self.config.recency_days_threshold:
            bonus = self.config.recency_bonus_value
            result = min(base_score + bonus, 1.0)

            logger.debug(
                f"Recency bonus applied ({age}d old): "
                f"{base_score:.3f} + {bonus:.3f} = {result:.3f}"
            )

            return result

        return base_score

    def calculate_final_score(
        self,
        base_score: float,
        has_location_overlap: bool = False,
        partner_rating: Optional[float] = None,
        created_at: Optional[datetime] = None,
        include_breakdown: bool = True
    ) -> Tuple[float, Optional[ScoreBreakdown]]:
        """
        Calculate final match score with all bonuses

        Pipeline:
        1. Start with base_score
        2. Apply location bonus (if location overlap)
        3. Apply trust bonus (if rating high enough)
        4. Apply recency bonus (if listing recent)
        5. Normalize to 0.0-1.0
        6. Return with breakdown

        Args:
            base_score: Base score from matching engine (0.0-1.0)
            has_location_overlap: Whether locations overlap
            partner_rating: Partner's rating (0.0-5.0)
            created_at: Listing creation datetime
            include_breakdown: Include detailed breakdown

        Returns:
            (final_score, breakdown) or (final_score, None)
        """
        # Validate input
        if not (0.0 <= base_score <= 1.0):
            logger.warning(f"Invalid base_score: {base_score}, clamping to 0.0-1.0")
            base_score = max(0.0, min(1.0, base_score))

        # Apply bonuses sequentially
        score = base_score
        score = self.apply_location_bonus(score, has_location_overlap)
        score = self.apply_trust_bonus(score, partner_rating)
        score = self.apply_recency_bonus(score, created_at)

        # Normalize
        final_score = max(0.0, min(1.0, score))

        # Build breakdown
        breakdown = None
        if include_breakdown:
            location_bonus = (
                self.config.location_bonus_value if (
                    self.config.enable_location_bonus and has_location_overlap
                ) else 0.0
            )

            trust_bonus = (
                self.config.trust_bonus_value if (
                    self.config.enable_trust_bonus and
                    partner_rating and
                    partner_rating >= self.config.min_trust_rating
                ) else 0.0
            )

            recency_bonus = 0.0
            listing_age_days = None
            if self.config.enable_recency_bonus and created_at:
                listing_age_days = (datetime.utcnow() - created_at).days
                if listing_age_days <= self.config.recency_days_threshold:
                    recency_bonus = self.config.recency_bonus_value

            # Validation
            is_valid = final_score >= self.config.min_valid_score
            errors = []
            if not is_valid:
                errors.append(
                    f"Score {final_score:.2f} < threshold {self.config.min_valid_score}"
                )

            breakdown = ScoreBreakdown(
                base_score=base_score,
                location_bonus=location_bonus,
                trust_bonus=trust_bonus,
                recency_bonus=recency_bonus,
                final_score=final_score,
                is_valid=is_valid,
                validation_errors=errors,
                location_overlap=has_location_overlap,
                partner_rating=partner_rating,
                listing_age_days=listing_age_days,
            )

        return final_score, breakdown

    def validate_threshold(
        self,
        score: float,
        threshold: Optional[float] = None
    ) -> bool:
        """
        Check if score passes threshold

        Args:
            score: Score to validate
            threshold: Threshold (uses config.min_valid_score if not provided)

        Returns:
            True if score >= threshold
        """
        min_threshold = threshold or self.config.min_valid_score
        return score >= min_threshold

    def get_score_quality_label(self, score: float) -> str:
        """
        Get quality label for score

        Args:
            score: Score (0.0-1.0)

        Returns:
            Quality label: excellent/good/fair/poor
        """
        if score >= 0.90:
            return "excellent"
        elif score >= 0.75:
            return "good"
        elif score >= 0.50:
            return "fair"
        else:
            return "poor"

    def calculate_score_percentile(
        self,
        score: float,
        all_scores: list
    ) -> float:
        """
        Calculate score percentile among all scores

        Args:
            score: Score to rank
            all_scores: List of all scores

        Returns:
            Percentile (0.0-100.0)
        """
        if not all_scores:
            return 0.0

        count_below = sum(1 for s in all_scores if s < score)
        percentile = (count_below / len(all_scores)) * 100.0

        return percentile

    def format_score_report(
        self,
        base_score: float,
        has_location_overlap: bool = False,
        partner_rating: Optional[float] = None,
        created_at: Optional[datetime] = None,
    ) -> str:
        """
        Generate human-readable score report

        Args:
            base_score: Base matching score
            has_location_overlap: Location overlap flag
            partner_rating: Partner rating
            created_at: Listing creation time

        Returns:
            Formatted report string
        """
        final_score, breakdown = self.calculate_final_score(
            base_score,
            has_location_overlap,
            partner_rating,
            created_at,
            include_breakdown=True
        )

        if not breakdown:
            return f"Score: {final_score:.2f}"

        report = f"""
╔═══════════════════════════════════╗
║ MATCH SCORE BREAKDOWN             ║
╚═══════════════════════════════════╝

Base Score:           {breakdown.base_score:.3f}

Bonuses:
  • Location (+0.10): {breakdown.location_bonus:.3f}
  • Trust (+0.05):    {breakdown.trust_bonus:.3f}
  • Recency (+0.03):  {breakdown.recency_bonus:.3f}

──────────────────────────────────
FINAL SCORE:          {breakdown.final_score:.3f}
──────────────────────────────────

Quality:              {self.get_score_quality_label(breakdown.final_score)}
Valid Match:          {'✅ YES' if breakdown.is_valid else '❌ NO'}
Threshold:            {self.config.min_valid_score:.2f}
"""

        return report


if __name__ == "__main__":
    # Test the score aggregation engine
    print("🧪 Score Aggregation Engine Tests\n")

    engine = ScoreAggregationEngine()

    # Test 1: Base score only
    print("✅ TEST 1: Base Score Only")
    score, breakdown = engine.calculate_final_score(0.75)
    print(f"  Base: 0.75 → Final: {score:.3f}")

    # Test 2: With location bonus
    print("\n✅ TEST 2: With Location Bonus")
    score, breakdown = engine.calculate_final_score(0.75, has_location_overlap=True)
    print(f"  Base: 0.75 + Location: {score:.3f}")
    print(f"  Report:{engine.format_score_report(0.75, has_location_overlap=True)}")

    # Test 3: With trust bonus
    print("\n✅ TEST 3: With Trust Bonus (high rating)")
    score, breakdown = engine.calculate_final_score(0.75, partner_rating=4.7)
    print(f"  Base: 0.75 + Trust (4.7★): {score:.3f}")

    # Test 4: With recency bonus
    print("\n✅ TEST 4: With Recency Bonus (recent listing)")
    recent_time = datetime.utcnow() - timedelta(days=3)
    score, breakdown = engine.calculate_final_score(0.75, created_at=recent_time)
    print(f"  Base: 0.75 + Recency (3d old): {score:.3f}")

    # Test 5: All bonuses combined
    print("\n✅ TEST 5: All Bonuses Combined")
    recent_time = datetime.utcnow() - timedelta(days=2)
    score, breakdown = engine.calculate_final_score(
        0.75,
        has_location_overlap=True,
        partner_rating=4.8,
        created_at=recent_time
    )
    print(f"  Base: 0.75 + All bonuses: {score:.3f}")
    print(f"  Valid: {breakdown.is_valid if breakdown else 'N/A'}")

    # Test 6: Low score (should be invalid)
    print("\n✅ TEST 6: Low Score (should be invalid)")
    score, breakdown = engine.calculate_final_score(0.45)
    print(f"  Base: 0.45 → Final: {score:.3f}")
    print(f"  Valid: {breakdown.is_valid if breakdown else 'N/A'}")

    # Test 7: Quality label
    print("\n✅ TEST 7: Quality Labels")
    for test_score in [0.95, 0.80, 0.65, 0.40]:
        label = engine.get_score_quality_label(test_score)
        print(f"  Score {test_score:.2f} → {label}")

    print("\n✅ All tests completed!")

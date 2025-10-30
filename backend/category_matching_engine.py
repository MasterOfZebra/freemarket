"""
Category Matching Engine

Handles:
- Item grouping by category
- Core matching within each category
- Location-based pre-filtering
- Score aggregation (average, weighted, minimum)
- Multi-category match finding

Orchestrates CoreMatchingEngine and LocationFilter for category-level matching.
"""

from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from enum import Enum
import logging
from dataclasses import dataclass

from backend.core_matching_engine import CoreMatchingEngine, ItemPairScore
from backend.location_filtering import LocationFilter

logger = logging.getLogger(__name__)


class AggregationMethod(str, Enum):
    """Aggregation strategies for multi-category scores"""
    AVERAGE = "average"        # Mean of all category scores
    WEIGHTED = "weighted"      # Weighted by item count per category
    MINIMUM = "minimum"        # Only passes if ALL categories match
    MAXIMUM = "maximum"        # Passes if ANY category matches well


@dataclass
class CategoryMatchResult:
    """Result for a single category match"""
    category: str
    score: float
    matching_pairs: List[ItemPairScore]
    item_count_user: int
    item_count_candidate: int

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "category": self.category,
            "score": round(self.score, 3),
            "pair_count": len(self.matching_pairs),
            "item_count_user": self.item_count_user,
            "item_count_candidate": self.item_count_candidate,
            "best_pairs": [p.to_dict() for p in self.matching_pairs[:3]],  # Top 3
        }


@dataclass
class UserMatchResult:
    """Complete match result for user pair"""
    user_id: int
    candidate_id: int
    final_score: float
    quality: str
    location_bonus: float
    categories: Dict[str, CategoryMatchResult]

    # Matching info
    matching_categories: int  # How many categories matched
    total_categories: int     # How many were compared

    # Validity
    is_valid: bool
    errors: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "candidate_id": self.candidate_id,
            "final_score": round(self.final_score, 3),
            "quality": self.quality,
            "location_bonus": round(self.location_bonus, 2),
            "total_score": round(self.final_score + self.location_bonus, 3),
            "matching_categories": self.matching_categories,
            "total_categories": self.total_categories,
            "categories": {k: v.to_dict() for k, v in self.categories.items()},
            "is_valid": self.is_valid,
        }


class CategoryMatchingEngine:
    """Multi-category matching orchestration"""

    def __init__(
        self,
        core_engine: Optional[CoreMatchingEngine] = None,
        location_filter: Optional[LocationFilter] = None,
        min_category_score: float = 0.50,
        min_valid_categories: int = 1,
    ):
        """
        Initialize category matching engine

        Args:
            core_engine: CoreMatchingEngine instance
            location_filter: LocationFilter instance
            min_category_score: Minimum score per category (default 0.50)
            min_valid_categories: Minimum matching categories required (default 1)
        """
        self.core_engine = core_engine or CoreMatchingEngine()
        self.location_filter = location_filter or LocationFilter()

        self.min_category_score = min_category_score
        self.min_valid_categories = min_valid_categories

        logger.info(
            f"CategoryMatchingEngine initialized: "
            f"min_cat_score={min_category_score} "
            f"min_valid_cats={min_valid_categories}"
        )

    def _group_by_category(self, items: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group items by category

        Args:
            items: List of item dicts

        Returns:
            Dict[category, [items]]
        """
        grouped = defaultdict(list)
        for item in items:
            category = item.get('category')
            if category:
                grouped[category].append(item)

        return dict(grouped)

    def _get_location_filtered_candidates(
        self,
        user_locations: List[str],
        candidates: List[Dict]
    ) -> Tuple[List[Dict], Dict[int, float]]:
        """
        Filter candidates by location and get bonuses

        Args:
            user_locations: User's preferred cities
            candidates: List of candidate dicts with 'id' and 'locations'

        Returns:
            (filtered_candidates, location_bonuses)
        """
        return self.location_filter.filter_candidates_by_location(
            user_locations,
            candidates,
            enable_bonus=True
        )

    def _score_category_match(
        self,
        user_items: List[Dict],
        candidate_items: List[Dict],
        category: str
    ) -> Tuple[float, List[ItemPairScore]]:
        """
        Score matching between user and candidate items in one category

        Strategy:
        1. Create all possible pairs (user_items × candidate_items)
        2. Score each pair using CoreMatchingEngine
        3. Keep only valid matches (score ≥ min_category_score)
        4. Return aggregated score and best matches

        Args:
            user_items: User's items in this category
            candidate_items: Candidate's items in this category
            category: Category name (for validation)

        Returns:
            (aggregated_score, list_of_best_pairs)
        """
        if not user_items or not candidate_items:
            return 0.0, []

        pairs_scores: List[ItemPairScore] = []

        # Score all pairs
        for user_item in user_items:
            for candidate_item in candidate_items:
                # Ensure same category
                if user_item['category'] != candidate_item['category']:
                    continue

                # Score the pair
                result = self.core_engine.score_item_pair(user_item, candidate_item)
                pairs_scores.append(result)

        if not pairs_scores:
            return 0.0, []

        # Filter by minimum category score
        valid_pairs = [p for p in pairs_scores if p.final_score >= self.min_category_score]

        if not valid_pairs:
            return 0.0, []

        # Sort by score descending
        valid_pairs.sort(key=lambda p: p.final_score, reverse=True)

        # Calculate aggregated score (average of top matches)
        aggregated_score = sum(p.final_score for p in valid_pairs) / len(valid_pairs)

        logger.debug(
            f"Category '{category}': "
            f"{len(user_items)} user items × {len(candidate_items)} candidate items = "
            f"{len(pairs_scores)} pairs, "
            f"{len(valid_pairs)} valid (score ≥ {self.min_category_score}), "
            f"aggregated: {aggregated_score:.3f}"
        )

        return aggregated_score, valid_pairs

    def _aggregate_scores(
        self,
        category_scores: Dict[str, float],
        method: str = AggregationMethod.AVERAGE.value,
        item_counts: Optional[Dict[str, Tuple[int, int]]] = None
    ) -> float:
        """
        Aggregate scores across categories

        Args:
            category_scores: Dict[category, score]
            method: 'average', 'weighted', 'minimum', 'maximum'
            item_counts: Dict[category, (user_count, candidate_count)] for weighted

        Returns:
            Final aggregated score
        """
        if not category_scores:
            return 0.0

        scores = list(category_scores.values())

        if method == AggregationMethod.AVERAGE.value:
            # Simple average
            return sum(scores) / len(scores)

        elif method == AggregationMethod.WEIGHTED.value:
            # Weighted by item count (more items = more weight)
            if not item_counts:
                return sum(scores) / len(scores)

            total_weight = 0
            weighted_sum = 0

            for category, score in category_scores.items():
                if category in item_counts:
                    user_count, candidate_count = item_counts[category]
                    weight = max(user_count, candidate_count)  # Weight by larger count
                    weighted_sum += score * weight
                    total_weight += weight

            if total_weight == 0:
                return sum(scores) / len(scores)

            return weighted_sum / total_weight

        elif method == AggregationMethod.MINIMUM.value:
            # Only passes if ALL categories match well
            return min(scores) if scores else 0.0

        elif method == AggregationMethod.MAXIMUM.value:
            # Passes if ANY category matches well
            return max(scores) if scores else 0.0

        else:
            # Default to average
            return sum(scores) / len(scores)

    def find_matches_for_user(
        self,
        user_id: int,
        user_listings: Dict[str, List[Dict]],
        user_locations: List[str],
        candidates: List[Dict],
        aggregation_method: str = AggregationMethod.AVERAGE.value,
        location_bonus_value: float = 0.1,
    ) -> List[UserMatchResult]:
        """
        Find all matches for a user against candidates

        Full matching pipeline:
        1. Filter candidates by location
        2. For each candidate:
           a. Group both user and candidate items by category
           b. Score each category independently
           c. Aggregate category scores
           d. Apply location bonus
           e. Return result

        Args:
            user_id: User ID
            user_listings: Dict[category, [items]] for user
            user_locations: User's cities
            candidates: List of candidate dicts with 'id', 'locations', 'listings'
            aggregation_method: How to combine category scores
            location_bonus_value: Bonus if locations overlap

        Returns:
            List of UserMatchResult (sorted by score)
        """
        logger.info(f"Finding matches for user {user_id} against {len(candidates)} candidates")

        # Step 1: Filter candidates by location
        filtered_candidates, location_bonuses = self._get_location_filtered_candidates(
            user_locations,
            candidates
        )

        if not filtered_candidates:
            logger.warning(f"No candidates left after location filtering for user {user_id}")
            return []

        logger.info(
            f"Location filtering: {len(candidates)} → {len(filtered_candidates)} candidates"
        )

        all_results: List[UserMatchResult] = []

        # Step 2: Score each candidate
        for candidate in filtered_candidates:
            candidate_id = candidate['id']
            candidate_listings = candidate.get('listings', {})
            candidate_locations = candidate.get('locations', [])

            # Get categories to compare (intersection)
            user_categories = set(user_listings.keys())
            candidate_categories = set(candidate_listings.keys())
            common_categories = user_categories & candidate_categories

            if not common_categories:
                logger.debug(f"No common categories between user {user_id} and candidate {candidate_id}")
                continue

            # Score each category
            category_results: Dict[str, CategoryMatchResult] = {}
            category_scores: Dict[str, float] = {}
            item_counts: Dict[str, Tuple[int, int]] = {}

            for category in common_categories:
                user_items = user_listings.get(category, [])
                candidate_items = candidate_listings.get(category, [])

                if not user_items or not candidate_items:
                    continue

                score, pairs = self._score_category_match(
                    user_items,
                    candidate_items,
                    category
                )

                if score > 0:
                    category_results[category] = CategoryMatchResult(
                        category=category,
                        score=score,
                        matching_pairs=pairs,
                        item_count_user=len(user_items),
                        item_count_candidate=len(candidate_items),
                    )
                    category_scores[category] = score
                    item_counts[category] = (len(user_items), len(candidate_items))

            if not category_scores:
                logger.debug(f"No matching categories for user {user_id} and candidate {candidate_id}")
                continue

            # Aggregate scores
            base_score = self._aggregate_scores(
                category_scores,
                aggregation_method,
                item_counts
            )

            # Apply location bonus
            location_bonus = location_bonuses.get(candidate_id, 0.0)
            final_score = base_score + location_bonus

            # Determine quality
            if final_score >= 0.85:
                quality = "excellent"
            elif final_score >= 0.70:
                quality = "good"
            elif final_score >= 0.50:
                quality = "fair"
            else:
                quality = "poor"

            # Check if valid
            matching_cats = len(category_scores)
            is_valid = matching_cats >= self.min_valid_categories and base_score >= 0.50

            result = UserMatchResult(
                user_id=user_id,
                candidate_id=candidate_id,
                final_score=final_score,
                quality=quality,
                location_bonus=location_bonus,
                categories=category_results,
                matching_categories=matching_cats,
                total_categories=len(common_categories),
                is_valid=is_valid,
                errors=[] if is_valid else ["Insufficient matching categories or low score"],
            )

            all_results.append(result)

        # Sort by score descending
        all_results.sort(key=lambda r: r.final_score, reverse=True)

        logger.info(
            f"Found {len(all_results)} matches for user {user_id}, "
            f"{sum(1 for r in all_results if r.is_valid)} are valid"
        )

        return all_results

    def get_top_matches(
        self,
        matches: List[UserMatchResult],
        top_n: int = 5,
        min_score: Optional[float] = None,
        only_valid: bool = True
    ) -> List[UserMatchResult]:
        """
        Get top N matches from results

        Args:
            matches: All match results
            top_n: Number of top matches to return
            min_score: Minimum score threshold
            only_valid: Only include valid matches

        Returns:
            Filtered and sorted list
        """
        filtered = matches

        # Filter by validity
        if only_valid:
            filtered = [m for m in filtered if m.is_valid]

        # Filter by minimum score
        if min_score is not None:
            filtered = [m for m in filtered if m.final_score >= min_score]

        # Return top N
        return filtered[:top_n]

    def get_matching_statistics(
        self,
        matches: List[UserMatchResult]
    ) -> Dict:
        """
        Calculate statistics about matches

        Args:
            matches: All match results

        Returns:
            Statistics dict
        """
        if not matches:
            return {
                "total_matches": 0,
                "valid_matches": 0,
                "avg_score": 0.0,
                "max_score": 0.0,
                "quality_distribution": {},
            }

        valid_matches = [m for m in matches if m.is_valid]
        scores = [m.final_score for m in valid_matches] if valid_matches else []

        quality_dist = defaultdict(int)
        for match in matches:
            quality_dist[match.quality] += 1

        return {
            "total_matches": len(matches),
            "valid_matches": len(valid_matches),
            "avg_score": sum(scores) / len(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
            "min_score": min(scores) if scores else 0.0,
            "quality_distribution": dict(quality_dist),
        }


if __name__ == "__main__":
    # Test the category matching engine
    print("🧪 Category Matching Engine Tests\n")

    engine = CategoryMatchingEngine(min_category_score=0.50, min_valid_categories=1)

    # Test 1: Single category matching
    print("✅ TEST 1: Single Category Match")
    user_listings = {
        "electronics": [
            {
                "id": 1,
                "category": "electronics",
                "exchange_type": "permanent",
                "value_tenge": 50000,
                "item_name": "iPhone",
            }
        ]
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
                        "value_tenge": 52000,
                        "item_name": "iPhone",
                    }
                ]
            }
        }
    ]

    results = engine.find_matches_for_user(
        user_id=1,
        user_listings=user_listings,
        user_locations=["Алматы"],
        candidates=candidates,
        aggregation_method=AggregationMethod.AVERAGE.value
    )

    if results:
        print(f"  Found {len(results)} matches")
        print(f"  Top match score: {results[0].final_score:.3f}")

    # Test 2: Multi-category matching
    print("\n✅ TEST 2: Multi-Category Match")
    user_listings = {
        "electronics": [
            {
                "id": 1,
                "category": "electronics",
                "exchange_type": "permanent",
                "value_tenge": 50000,
                "item_name": "Laptop",
            }
        ],
        "furniture": [
            {
                "id": 3,
                "category": "furniture",
                "exchange_type": "permanent",
                "value_tenge": 30000,
                "item_name": "Desk",
            }
        ]
    }

    candidates = [
        {
            "id": 102,
            "locations": ["Алматы"],
            "listings": {
                "electronics": [
                    {
                        "id": 4,
                        "category": "electronics",
                        "exchange_type": "permanent",
                        "value_tenge": 50000,
                        "item_name": "Computer",
                    }
                ],
                "furniture": [
                    {
                        "id": 5,
                        "category": "furniture",
                        "exchange_type": "permanent",
                        "value_tenge": 32000,
                        "item_name": "Table",
                    }
                ]
            }
        }
    ]

    results = engine.find_matches_for_user(
        user_id=1,
        user_listings=user_listings,
        user_locations=["Алматы"],
        candidates=candidates,
        aggregation_method=AggregationMethod.AVERAGE.value
    )

    if results:
        print(f"  Found {len(results)} matches")
        print(f"  Matching categories: {results[0].matching_categories}/{results[0].total_categories}")

    print("\n✅ All tests completed!")

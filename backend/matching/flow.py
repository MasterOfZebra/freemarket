"""
Unified Matching Flow Engine

Orchestrates the complete matching pipeline:
1. Location-aware candidate filtering
2. Scoring with location bonuses
3. Bilateral matching detection
4. Chain discovery (3+ participants)
5. Notification creation
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Dict, Tuple
import logging

from backend.models import Item, User, Match, ExchangeChain
from backend.crud import create_notification
from backend.schemas import NotificationCreate

logger = logging.getLogger(__name__)


class MatchingEngine:
    """Unified matching engine for FreeMarket"""

    def __init__(self, db: Session):
        self.db = db
        self.threshold = 0.3  # Minimum score for edge/match

    # ========================================================================
    # PHASE 1: LOCATION-AWARE CANDIDATE FILTERING
    # ========================================================================

    def find_location_aware_candidates(self, item: Item) -> List[Item]:
        """
        Find candidates with location filtering.

        Returns only items from users who share at least one location.
        """
        item_user = self.db.query(User).filter(User.id == item.user_id).first()
        if not item_user or not item_user.locations:
            return []

        # Find opposite kind in same category
        candidates = self.db.query(Item).filter(
            and_(
                Item.category == item.category,
                Item.user_id != item.user_id,
                Item.active == True,
                Item.kind != item.kind  # opposite kind
            )
        ).all()

        # Filter by location overlap
        location_filtered = []
        for candidate in candidates:
            candidate_user = self.db.query(User).filter(
                User.id == candidate.user_id
            ).first()

            if candidate_user and candidate_user.locations:
                # Check for at least one common location
                if any(loc in item_user.locations
                       for loc in candidate_user.locations):
                    location_filtered.append(candidate)

        return location_filtered

    # ========================================================================
    # PHASE 2: UNIFIED SCORING
    # ========================================================================

    def calculate_score(self, item_a: Item, item_b: Item) -> float:
        """
        Calculate match score with all factors:
        - Text similarity (TF-IDF)
        - Trust bonus
        - Location bonus

        Returns: score 0.0-1.0
        """
        # Text similarity
        text_score = self._text_similarity(item_a, item_b)

        # Trust bonus
        user_b = self.db.query(User).filter(User.id == item_b.user_id).first()
        trust_bonus = min(user_b.trust_score * 0.1, 0.2) if user_b else 0

        # Location bonus
        user_a = self.db.query(User).filter(User.id == item_a.user_id).first()
        location_bonus = 0.0

        if user_a and user_a.locations and user_b and user_b.locations:
            if any(loc in user_a.locations for loc in user_b.locations):
                location_bonus = 0.1

        # Final score (clamped to 1.0)
        score = min(text_score * 0.7 + trust_bonus + location_bonus, 1.0)
        return float(score)

    def _text_similarity(self, item_a: Item, item_b: Item) -> float:
        """Simple text similarity based on word overlap"""
        text_a = (item_a.description or item_a.title or "").lower().split()
        text_b = (item_b.description or item_b.title or "").lower().split()

        if not text_a or not text_b:
            return 0.5

        set_a, set_b = set(text_a), set(text_b)
        overlap = len(set_a & set_b)

        return overlap / max(len(set_a), len(set_b))

    # ========================================================================
    # PHASE 3: BILATERAL MATCHING
    # ========================================================================

    def find_bilateral_matches(self, item: Item) -> List[Dict]:
        """
        Find bilateral matches for a single item.

        Requirements:
        - item_a.want ⊆ item_b.offer (item_b satisfies item_a's want)
        - item_b.want ⊆ item_a.offer (item_a satisfies item_b's want)
        - score > threshold
        """
        if item.kind != 2:  # Must be a want
            return []

        candidates = self.find_location_aware_candidates(item)
        matches = []

        for candidate in candidates:
            # Both must be active and from different users
            if not candidate.active or candidate.user_id == item.user_id:
                continue

            score = self.calculate_score(item, candidate)

            if score >= self.threshold:
                # Check if other user also has complementary item
                other_candidate = self.db.query(Item).filter(
                    and_(
                        Item.user_id == item.user_id,
                        Item.kind == 1,  # This user's offer
                        Item.category == candidate.category,
                        Item.active == True
                    )
                ).first()

                if other_candidate:
                    other_score = self.calculate_score(candidate, other_candidate)
                    if other_score >= self.threshold:
                        # Bilateral match found!
                        matches.append({
                            "item_a": item.id,
                            "item_b": candidate.id,
                            "score": score,
                            "bidirectional_score": other_score,
                            "computed_by": "unified_engine"
                        })

        return matches

    # ========================================================================
    # PHASE 4: CHAIN DISCOVERY
    # ========================================================================

    def discover_chains(self) -> List[Dict]:
        """
        Discover multi-way exchange chains (3+ participants).

        Uses DFS to find cycles in the want-offer graph.
        """
        from backend.chain_matching import discover_and_create_chains

        try:
            chains_created = discover_and_create_chains(self.db)
            return chains_created
        except Exception as e:
            logger.warning(f"Chain discovery failed: {e}")
            return 0

    # ========================================================================
    # PHASE 5: NOTIFICATION
    # ========================================================================

    async def notify_matches(self, matches: List[Dict]) -> None:
        """Send notifications for all match participants (both DB and Telegram)"""
        import asyncio
        from backend.bot import send_match_notification

        for match in matches:
            item_a = self.db.query(Item).filter(Item.id == match['item_a']).first()
            item_b = self.db.query(Item).filter(Item.id == match['item_b']).first()

            if not item_a or not item_b:
                continue

            user_a = self.db.query(User).filter(User.id == item_a.user_id).first()
            user_b = self.db.query(User).filter(User.id == item_b.user_id).first()

            if not user_a or not user_b:
                continue

            match_id = match.get('id', 0)

            # Notification for user A
            payload_a = {
                "type": "bilateral_match",
                "match_id": match_id,
                "partner": user_b.username,
                "partner_contact": user_b.contact,
                "partner_item": item_b.description or item_b.title,
                "your_item": item_a.description or item_a.title,
                "score": match['score'],
                "message": f"Найдено совпадение с {user_b.username}!"
            }

            create_notification(self.db, NotificationCreate(
                user_id=user_a.id,
                payload=payload_a
            ))

            # Send Telegram notification to user A
            if user_a.telegram_id:
                await send_match_notification(
                    user_telegram_id=user_a.telegram_id,
                    partner_username=user_b.contact if user_b.contact else f"User {user_b.id}",
                    partner_wants=item_b.description or item_b.title or "товар",
                    your_offers=item_a.description or item_a.title or "товар",
                    score=match['score'],
                    match_id=match_id
                )

            # Notification for user B
            payload_b = {
                "type": "bilateral_match",
                "match_id": match_id,
                "partner": user_a.username,
                "partner_contact": user_a.contact,
                "partner_item": item_a.description or item_a.title,
                "your_item": item_b.description or item_b.title,
                "score": match.get('bidirectional_score', match['score']),
                "message": f"Найдено совпадение с {user_a.username}!"
            }

            create_notification(self.db, NotificationCreate(
                user_id=user_b.id,
                payload=payload_b
            ))

            # Send Telegram notification to user B
            if user_b.telegram_id:
                await send_match_notification(
                    user_telegram_id=user_b.telegram_id,
                    partner_username=user_a.contact if user_a.contact else f"User {user_a.id}",
                    partner_wants=item_a.description or item_a.title or "товар",
                    your_offers=item_b.description or item_b.title or "товар",
                    score=match.get('bidirectional_score', match['score']),
                    match_id=match_id
                )

    # ========================================================================
    # COMPLETE PIPELINE
    # ========================================================================

    def run_full_pipeline(self, user_id: int = None) -> Dict:
        """
        Run complete matching pipeline:
        1. Get location-aware candidates
        2. Score them
        3. Find bilateral matches
        4. Discover chains
        5. Notify participants

        Returns statistics
        """
        logger.info("=== Starting full matching pipeline ===")

        stats = {
            "bilateral_matches": 0,
            "exchange_chains": 0,
            "total_participants": 0,
            "errors": []
        }

        try:
            # Get user items to match
            if user_id:
                user_items = self.db.query(Item).filter(
                    and_(Item.user_id == user_id, Item.active == True)
                ).all()
            else:
                user_items = self.db.query(Item).filter(Item.active == True).all()

            all_matches = []

            # Phase 1-3: Find bilateral matches
            for item in user_items:
                if item.kind == 2:  # Only wants
                    matches = self.find_bilateral_matches(item)
                    all_matches.extend(matches)

            stats["bilateral_matches"] = len(all_matches)

            # Phase 5: Notify
            asyncio.run(self.notify_matches(all_matches))

            # Phase 4: Discover chains
            chains_created = self.discover_chains()
            stats["exchange_chains"] = chains_created

            logger.info(f"Pipeline complete: {len(all_matches)} bilateral, "
                       f"{chains_created} chains")

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            stats["errors"].append(str(e))

        return stats

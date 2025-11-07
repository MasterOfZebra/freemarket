"""
Reviews service for user ratings and reputation management.

Handles review creation, rating calculation, and Redis caching.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from .database import get_db
from .models import UserReview, User, ExchangeHistory, ExchangeEventType
from .notification_service import get_notification_service
from .config import REDIS_URL

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class ReviewsService:
    """
    Service for managing user reviews and ratings.
    """

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.redis_client: Optional[redis.Redis] = None

        if REDIS_AVAILABLE and REDIS_URL:
            try:
                self.redis_client = redis.from_url(REDIS_URL)
                logger.info("Connected to Redis for reviews caching")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")

    def create_review(
        self,
        author_id: int,
        target_id: int,
        exchange_id: str,
        rating: int,
        text: Optional[str] = None,
        is_public: bool = True
    ) -> Optional[UserReview]:
        """
        Create a new review for completed exchange.

        Args:
            author_id: User leaving the review
            target_id: User being reviewed
            exchange_id: Related exchange
            rating: Rating 1-5
            text: Review text (optional)
            is_public: Whether review is public

        Returns:
            Created UserReview or None if failed
        """
        try:
            # Validate rating
            if not 1 <= rating <= 5:
                logger.warning(f"Invalid rating {rating} for review")
                return None

            # Anti-spam: Check review frequency limits
            if not self._check_review_limits(author_id, target_id):
                logger.warning(f"Review spam detected for user {author_id}")
                return None

            # Check if exchange exists and is completed
            exchange_completed = self.db.query(ExchangeHistory).filter(
                and_(
                    ExchangeHistory.exchange_id == exchange_id,
                    ExchangeHistory.event_type == ExchangeEventType.COMPLETED
                )
            ).first()

            if not exchange_completed:
                logger.warning(f"Cannot review incomplete exchange {exchange_id}")
                return None

            # Check if review already exists
            existing_review = self.db.query(UserReview).filter(
                and_(
                    UserReview.author_id == author_id,
                    UserReview.exchange_id == exchange_id
                )
            ).first()

            if existing_review:
                logger.warning(f"Review already exists for exchange {exchange_id} by user {author_id}")
                return None

            # Mark review as verified (since exchange is completed)
            is_verified = True

            # Create review
            review = UserReview(
                author_id=author_id,
                target_id=target_id,
                exchange_id=exchange_id,
                rating=rating,
                text=text,
                is_public=is_public
            )

            self.db.add(review)
            self.db.commit()
            self.db.refresh(review)

            logger.info(f"Created verified review {review.id} for user {target_id} by {author_id}")

            # Update user's rating cache
            self._update_user_rating(target_id)

            # Send notification
            notification_service = get_notification_service(self.db)
            import asyncio
            asyncio.create_task(
                notification_service.notify_review_received(target_id, review.id, rating)
            )

            return review

        except Exception as e:
            logger.error(f"Failed to create review: {e}")
            self.db.rollback()
            return None

    def _update_user_rating(self, user_id: int):
        """
        Update user's cached rating statistics.

        Args:
            user_id: User ID to update
        """
        try:
            # Calculate new average rating and count
            result = self.db.query(
                func.avg(UserReview.rating).label('avg_rating'),
                func.count(UserReview.id).label('count')
            ).filter(
                and_(
                    UserReview.target_id == user_id,
                    UserReview.is_public == True
                )
            ).first()

            avg_rating = float(result.avg_rating) if result.avg_rating else 0.0
            count = result.count or 0

            # Update user record
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.rating_avg = avg_rating
                user.rating_count = count
                user.last_rating_update = datetime.utcnow()
                self.db.commit()

                logger.info(f"Updated rating for user {user_id}: {avg_rating:.2f} ({count} reviews)")

                # Cache in Redis
                self._cache_user_rating(user_id, avg_rating, count)

        except Exception as e:
            logger.error(f"Failed to update user rating: {e}")
            self.db.rollback()

    def _cache_user_rating(self, user_id: int, avg_rating: float, count: int):
        """
        Cache user rating in Redis for fast access.
        """
        if not self.redis_client:
            return

        try:
            cache_key = f"user_rating:{user_id}"
            cache_data = {
                "rating_avg": avg_rating,
                "rating_count": count,
                "last_update": datetime.utcnow().isoformat()
            }

            self.redis_client.setex(cache_key, 3600, json.dumps(cache_data))  # 1 hour TTL

        except Exception as e:
            logger.error(f"Failed to cache user rating: {e}")

    def get_user_rating(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's rating statistics.

        Args:
            user_id: User ID

        Returns:
            Rating data with cache fallback
        """
        # Try Redis cache first
        if self.redis_client:
            try:
                cache_key = f"user_rating:{user_id}"
                cached = self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Failed to get cached rating: {e}")

        # Fallback to database
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    "rating_avg": user.rating_avg or 0.0,
                    "rating_count": user.rating_count or 0,
                    "last_update": user.last_rating_update.isoformat() if user.last_rating_update else None
                }

        except Exception as e:
            logger.error(f"Failed to get user rating from DB: {e}")

        return {"rating_avg": 0.0, "rating_count": 0, "last_update": None}

    def get_user_reviews(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        public_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get reviews for a user.

        Args:
            user_id: User being reviewed
            limit: Max reviews to return
            offset: Pagination offset
            public_only: Return only public reviews

        Returns:
            List of review dictionaries
        """
        try:
            query = self.db.query(UserReview).filter(UserReview.target_id == user_id)

            if public_only:
                query = query.filter(UserReview.is_public == True)

            reviews = query.order_by(
                desc(UserReview.created_at)
            ).offset(offset).limit(limit).all()

            return [review.to_dict() for review in reviews]

        except Exception as e:
            logger.error(f"Failed to get user reviews: {e}")
            return []

    def get_reviews_given(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get reviews given by a user.

        Args:
            user_id: User who gave reviews
            limit: Max reviews to return
            offset: Pagination offset

        Returns:
            List of review dictionaries
        """
        try:
            reviews = self.db.query(UserReview).filter(
                UserReview.author_id == user_id
            ).order_by(
                desc(UserReview.created_at)
            ).offset(offset).limit(limit).all()

            return [review.to_dict() for review in reviews]

        except Exception as e:
            logger.error(f"Failed to get reviews given: {e}")
            return []

    def _check_review_limits(self, author_id: int, target_id: int) -> bool:
        """
        Check review frequency limits to prevent spam.

        Args:
            author_id: User creating the review
            target_id: User being reviewed

        Returns:
            True if review is allowed, False if spam detected
        """
        try:
            from datetime import datetime, timedelta

            # Limit 1: Max 5 reviews per day from one author
            one_day_ago = datetime.utcnow() - timedelta(days=1)
            daily_reviews = self.db.query(UserReview).filter(
                and_(
                    UserReview.author_id == author_id,
                    UserReview.created_at >= one_day_ago
                )
            ).count()

            if daily_reviews >= 5:
                logger.warning(f"Daily review limit exceeded for user {author_id}")
                return False

            # Limit 2: Max 10 reviews per week from one author
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            weekly_reviews = self.db.query(UserReview).filter(
                and_(
                    UserReview.author_id == author_id,
                    UserReview.created_at >= one_week_ago
                )
            ).count()

            if weekly_reviews >= 10:
                logger.warning(f"Weekly review limit exceeded for user {author_id}")
                return False

            # Limit 3: Max 3 reviews for the same target in 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            target_reviews = self.db.query(UserReview).filter(
                and_(
                    UserReview.author_id == author_id,
                    UserReview.target_id == target_id,
                    UserReview.created_at >= thirty_days_ago
                )
            ).count()

            if target_reviews >= 3:
                logger.warning(f"Target review limit exceeded for user {author_id} -> {target_id}")
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to check review limits: {e}")
            # Allow review on error to avoid blocking legitimate reviews
            return True

    def can_review_exchange(self, user_id: int, exchange_id: str) -> bool:
        """
        Check if user can leave a review for exchange.

        Args:
            user_id: User wanting to review
            exchange_id: Exchange to review

        Returns:
            True if review is allowed
        """
        try:
            # Check if exchange is completed
            completed = self.db.query(ExchangeHistory).filter(
                and_(
                    ExchangeHistory.exchange_id == exchange_id,
                    ExchangeHistory.event_type == ExchangeEventType.COMPLETED,
                    ExchangeHistory.user_id == user_id  # User was involved
                )
            ).first()

            if not completed:
                return False

            # Check if review already exists
            existing = self.db.query(UserReview).filter(
                and_(
                    UserReview.author_id == user_id,
                    UserReview.exchange_id == exchange_id
                )
            ).first()

            return existing is None

        except Exception as e:
            logger.error(f"Failed to check review permission: {e}")
            return False

    def get_exchange_participants(self, exchange_id: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Get participants of an exchange for review purposes.

        Args:
            exchange_id: Exchange identifier

        Returns:
            Tuple of (user_a_id, user_b_id)
        """
        try:
            # Parse exchange_id format: mutual_X_Y_A_B
            parts = exchange_id.split("_")
            if len(parts) >= 4:
                return int(parts[1]), int(parts[2])  # user_a_id, user_b_id
        except (ValueError, IndexError):
            pass
        return None, None


# Global service instance
_reviews_service: Optional[ReviewsService] = None


def get_reviews_service(db: Session = None) -> ReviewsService:
    """Get global reviews service instance"""
    global _reviews_service
    if _reviews_service is None or db:
        _reviews_service = ReviewsService(db)
    return _reviews_service

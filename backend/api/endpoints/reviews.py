"""
API endpoints for user reviews and ratings.

Provides REST endpoints for managing user reviews and reputation.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.reviews_service import get_reviews_service
from backend.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])


class ReviewCreateRequest(BaseModel):
    """Request model for creating a review"""
    target_user_id: int = Field(..., description="User being reviewed")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5 stars")
    text: Optional[str] = Field(None, max_length=1000, description="Review text")
    is_public: bool = Field(True, description="Whether review is public")


@router.post("/exchanges/{exchange_id}")
def create_review(
    exchange_id: str,
    review_data: ReviewCreateRequest,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Create a review for a completed exchange.

    User must be a participant in the exchange and exchange must be completed.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    reviews_service = get_reviews_service(db)

    # Check if user can review this exchange
    if not reviews_service.can_review_exchange(current_user.id, exchange_id):
        raise HTTPException(
            status_code=403,
            detail="Cannot review this exchange (not completed or already reviewed)"
        )

    # Validate target user is a participant
    user_a, user_b = reviews_service.get_exchange_participants(exchange_id)
    if review_data.target_user_id not in [user_a, user_b]:
        raise HTTPException(status_code=400, detail="Target user is not a participant in this exchange")

    # Don't allow self-reviews
    if review_data.target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot review yourself")

    # Create the review
    review = reviews_service.create_review(
        author_id=current_user.id,
        target_id=review_data.target_user_id,
        exchange_id=exchange_id,
        rating=review_data.rating,
        text=review_data.text,
        is_public=review_data.is_public
    )

    if not review:
        raise HTTPException(status_code=500, detail="Failed to create review")

    return {
        "status": "created",
        "review": review.to_dict()
    }


@router.get("/users/{user_id}")
def get_user_reviews(
    user_id: int,
    current_user=Depends(get_current_user_optional),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    public_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Get reviews received by a user.

    Query parameters:
    - limit: Max reviews to return (1-100)
    - offset: Pagination offset
    - public_only: Return only public reviews
    """
    reviews_service = get_reviews_service(db)

    # If viewing own reviews, show all (including private)
    if current_user and current_user.id == user_id:
        public_only = False

    reviews = reviews_service.get_user_reviews(
        user_id=user_id,
        limit=limit,
        offset=offset,
        public_only=public_only
    )

    return {
        "user_id": user_id,
        "reviews": reviews,
        "limit": limit,
        "offset": offset
    }


@router.get("/users/{user_id}/given")
def get_reviews_given(
    user_id: int,
    current_user=Depends(get_current_user_optional),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get reviews given by a user.

    Query parameters:
    - limit: Max reviews to return (1-100)
    - offset: Pagination offset
    """
    # Only allow viewing own given reviews or admin
    if not current_user or (current_user.id != user_id and not current_user.is_admin):
        raise HTTPException(status_code=403, detail="Access denied")

    reviews_service = get_reviews_service(db)
    reviews = reviews_service.get_reviews_given(
        user_id=user_id,
        limit=limit,
        offset=offset
    )

    return {
        "user_id": user_id,
        "reviews_given": reviews,
        "limit": limit,
        "offset": offset
    }


@router.get("/users/{user_id}/rating")
def get_user_rating(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user's rating statistics.
    """
    reviews_service = get_reviews_service(db)
    rating_data = reviews_service.get_user_rating(user_id)

    return {
        "user_id": user_id,
        "rating": rating_data
    }


@router.get("/exchanges/{exchange_id}/can-review")
def can_review_exchange(
    exchange_id: str,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Check if current user can leave a review for exchange.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    reviews_service = get_reviews_service(db)
    can_review = reviews_service.can_review_exchange(current_user.id, exchange_id)

    participants = reviews_service.get_exchange_participants(exchange_id)

    return {
        "exchange_id": exchange_id,
        "can_review": can_review,
        "participants": participants,
        "current_user_id": current_user.id
    }


# Admin endpoints
@router.delete("/admin/reviews/{review_id}")
def delete_review_admin(
    review_id: int,
    reason: str = Query(..., description="Reason for deletion"),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: Delete a review.

    Requires admin privileges.
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from backend.models import UserReview

        # Get review before deletion for logging
        review = db.query(UserReview).filter(UserReview.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        # Log the deletion
        logger.info(f"Admin {current_user.id} deleted review {review_id} by {review.author_id} for user {review.target_id}. Reason: {reason}")

        # Delete the review
        db.query(UserReview).filter(UserReview.id == review_id).delete()
        db.commit()

        # Update target user's rating cache
        reviews_service = get_reviews_service(db)
        reviews_service._update_user_rating(review.target_id)

        return {
            "status": "deleted",
            "review_id": review_id,
            "reason": reason
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete review: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete review")

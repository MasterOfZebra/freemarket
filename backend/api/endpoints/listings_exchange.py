"""
API Endpoints for Exchange Type Listings (Permanent & Temporary)

This module handles:
- Creating listings with items organized by category and exchange type
- Retrieving listings with grouped items
- Finding matches based on equivalence logic
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import logging

from backend.database import SessionLocal
from backend.models import User, Listing, ListingItem, ListingItemType, ExchangeType
from backend.schemas import (
    ListingItemsByCategoryCreate,
    ListingItemsByCategoryResponse,
    ListingItemResponse
)
from backend.equivalence_engine import ExchangeEquivalence
from backend.language_normalization import get_normalizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/listings", tags=["listings"])

# Initialize language normalizer for matching
language_normalizer = get_normalizer()


def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# CREATE LISTING ENDPOINTS
# ============================================================

@router.post("/create-by-categories", response_model=Dict)
def create_listing_by_categories(
    user_id: int = Query(..., description="User ID"),
    listing: ListingItemsByCategoryCreate = None,
    db: Session = Depends(get_db)
):
    """
    Create a new listing with items organized by categories and exchange types.

    Request body:
    {
      "wants": {
        "electronics": [
          {"category": "electronics", "exchange_type": "permanent", "item_name": "Phone", "value_tenge": 50000}
        ],
        "transport": [
          {"category": "transport", "exchange_type": "temporary", "item_name": "Bike", "value_tenge": 30000, "duration_days": 7}
        ]
      },
      "offers": { ... },
      "locations": ["Алматы", "Астана"]
    }

    Returns:
    {
      "listing_id": 123,
      "user_id": 1,
      "items_created": 5,
      "wants": { ... },
      "offers": { ... },
      "status": "success"
    }
    """

    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        # Create listing
        db_listing = Listing(user_id=user_id)
        db.add(db_listing)
        db.flush()  # Get listing ID before creating items

        items_created = 0
        wants_summary = {}
        offers_summary = {}

        # Process WANTS
        for category, items in listing.wants.items():
            wants_summary[category] = []
            for item in items:
                db_item = ListingItem(
                    listing_id=db_listing.id,
                    item_type=ListingItemType.WANT,
                    category=category,
                    exchange_type=item.exchange_type,
                    item_name=item.item_name,
                    value_tenge=item.value_tenge,
                    duration_days=item.duration_days,
                    description=item.description or ""
                )

                # Validate item
                if not db_item.is_valid:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid want item: {item.item_name} (check value and duration)"
                    )

                db.add(db_item)
                items_created += 1
                wants_summary[category].append({
                    "item_name": item.item_name,
                    "value_tenge": item.value_tenge,
                    "daily_rate": db_item.daily_rate,
                    "exchange_type": item.exchange_type.value
                })

        # Process OFFERS
        for category, items in listing.offers.items():
            offers_summary[category] = []
            for item in items:
                db_item = ListingItem(
                    listing_id=db_listing.id,
                    item_type=ListingItemType.OFFER,
                    category=category,
                    exchange_type=item.exchange_type,
                    item_name=item.item_name,
                    value_tenge=item.value_tenge,
                    duration_days=item.duration_days,
                    description=item.description or ""
                )

                # Validate item
                if not db_item.is_valid:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid offer item: {item.item_name} (check value and duration)"
                    )

                db.add(db_item)
                items_created += 1
                offers_summary[category].append({
                    "item_name": item.item_name,
                    "value_tenge": item.value_tenge,
                    "daily_rate": db_item.daily_rate,
                    "exchange_type": item.exchange_type.value
                })

        # Update user locations if provided
        if listing.locations:
            user.locations = listing.locations

        db.commit()
        db.refresh(db_listing)

        logger.info(f"Created listing {db_listing.id} for user {user_id} with {items_created} items")

        # Automatically trigger matching after listing creation
        matches_found = 0
        try:
            # Call matching function directly (defined in this module)
            # Use the same logic as find_matches_for_user endpoint
            matching_result = _find_matches_internal(user_id, None, db)
            matches_found = matching_result.get("matches_found", 0)

            logger.info(f"Automatic matching completed: {matches_found} matches found for user {user_id}")
        except Exception as matching_error:
            # Don't fail listing creation if matching fails
            logger.warning(f"Matching failed after listing creation (listing still created): {matching_error}")

        return {
            "status": "success",
            "listing_id": db_listing.id,
            "user_id": user_id,
            "items_created": items_created,
            "matches_found": matches_found,
            "wants": wants_summary,
            "offers": offers_summary,
            "locations": user.locations
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating listing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# RETRIEVE LISTING ENDPOINTS
# ============================================================

@router.get("/user/{user_id}", response_model=Dict)
def get_user_listings(
    user_id: int,
    exchange_type: Optional[str] = Query(None, description="Filter by exchange type (permanent/temporary)"),
    db: Session = Depends(get_db)
):
    """
    Get all listings for a user, organized by category and exchange type.

    Query params:
    - exchange_type: Optional filter for "permanent" or "temporary"

    Returns:
    {
      "user_id": 1,
      "listings": [
        {
          "listing_id": 123,
          "wants": { ... },
          "offers": { ... },
          "created_at": "2025-01-15T..."
        }
      ]
    }
    """

    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        # Get listings
        query = db.query(Listing).filter(Listing.user_id == user_id)
        listings = query.all()

        listings_data = []
        for listing in listings:
            wants_by_cat = {}
            offers_by_cat = {}

            for item in listing.items:
                # Apply exchange type filter if provided
                if exchange_type and item.exchange_type.value != exchange_type:
                    continue

                if item.item_type == ListingItemType.WANT:
                    if item.category not in wants_by_cat:
                        wants_by_cat[item.category] = []
                    wants_by_cat[item.category].append({
                        "item_id": item.id,
                        "item_name": item.item_name,
                        "value_tenge": item.value_tenge,
                        "daily_rate": item.daily_rate,
                        "exchange_type": item.exchange_type.value,
                        "description": item.description
                    })
                else:  # OFFER
                    if item.category not in offers_by_cat:
                        offers_by_cat[item.category] = []
                    offers_by_cat[item.category].append({
                        "item_id": item.id,
                        "item_name": item.item_name,
                        "value_tenge": item.value_tenge,
                        "daily_rate": item.daily_rate,
                        "exchange_type": item.exchange_type.value,
                        "description": item.description
                    })

            listings_data.append({
                "listing_id": listing.id,
                "wants_by_category": wants_by_cat,
                "offers_by_category": offers_by_cat,
                "created_at": listing.created_at.isoformat()
            })

        return {
            "user_id": user_id,
            "total_listings": len(listings_data),
            "listings": listings_data,
            "locations": user.locations
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# MATCHING ENDPOINTS
# ============================================================

def _find_matches_internal(
    user_id: int,
    exchange_type: Optional[str] = None,
    db: Session = None
):
    """
    Internal matching function that can be called from other endpoints.
    Separated from the HTTP endpoint to avoid circular dependencies.

    Find all potential matches for a user's listing items.

    Matching algorithm:
    1. Find all other users
    2. For each category in user's listing, find items in other listings
    3. Calculate equivalence score
    4. Create notifications for matches
    5. Return matches sorted by score

    Args:
        user_id: User ID to find matches for
        exchange_type: Optional filter for "permanent" or "temporary"
        db: Database session (required, but can be None for HTTP endpoint calls)

    Returns:
    {
      "user_id": 1,
      "matches_found": 5,
      "notifications_created": 10,
      "matches": [...]
    }
    """

    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        # Get user's latest listing
        my_listing = db.query(Listing).filter(
            Listing.user_id == user_id
        ).order_by(Listing.created_at.desc()).first()

        if not my_listing:
            return {"user_id": user_id, "matches": []}

        matches = []

        # Get my wants and offers
        my_wants = db.query(ListingItem).filter(
            ListingItem.listing_id == my_listing.id,
            ListingItem.item_type == ListingItemType.WANT
        ).all()

        my_offers = db.query(ListingItem).filter(
            ListingItem.listing_id == my_listing.id,
            ListingItem.item_type == ListingItemType.OFFER
        ).all()

        # Get all other users' listings
        other_listings = db.query(Listing).filter(
            Listing.user_id != user_id
        ).all()

        # Find matches
        for other_listing in other_listings:
            other_user = db.query(User).filter(User.id == other_listing.user_id).first()

            other_wants = db.query(ListingItem).filter(
                ListingItem.listing_id == other_listing.id,
                ListingItem.item_type == ListingItemType.WANT
            ).all()

            other_offers = db.query(ListingItem).filter(
                ListingItem.listing_id == other_listing.id,
                ListingItem.item_type == ListingItemType.OFFER
            ).all()

            # Match my wants with their offers
            for my_want in my_wants:
                if exchange_type and my_want.exchange_type.value != exchange_type:
                    continue

                for their_offer in other_offers:
                    if my_want.category != their_offer.category:
                        continue

                    if my_want.exchange_type != their_offer.exchange_type:
                        continue

                    # Calculate equivalence score
                    if my_want.exchange_type == ExchangeType.PERMANENT:
                        result = ExchangeEquivalence.calculate_permanent_score(
                            my_want.value_tenge,
                            their_offer.value_tenge
                        )
                    else:  # TEMPORARY
                        result = ExchangeEquivalence.calculate_temporary_score(
                            my_want.value_tenge,
                            my_want.duration_days,
                            their_offer.value_tenge,
                            their_offer.duration_days
                        )

                    # Apply language similarity multiplier
                    language_similarity = language_normalizer.similarity_score(
                        my_want.item_name,
                        their_offer.item_name
                    )

                    # Combined score: 70% equivalence, 30% language similarity
                    combined_score = result.score * 0.7 + language_similarity * 0.3

                    # Only match if both equivalence and combined score pass threshold
                    if result.is_match and combined_score >= 0.70:
                        matches.append({
                            "match_id": f"{my_want.id}_{their_offer.id}",
                            "type": "want_offer",
                            "partner_user_id": other_user.id,
                            "partner_contact": other_user.contact,
                            "category": my_want.category,
                            "exchange_type": my_want.exchange_type.value,
                            "my_want": {
                                "item_id": my_want.id,
                                "item_name": my_want.item_name,
                                "value_tenge": my_want.value_tenge,
                                "duration_days": my_want.duration_days,
                                "daily_rate": my_want.daily_rate
                            },
                            "their_offer": {
                                "item_id": their_offer.id,
                                "item_name": their_offer.item_name,
                                "value_tenge": their_offer.value_tenge,
                                "duration_days": their_offer.duration_days,
                                "daily_rate": their_offer.daily_rate
                            },
                            "score": round(combined_score, 2),
                            "equivalence_score": round(result.score, 2),
                            "language_similarity": round(language_similarity, 2),
                            "score_category": result.category.value,
                            "difference_percent": round(result.difference_percent, 1),
                            "explanation": result.explanation
                        })

            # Match my offers with their wants
            for my_offer in my_offers:
                if exchange_type and my_offer.exchange_type.value != exchange_type:
                    continue

                for their_want in other_wants:
                    if my_offer.category != their_want.category:
                        continue

                    if my_offer.exchange_type != their_want.exchange_type:
                        continue

                    # Calculate equivalence score
                    if my_offer.exchange_type == ExchangeType.PERMANENT:
                        result = ExchangeEquivalence.calculate_permanent_score(
                            my_offer.value_tenge,
                            their_want.value_tenge
                        )
                    else:  # TEMPORARY
                        result = ExchangeEquivalence.calculate_temporary_score(
                            my_offer.value_tenge,
                            my_offer.duration_days,
                            their_want.value_tenge,
                            their_want.duration_days
                        )

                    # Apply language similarity multiplier
                    language_similarity = language_normalizer.similarity_score(
                        my_offer.item_name,
                        their_want.item_name
                    )

                    # Combined score: 70% equivalence, 30% language similarity
                    combined_score = result.score * 0.7 + language_similarity * 0.3

                    # Only match if both equivalence and combined score pass threshold
                    if result.is_match and combined_score >= 0.70:
                        matches.append({
                            "match_id": f"{my_offer.id}_{their_want.id}",
                            "type": "offer_want",
                            "partner_user_id": other_user.id,
                            "partner_contact": other_user.contact,
                            "category": my_offer.category,
                            "exchange_type": my_offer.exchange_type.value,
                            "my_offer": {
                                "item_id": my_offer.id,
                                "item_name": my_offer.item_name,
                                "value_tenge": my_offer.value_tenge,
                                "duration_days": my_offer.duration_days,
                                "daily_rate": my_offer.daily_rate
                            },
                            "their_want": {
                                "item_id": their_want.id,
                                "item_name": their_want.item_name,
                                "value_tenge": their_want.value_tenge,
                                "duration_days": their_want.duration_days,
                                "daily_rate": their_want.daily_rate
                            },
                            "score": round(combined_score, 2),
                            "equivalence_score": round(result.score, 2),
                            "language_similarity": round(language_similarity, 2),
                            "score_category": result.category.value,
                            "difference_percent": round(result.difference_percent, 1),
                            "explanation": result.explanation
                        })

        # Sort by score descending
        matches.sort(key=lambda x: x["score"], reverse=True)

        # Create notifications for each match
        from backend.crud import create_notification
        from backend.schemas import NotificationCreate

        notifications_created = 0
        for match in matches:
            try:
                partner_user_id = match["partner_user_id"]
                partner_user = db.query(User).filter(User.id == partner_user_id).first()

                if partner_user:
                    # Notification for partner (they have an item that matches user's want/offer)
                    partner_notification = NotificationCreate(
                        user_id=partner_user_id,
                        payload={
                            "match_id": match["match_id"],
                            "match_type": match.get("type", "unknown"),
                            "your_item": match.get("their_offer") or match.get("their_want", {}),
                            "matched_with": match.get("my_want") or match.get("my_offer", {}),
                            "score": match["score"],
                            "quality": match.get("score_category", "unknown"),
                            "category": match.get("category", ""),
                            "exchange_type": match.get("exchange_type", ""),
                            "difference_percent": match.get("difference_percent", 0),
                            "explanation": match.get("explanation", "")
                        }
                    )
                    create_notification(db, partner_notification)
                    notifications_created += 1

                # Notification for current user (optional - they initiated the search)
                user_notification = NotificationCreate(
                    user_id=user_id,
                    payload={
                        "match_id": match["match_id"],
                        "match_type": match.get("type", "unknown"),
                        "your_item": match.get("my_want") or match.get("my_offer", {}),
                        "matched_with": match.get("their_offer") or match.get("their_want", {}),
                        "partner_user_id": partner_user_id,
                        "partner_contact": match.get("partner_contact", ""),
                        "score": match["score"],
                        "quality": match.get("score_category", "unknown"),
                        "category": match.get("category", ""),
                        "exchange_type": match.get("exchange_type", ""),
                        "difference_percent": match.get("difference_percent", 0),
                        "explanation": match.get("explanation", "")
                    }
                )
                create_notification(db, user_notification)
                notifications_created += 1

            except Exception as notif_error:
                logger.warning(f"Failed to create notification for match {match.get('match_id')}: {notif_error}")
                # Continue processing other matches

        db.commit()  # Commit notifications

        logger.info(f"Found {len(matches)} matches for user {user_id}, created {notifications_created} notifications")

        return {
            "user_id": user_id,
            "matches_found": len(matches),
            "notifications_created": notifications_created,
            "matches": matches
        }

    except ValueError as ve:
        # Re-raise ValueError as HTTPException for HTTP endpoint
        logger.error(f"Error finding matches: {ve}")
        raise HTTPException(status_code=404 if "not found" in str(ve).lower() else 500, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/find-matches/{user_id}")
def find_matches_for_user(
    user_id: int,
    exchange_type: Optional[str] = Query(None, description="Filter by exchange type"),
    db: Session = Depends(get_db)
):
    """
    HTTP endpoint wrapper for matching functionality.
    Delegates to _find_matches_internal for the actual work.
    """
    return _find_matches_internal(user_id, exchange_type, db)

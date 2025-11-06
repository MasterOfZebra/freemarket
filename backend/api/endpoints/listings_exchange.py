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

router = APIRouter(prefix="/listings", tags=["listings"])

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
# GET LISTINGS - FOR FRONTEND DISPLAY
# ============================================================

@router.get("/wants", response_model=Dict)
def get_wants_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    exchange_type: Optional[str] = None,
    min_price: Optional[int] = Query(None, ge=1),
    max_price: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db)
):
    """
    Get all wants (what people need) from existing listings.
    Supports pagination and filtering.
    """
    try:
        query = db.query(ListingItem).filter(
            ListingItem.item_type == ListingItemType.WANT
        )

        # Apply filters
        if category:
            query = query.filter(ListingItem.category == category)
        if exchange_type:
            query = query.filter(ListingItem.exchange_type == exchange_type)
        if min_price:
            query = query.filter(ListingItem.value_tenge >= min_price)
        if max_price:
            query = query.filter(ListingItem.value_tenge <= max_price)

        query = query.order_by(ListingItem.created_at.desc())

        total = query.count()
        items = query.offset(skip).limit(limit).all()

        items_list = []
        for item in items:
            items_list.append({
                "id": item.id,
                "item_name": item.item_name,
                "category": item.category,
                "value_tenge": item.value_tenge,
                "duration_days": item.duration_days,
                "daily_rate": item.daily_rate,
                "exchange_type": item.exchange_type.value,
                "description": item.description,
                "created_at": item.created_at.isoformat() if item.created_at else None
            })

        # Build filters info
        applied_filters = {}
        if category:
            applied_filters["category"] = category
        if exchange_type:
            applied_filters["exchange_type"] = exchange_type
        if min_price:
            applied_filters["min_price"] = min_price
        if max_price:
            applied_filters["max_price"] = max_price

        return {
            "items": items_list,
            "total": total,
            "skip": skip,
            "limit": limit,
            "filters_applied": applied_filters
        }
    except Exception as e:
        logger.error(f"Error fetching wants: {e}")
        return {"items": [], "total": 0, "skip": skip, "limit": limit, "error": str(e)}


@router.get("/offers", response_model=Dict)
def get_offers_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    exchange_type: Optional[str] = None,
    min_price: Optional[int] = Query(None, ge=1),
    max_price: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db)
):
    """
    Get all offers (what people have) from existing listings.
    Supports pagination and filtering.
    """
    try:
        query = db.query(ListingItem).filter(
            ListingItem.item_type == ListingItemType.OFFER
        )

        # Apply filters
        if category:
            query = query.filter(ListingItem.category == category)
        if exchange_type:
            query = query.filter(ListingItem.exchange_type == exchange_type)
        if min_price:
            query = query.filter(ListingItem.value_tenge >= min_price)
        if max_price:
            query = query.filter(ListingItem.value_tenge <= max_price)

        query = query.order_by(ListingItem.created_at.desc())

        total = query.count()
        items = query.offset(skip).limit(limit).all()

        items_list = []
        for item in items:
            items_list.append({
                "id": item.id,
                "item_name": item.item_name,
                "category": item.category,
                "value_tenge": item.value_tenge,
                "duration_days": item.duration_days,
                "daily_rate": item.daily_rate,
                "exchange_type": item.exchange_type.value,
                "description": item.description,
                "created_at": item.created_at.isoformat() if item.created_at else None
            })

        # Build filters info
        applied_filters = {}
        if category:
            applied_filters["category"] = category
        if exchange_type:
            applied_filters["exchange_type"] = exchange_type
        if min_price:
            applied_filters["min_price"] = min_price
        if max_price:
            applied_filters["max_price"] = max_price

        return {
            "items": items_list,
            "total": total,
            "skip": skip,
            "limit": limit,
            "filters_applied": applied_filters
        }
    except Exception as e:
        logger.error(f"Error fetching offers: {e}")
        return {"items": [], "total": 0, "skip": skip, "limit": limit, "error": str(e)}


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

        # Update user data if provided
        if listing.user_data:
            user_data = listing.user_data
            if user_data.get('name'):
                user.username = user_data['name']
            if user_data.get('telegram'):
                telegram = user_data['telegram'].strip()
                if telegram.startswith('@'):
                    user.telegram_username = telegram
                elif telegram.isdigit() or (telegram.startswith('+') and telegram[1:].isdigit()):
                    try:
                        user.telegram_id = int(telegram.replace('+', ''))
                    except:
                        pass
                else:
                    user.telegram_username = telegram
            db.flush()

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


@router.post("/create", response_model=Dict)
def create_listing(
    user_id: int = Query(..., description="User ID"),
    listing: ListingItemsByCategoryCreate = None,
    db: Session = Depends(get_db)
):
    """
    Create a new listing with items organized by category.

    This is the main endpoint for creating listings from the frontend form.

    Request: POST /api/listings/create?user_id=1
    Body:
    {
      "wants": {
        "cars": [
          {
            "category": "cars",
            "exchange_type": "permanent",
            "item_name": "Honda Civic",
            "value_tenge": 1000000,
            "description": "Отличная машина"
          }
        ]
      },
      "offers": {},
      "locations": ["Алматы"],
      "user_data": {"name": "Иван", "telegram": "@ivan", "city": "Алматы"}
    }
    """

    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        # Update user data if provided
        if listing.user_data:
            user_data = listing.user_data
            if user_data.get('name'):
                user.username = user_data['name']
            if user_data.get('telegram'):
                telegram = user_data['telegram'].strip()
                if telegram.startswith('@'):
                    user.telegram_username = telegram
                elif telegram.isdigit() or (telegram.startswith('+') and telegram[1:].isdigit()):
                    try:
                        user.telegram_id = int(telegram.replace('+', ''))
                    except:
                        pass
                else:
                    user.telegram_username = telegram
            if user_data.get('city'):
                user.locations = [user_data['city']]
            db.flush()

        # Save locations from listing if provided separately
        if listing.locations and not (listing.user_data and listing.user_data.get('city')):
            user.locations = listing.locations
            db.flush()

        # Create listing
        db_listing = Listing(user_id=user_id)
        db.add(db_listing)
        db.flush()

        total_items = 0
        all_items_data = {'wants': {}, 'offers': {}}

        # Process wants
        if listing.wants:
            for category, items_list in listing.wants.items():
                if not items_list:
                    continue

                all_items_data['wants'][category] = []

                for item_data in items_list:
                    # Create ListingItem
                    list_item = ListingItem(
                        listing_id=db_listing.id,
                        item_type=ListingItemType.WANT,
                        category=item_data.category,
                        exchange_type=item_data.exchange_type,
                        item_name=item_data.item_name,
                        value_tenge=item_data.value_tenge,
                        duration_days=item_data.duration_days,
                        description=item_data.description
                    )
                    db.add(list_item)
                    total_items += 1

                    all_items_data['wants'][category].append({
                        "id": list_item.id,
                        "item_name": list_item.item_name,
                        "value_tenge": list_item.value_tenge,
                        "duration_days": list_item.duration_days,
                        "description": list_item.description
                    })

        # Process offers
        if listing.offers:
            for category, items_list in listing.offers.items():
                if not items_list:
                    continue

                all_items_data['offers'][category] = []

                for item_data in items_list:
                    # Create ListingItem
                    list_item = ListingItem(
                        listing_id=db_listing.id,
                        item_type=ListingItemType.OFFER,
                        category=item_data.category,
                        exchange_type=item_data.exchange_type,
                        item_name=item_data.item_name,
                        value_tenge=item_data.value_tenge,
                        duration_days=item_data.duration_days,
                        description=item_data.description
                    )
                    db.add(list_item)
                    total_items += 1

                    all_items_data['offers'][category].append({
                        "id": list_item.id,
                        "item_name": list_item.item_name,
                        "value_tenge": list_item.value_tenge,
                        "duration_days": list_item.duration_days,
                        "description": list_item.description
                    })

        db.commit()

        return {
            "listing_id": db_listing.id,
            "user_id": user_id,
            "items_created": total_items,
            "wants": all_items_data['wants'],
            "offers": all_items_data['offers'],
            "status": "success"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating listing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating listing: {str(e)}")


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
    2. Cross-category matching: ANY item can match with ANY other item of same exchange type
    3. Calculate equivalence score based on value (permanent) or daily rate (temporary)
    4. Apply language similarity bonus (30% weight)
    5. Create notifications for matches above 70% threshold
    6. Return matches sorted by combined score (70% equivalence + 30% language)

    Cross-category exchange means:
    - Phone (electronics) can exchange with Bike (transport)
    - Laptop (electronics) can exchange with Camera (photo equipment)
    - Any category ↔ Any other category, as long as values/daily rates match

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
                    # Allow cross-category matching - items from any category can exchange
                    # based on equivalent value/cost, not category restrictions
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
                    # Allow cross-category matching - items from any category can exchange
                    # based on equivalent value/cost, not category restrictions
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
                        user_id=other_user.id,
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
                            "explanation": match.get("explanation", ""),
                            # Add partner contact info
                            "partner_name": user.username,
                            "partner_telegram": user.telegram_username or f"+{user.telegram_id}" if user.telegram_id else None,
                            "partner_rating": round(user.trust_score, 2),
                            "partner_exchanges": len([r for r in user.ratings_received]) if hasattr(user, 'ratings_received') else 0
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
                        "partner_name": other_user.username,
                        "partner_telegram": other_user.telegram_username or f"+{other_user.telegram_id}" if other_user.telegram_id else None,
                        "partner_rating": round(other_user.trust_score, 2),
                        "partner_exchanges": len([r for r in other_user.ratings_received]) if hasattr(other_user, 'ratings_received') else 0,
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

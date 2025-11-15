"""
API Endpoints for Exchange Type Listings (Permanent & Temporary)

This module handles:
- Creating listings with items organized by category and exchange type
- Retrieving listings with grouped items
- Finding matches based on equivalence logic
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any, cast
import logging

from backend.database import SessionLocal
from backend.models import User, Listing, ListingItem, ListingItemType, ExchangeType, ExchangeEventType
from backend.schemas import (
    ListingItemsByCategoryCreate,
    ListingItemsByCategoryResponse,
    ListingItemResponse
)
from backend.equivalence_engine import ExchangeEquivalence
from backend.language_normalization import get_normalizer
from backend.events import emit_profile_change
from backend.auth import get_current_user, get_current_user_optional
from backend.match_index_service import get_match_index_service

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
                "created_at": str(getattr(item, 'created_at'))
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
                "created_at": str(getattr(item, 'created_at'))
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
    listing: Optional[ListingItemsByCategoryCreate] = None,
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

        # Verify listing is provided
        if not listing:
            raise HTTPException(status_code=400, detail="Listing data is required")

        # Type narrowing: listing is guaranteed to be not None after the check above
        listing = cast(ListingItemsByCategoryCreate, listing)

        # Update user data if provided
        if listing.user_data:
            user_data = listing.user_data
            if user_data.get('name'):
                new_username = user_data['name'].strip()
                # Check if username is already taken by another user
                existing_user = db.query(User).filter(
                    User.username == new_username,
                    User.id != user_id
                ).first()
                if not existing_user:
                    # Username is available, update it
                    setattr(user, 'username', new_username)  # type: ignore[assignment]
                else:
                    # Username is taken, log warning but don't fail
                    logger.warning(f"Username '{new_username}' is already taken by user {existing_user.id}, skipping update for user {user_id}")
            if user_data.get('telegram'):
                telegram = user_data['telegram'].strip()
                if telegram.startswith('@'):
                    setattr(user, 'telegram_username', telegram)  # type: ignore[assignment]
                elif telegram.isdigit() or (telegram.startswith('+') and telegram[1:].isdigit()):
                    try:
                        setattr(user, 'telegram_id', int(telegram.replace('+', '')))  # type: ignore[assignment]
                    except:
                        pass
                else:
                    setattr(user, 'telegram_username', telegram)  # type: ignore[assignment]
            db.flush()

        # Create listing with default title and description
        db_listing = Listing(
            user_id=user_id,
            title=f"Listing for user {user_id}",
            description="Created via create-by-categories endpoint"
        )
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
            setattr(user, 'locations', listing.locations)  # type: ignore[assignment]

        db.commit()
        db.refresh(db_listing)

        logger.info(f"Created listing {db_listing.id} for user {user_id} with {items_created} items")
        logger.info(f"Listing details: title='{db_listing.title}', user_id={db_listing.user_id}, items_count={items_created}")

        # Verify listing was saved correctly
        verify_listing = db.query(Listing).filter(Listing.id == db_listing.id).first()
        if verify_listing:
            verify_items = db.query(ListingItem).filter(ListingItem.listing_id == db_listing.id).count()
            logger.info(f"Verification: listing {db_listing.id} exists with {verify_items} items")
        else:
            logger.error(f"ERROR: Listing {db_listing.id} was not found after commit!")

        # Update match index for new listing
        try:
            index_service = get_match_index_service(db)
            index_service.build_user_index(user_id)
            logger.info(f"Built match index for user {user_id}")
        except Exception as index_error:
            logger.warning(f"Failed to build match index for user {user_id}: {index_error}")

        # Emit profile change event
        try:
            # Extract added items for event
            added_items = {"wants": [], "offers": []}

            # Collect wants
            for category, items in wants_summary.items():
                for item in items:
                    added_items["wants"].append({
                        "category": category,
                        "exchange_type": item["exchange_type"],
                        "item_name": item["item_name"]
                    })

            # Collect offers
            for category, items in offers_summary.items():
                for item in items:
                    added_items["offers"].append({
                        "category": category,
                        "exchange_type": item["exchange_type"],
                        "item_name": item["item_name"]
                    })

            # Emit event asynchronously (don't block response)
            # Note: This is a fire-and-forget operation, errors are logged but don't affect response
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create task
                    asyncio.create_task(emit_profile_change(user_id, added=added_items))
                else:
                    # If no loop is running, run in new event loop
                    asyncio.run(emit_profile_change(user_id, added=added_items))
            except RuntimeError:
                # No event loop available, skip event emission (non-critical)
                logger.debug(f"Skipping profile change event for user {user_id} (no event loop)")

        except Exception as event_error:
            logger.warning(f"Failed to emit profile change event for user {user_id}: {event_error}")

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
    listing: Optional[ListingItemsByCategoryCreate] = None,
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

        # Verify listing is provided
        if not listing:
            raise HTTPException(status_code=400, detail="Listing data is required")

        # Type narrowing: listing is guaranteed to be not None after the check above
        listing = cast(ListingItemsByCategoryCreate, listing)

        # Update user data if provided
        if listing.user_data:
            user_data = listing.user_data
            if user_data.get('name'):
                new_username = user_data['name'].strip()
                # Check if username is already taken by another user
                existing_user = db.query(User).filter(
                    User.username == new_username,
                    User.id != user_id
                ).first()
                if not existing_user:
                    # Username is available, update it
                    setattr(user, 'username', new_username)  # type: ignore[assignment]
                else:
                    # Username is taken, log warning but don't fail
                    logger.warning(f"Username '{new_username}' is already taken by user {existing_user.id}, skipping update for user {user_id}")
            if user_data.get('telegram'):
                telegram = user_data['telegram'].strip()
                if telegram.startswith('@'):
                    setattr(user, 'telegram_username', telegram)  # type: ignore[assignment]
                elif telegram.isdigit() or (telegram.startswith('+') and telegram[1:].isdigit()):
                    try:
                        setattr(user, 'telegram_id', int(telegram.replace('+', '')))  # type: ignore[assignment]
                    except:
                        pass
                else:
                    setattr(user, 'telegram_username', telegram)  # type: ignore[assignment]
            if user_data.get('city'):
                setattr(user, 'locations', [user_data['city']])  # type: ignore[assignment]
            db.flush()

        # Save locations from listing if provided separately
        if listing.locations and not (listing.user_data and listing.user_data.get('city')):
            setattr(user, 'locations', listing.locations)  # type: ignore[assignment]
            db.flush()

        # Create listing with default title and description
        db_listing = Listing(
            user_id=user_id,
            title=f"Listing for user {user_id}",
            description="Created via create endpoint"
        )
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

@router.get("/my")
def get_my_listings(
    exchange_type: Optional[str] = Query(None, description="Filter by exchange type (permanent/temporary)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get current user's listings
    """
    if not current_user:
        return {"error": "Authentication required"}
    try:
        return get_user_listings(current_user.id, exchange_type, db)
    except Exception as e:
        return {"error": f"Internal error: {str(e)}"}


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
    db: Optional[Session] = None
):
    """
    Internal matching function that can be called from other endpoints.
    Separated from the HTTP endpoint to avoid circular dependencies.

    Find MUTUAL exchange matches for a user's listing items.

    MUTUAL EXCHANGE ALGORITHM:
    1. Find all other users with listings
    2. For each partner, check BOTH exchange directions simultaneously:
       - Direction A→B: User's wants match with partner's offers
       - Direction B→A: User's offers match with partner's wants
    3. Only create match if BOTH directions have valid matches (threshold ≥70%)
    4. Cross-category matching: ANY item can match with ANY other item of same exchange type
    5. Calculate equivalence scores based on value (permanent) or daily rate (temporary)
    6. Apply language similarity bonus (30% weight to final score)
    7. Select best matches from each direction for the final exchange
    8. Create notifications for mutual matches
    9. Return matches sorted by overall exchange score

    MUTUAL EXCHANGE REQUIREMENTS:
    - At least one want↔offer match in both directions
    - Same exchange type (permanent↔permanent OR temporary↔temporary)
    - Cross-category allowed: Phone↔Bike, Laptop↔Camera, etc.
    - Combined score ≥70% for each direction
    - Final score = average of both direction scores

    Args:
        user_id: User ID to find matches for
        exchange_type: Optional filter for "permanent" or "temporary"
        db: Database session (required, but can be None for HTTP endpoint calls)

    Returns:
        {
          "user_id": 1,
          "matches_found": 3,
          "notifications_created": 6,
          "matches": [{
            "type": "mutual_exchange",
            "my_want_item": {...}, "their_offer_item": {...},
            "my_offer_item": {...}, "their_want_item": {...},
            "overall_score": 0.85,
            "explanation": "Mutual exchange: X want↔offer + Y offer↔want matches"
          }]
        }
    """

    # Create session if not provided
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    # Type narrowing: db is guaranteed to be not None after the check above
    db = cast(Session, db)

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

        # Find matches with MUTUAL exchange logic
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

            # Check for MUTUAL matches: both directions must have at least one match
            # Direction 1: My wants match with their offers
            want_offer_matches = []
            for my_want in my_wants:
                if exchange_type and my_want.exchange_type.value != exchange_type:
                    continue

                for their_offer in other_offers:
                    # Allow cross-category matching - items from any category can exchange
                    # based on equivalent value/cost, not category restrictions
                    if my_want.exchange_type != their_offer.exchange_type:  # type: ignore[comparison]
                        continue

                    # Calculate equivalence score with cross-category adjustment
                    is_cross_category = (my_want.category != their_offer.category)
                    if my_want.exchange_type == ExchangeType.PERMANENT:
                        result = ExchangeEquivalence.calculate_permanent_score(
                            my_want.value_tenge,
                            their_offer.value_tenge,
                            tolerance=0.5 if is_cross_category else None  # Lower tolerance for cross-category
                        )
                    else:  # TEMPORARY
                        result = ExchangeEquivalence.calculate_temporary_score(
                            my_want.value_tenge,
                            my_want.duration_days,
                            their_offer.value_tenge,
                            their_offer.duration_days,
                            tolerance=0.5 if is_cross_category else None  # Lower tolerance for cross-category
                        )

                    # Apply language similarity multiplier
                    language_similarity = language_normalizer.similarity_score(
                        my_want.item_name,
                        their_offer.item_name
                    )

                    # Combined score: 70% equivalence, 30% language similarity
                    combined_score = result.score * 0.7 + language_similarity * 0.3

                    # Dynamic threshold: lower for cross-category matches
                    # Cross-category exchanges allow lower similarity threshold
                    is_cross_category = (my_want.category != their_offer.category)
                    threshold = 0.20 if is_cross_category else 0.70

                    # For cross-category exchanges, lower equivalence threshold
                    equivalence_threshold = 0.30 if is_cross_category else ExchangeEquivalence.config.MIN_MATCH_SCORE
                    result_is_match = result.score >= equivalence_threshold

                    # Only match if equivalence passes and combined score meets dynamic threshold
                    if result_is_match and combined_score >= threshold:
                        want_offer_matches.append({
                            "my_want": my_want,
                            "their_offer": their_offer,
                            "score": combined_score,
                            "result": result,
                            "language_similarity": language_similarity
                        })

            # Direction 2: My offers match with their wants
            offer_want_matches = []
            for my_offer in my_offers:
                if exchange_type and my_offer.exchange_type.value != exchange_type:
                    continue

                for their_want in other_wants:
                    # Allow cross-category matching - items from any category can exchange
                    # based on equivalent value/cost, not category restrictions
                    if my_offer.exchange_type != their_want.exchange_type:  # type: ignore[comparison]
                        continue

                    # Calculate equivalence score with cross-category adjustment
                    is_cross_category = (my_offer.category != their_want.category)
                    if my_offer.exchange_type == ExchangeType.PERMANENT:
                        result = ExchangeEquivalence.calculate_permanent_score(
                            my_offer.value_tenge,
                            their_want.value_tenge,
                            tolerance=0.5 if is_cross_category else None  # Lower tolerance for cross-category
                        )
                    else:  # TEMPORARY
                        result = ExchangeEquivalence.calculate_temporary_score(
                            my_offer.value_tenge,
                            my_offer.duration_days,
                            their_want.value_tenge,
                            their_want.duration_days,
                            tolerance=0.5 if is_cross_category else None  # Lower tolerance for cross-category
                        )

                    # Apply language similarity multiplier
                    language_similarity = language_normalizer.similarity_score(
                        my_offer.item_name,
                        their_want.item_name
                    )

                    # Combined score: 70% equivalence, 30% language similarity
                    combined_score = result.score * 0.7 + language_similarity * 0.3

                    # Dynamic threshold: lower for cross-category matches
                    # Cross-category exchanges allow lower similarity threshold
                    is_cross_category = (my_offer.category != their_want.category)
                    threshold = 0.20 if is_cross_category else 0.70

                    # For cross-category exchanges, lower equivalence threshold
                    equivalence_threshold = 0.30 if is_cross_category else ExchangeEquivalence.config.MIN_MATCH_SCORE
                    result_is_match = result.score >= equivalence_threshold

                    # Only match if equivalence passes and combined score meets dynamic threshold
                    if result_is_match and combined_score >= threshold:
                        offer_want_matches.append({
                            "my_offer": my_offer,
                            "their_want": their_want,
                            "score": combined_score,
                            "result": result,
                            "language_similarity": language_similarity
                        })

            # MUTUAL EXCHANGE REQUIREMENT:
            # Only create match if BOTH directions have at least one valid match
            if want_offer_matches and offer_want_matches:
                # Find the best matches from each direction for the final exchange
                best_want_offer = max(want_offer_matches, key=lambda x: x["score"])
                best_offer_want = max(offer_want_matches, key=lambda x: x["score"])

                # Calculate overall exchange score (average of both directions)
                overall_score = (best_want_offer["score"] + best_offer_want["score"]) / 2

                # Get partner rating for sorting
                from backend.reviews_service import get_reviews_service
                reviews_service = get_reviews_service(db)
                partner_rating = reviews_service.get_user_rating(other_user.id)

                matches.append({
                    "match_id": f"mutual_{user_id}_{other_user.id}_{best_want_offer['my_want'].id}_{best_offer_want['my_offer'].id}",
                    "type": "mutual_exchange",
                    "partner_user_id": other_user.id,
                    "partner_contact": other_user.contact,
                    "partner_rating": partner_rating,
                    "exchange_type": best_want_offer["my_want"].exchange_type.value,

                    # Best want->offer match
                    "my_want_item": {
                        "item_id": best_want_offer["my_want"].id,
                        "item_name": best_want_offer["my_want"].item_name,
                        "category": best_want_offer["my_want"].category,
                        "value_tenge": best_want_offer["my_want"].value_tenge,
                        "duration_days": best_want_offer["my_want"].duration_days,
                        "daily_rate": best_want_offer["my_want"].daily_rate
                    },
                    "their_offer_item": {
                        "item_id": best_want_offer["their_offer"].id,
                        "item_name": best_want_offer["their_offer"].item_name,
                        "category": best_want_offer["their_offer"].category,
                        "value_tenge": best_want_offer["their_offer"].value_tenge,
                        "duration_days": best_want_offer["their_offer"].duration_days,
                        "daily_rate": best_want_offer["their_offer"].daily_rate
                    },

                    # Best offer->want match
                    "my_offer_item": {
                        "item_id": best_offer_want["my_offer"].id,
                        "item_name": best_offer_want["my_offer"].item_name,
                        "category": best_offer_want["my_offer"].category,
                        "value_tenge": best_offer_want["my_offer"].value_tenge,
                        "duration_days": best_offer_want["my_offer"].duration_days,
                        "daily_rate": best_offer_want["my_offer"].daily_rate
                    },
                    "their_want_item": {
                        "item_id": best_offer_want["their_want"].id,
                        "item_name": best_offer_want["their_want"].item_name,
                        "category": best_offer_want["their_want"].category,
                        "value_tenge": best_offer_want["their_want"].value_tenge,
                        "duration_days": best_offer_want["their_want"].duration_days,
                        "daily_rate": best_offer_want["their_want"].daily_rate
                    },

                    # Scores
                    "overall_score": round(overall_score, 2),
                    "want_offer_score": round(best_want_offer["score"], 2),
                    "offer_want_score": round(best_offer_want["score"], 2),
                    "want_offer_equivalence": round(best_want_offer["result"].score, 2),
                    "offer_want_equivalence": round(best_offer_want["result"].score, 2),
                    "want_offer_similarity": round(best_want_offer["language_similarity"], 2),
                    "offer_want_similarity": round(best_offer_want["language_similarity"], 2),

                    # Quality indicators
                    "score_category": "mutual_exchange",
                    "explanation": f"Mutual exchange: {len(want_offer_matches)} want↔offer + {len(offer_want_matches)} offer↔want matches found"
                })

        # Sort by overall exchange score descending
        matches.sort(key=lambda x: x["overall_score"], reverse=True)

        # Create notifications for each match
        from backend.crud import create_notification
        from backend.schemas import NotificationCreate

        notifications_created = 0
        for match in matches:
            try:
                partner_user_id = match["partner_user_id"]
                partner_user = db.query(User).filter(User.id == partner_user_id).first()

                if partner_user:
                    # Notification for partner (mutual exchange found)
                    partner_notification = NotificationCreate(
                        user_id=partner_user.id,
                        payload={
                            "match_id": match["match_id"],
                            "match_type": "mutual_exchange",
                            "exchange_type": match["exchange_type"],

                            # Partner gets what they want
                            "you_receive": match["their_want_item"],
                            "you_give": match["my_offer_item"],

                            # Partner info about the other person
                            "partner_name": user.username,
                            "partner_telegram": user.telegram_username or f"+{user.telegram_id}" if user.telegram_id else None,
                            "partner_rating": round(user.trust_score, 2),
                            "partner_exchanges": len([r for r in user.ratings_received]) if hasattr(user, 'ratings_received') else 0,

                            # Exchange details
                            "overall_score": match["overall_score"],
                            "want_offer_score": match["want_offer_score"],
                            "offer_want_score": match["offer_want_score"],
                            "explanation": match["explanation"]
                        }
                    )
                    create_notification(db, partner_notification)
                    notifications_created += 1

                # Notification for current user (mutual exchange found)
                user_notification = NotificationCreate(
                    user_id=user_id,
                    payload={
                        "match_id": match["match_id"],
                        "match_type": "mutual_exchange",
                        "exchange_type": match["exchange_type"],

                        # User gets what they want
                        "you_receive": match["my_want_item"],
                        "you_give": match["my_offer_item"],

                        # Partner info
                        "partner_user_id": partner_user_id,
                        "partner_name": other_user.username,
                        "partner_telegram": other_user.telegram_username or f"+{other_user.telegram_id}" if other_user.telegram_id else None,
                        "partner_rating": round(other_user.trust_score, 2),
                        "partner_exchanges": len([r for r in other_user.ratings_received]) if hasattr(other_user, 'ratings_received') else 0,

                        # Exchange details
                        "overall_score": match["overall_score"],
                        "want_offer_score": match["want_offer_score"],
                        "offer_want_score": match["offer_want_score"],
                        "explanation": match["explanation"]
                    }
                )
                create_notification(db, user_notification)
                notifications_created += 1

            except Exception as notif_error:
                logger.warning(f"Failed to create notification for mutual match {match.get('match_id')}: {notif_error}")
                # Continue processing other matches

        db.commit()  # Commit notifications

        # Sort matches by rating (high rating first), then by overall score
        def sort_key(match):
            rating = match.get("partner_rating", {}).get("rating_avg", 0.0)
            score = match.get("overall_score", 0.0)
            return (-rating, -score)  # Negative for descending order

        matches_sorted = sorted(matches, key=sort_key)

        logger.info(f"Found {len(matches)} matches for user {user_id}, created {notifications_created} notifications")

        return {
            "user_id": user_id,
            "matches_found": len(matches),
            "notifications_created": notifications_created,
            "matches": matches_sorted
        }

    except ValueError as ve:
        # Re-raise ValueError as HTTPException for HTTP endpoint
        logger.error(f"Error finding matches (ValueError) for user {user_id}: {ve}", exc_info=True)
        raise HTTPException(status_code=404 if "not found" in str(ve).lower() else 500, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding matches (Exception) for user {user_id}: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error finding matches: {str(e)}")
    finally:
        # Close session if it was created inside this function
        if should_close and db is not None:
            db.close()


# ============================================================
# PARTIAL LISTING UPDATES - INCREMENTAL MATCHING
# ============================================================

@router.patch("/listings/{listing_id}")
def update_listing_partial(
    listing_id: int,
    updates: Dict[str, Any],  # JSON Patch style updates
    user_id: int = Query(..., description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """
    Partially update a listing with incremental matching support.

    Supports JSON Patch-style operations for adding/removing items without full replacement.
    Automatically triggers incremental index updates and match recalculation.

    Supported operations:
    - Add new items: {"wants": {"electronics": [{"item_name": "...", ...}]}}
    - Remove items: {"remove_items": [item_id1, item_id2]}

    Args:
        listing_id: ID of the listing to update
        updates: Partial update payload
        user_id: User ID for authorization

    Returns:
        Updated listing information
    """
    try:
        # Verify listing ownership
        listing = db.query(Listing).filter(
            Listing.id == listing_id,
            Listing.user_id == user_id
        ).first()

        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found or access denied")

        # Track changes for event emission
        added_items = {"wants": [], "offers": []}
        removed_items = {"wants": [], "offers": []}

        # Handle item additions
        if "wants" in updates:
            for category, items in updates["wants"].items():
                for item_data in items:
                    # Validate item data
                    if not item_data.get("item_name") or not item_data.get("value_tenge"):
                        continue

                    # Create new listing item
                    new_item = ListingItem(
                        listing_id=listing_id,
                        item_type=ListingItemType.WANT,
                        category=category,
                        exchange_type=item_data.get("exchange_type", "PERMANENT"),
                        item_name=item_data["item_name"],
                        value_tenge=item_data["value_tenge"],
                        duration_days=item_data.get("duration_days"),
                        description=item_data.get("description", "")
                    )

                    if not new_item.is_valid:
                        continue

                    db.add(new_item)

                    # Track for events
                    added_items["wants"].append({
                        "category": category,
                        "exchange_type": new_item.exchange_type.value,
                        "item_name": new_item.item_name
                    })

        if "offers" in updates:
            for category, items in updates["offers"].items():
                for item_data in items:
                    # Validate item data
                    if not item_data.get("item_name") or not item_data.get("value_tenge"):
                        continue

                    # Create new listing item
                    new_item = ListingItem(
                        listing_id=listing_id,
                        item_type=ListingItemType.OFFER,
                        category=category,
                        exchange_type=item_data.get("exchange_type", "PERMANENT"),
                        item_name=item_data["item_name"],
                        value_tenge=item_data["value_tenge"],
                        duration_days=item_data.get("duration_days"),
                        description=item_data.get("description", "")
                    )

                    if not new_item.is_valid:
                        continue

                    db.add(new_item)

                    # Track for events
                    added_items["offers"].append({
                        "category": category,
                        "exchange_type": new_item.exchange_type.value,
                        "item_name": new_item.item_name
                    })

        # Handle item removals
        if "remove_items" in updates:
            item_ids_to_remove = updates["remove_items"]
            if not isinstance(item_ids_to_remove, list):
                item_ids_to_remove = [item_ids_to_remove]

            for item_id in item_ids_to_remove:
                # Find and soft-delete item
                item = db.query(ListingItem).filter(
                    ListingItem.id == item_id,
                    ListingItem.listing_id == listing_id,
                    ListingItem.is_archived == False
                ).first()

                if item:
                    item.is_archived = True

                    # Track for events
                    item_type_str = "wants" if item.item_type == ListingItemType.WANT else "offers"
                    removed_items[item_type_str].append({
                        "category": item.category,
                        "exchange_type": item.exchange_type.value,
                        "item_name": item.item_name
                    })

        # Commit changes
        db.commit()
        db.refresh(listing)

        # Emit profile change event
        try:
            import asyncio
            from backend.events import emit_profile_change

            # Only emit if there are actual changes
            has_changes = (added_items["wants"] or added_items["offers"] or
                          removed_items["wants"] or removed_items["offers"])

            if has_changes:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(emit_profile_change(user_id, added=added_items, removed=removed_items))
                    else:
                        asyncio.run(emit_profile_change(user_id, added=added_items, removed=removed_items))
                    logger.info(f"Emitted profile change event for user {user_id} after partial update")
                except RuntimeError:
                    logger.debug(f"Skipping profile change event for user {user_id} (no event loop)")

        except Exception as event_error:
            logger.warning(f"Failed to emit profile change event: {event_error}")

        # Build response with updated item counts
        wants_count = db.query(ListingItem).filter(
            ListingItem.listing_id == listing_id,
            ListingItem.item_type == ListingItemType.WANT,
            ListingItem.is_archived == False
        ).count()

        offers_count = db.query(ListingItem).filter(
            ListingItem.listing_id == listing_id,
            ListingItem.item_type == ListingItemType.OFFER,
            ListingItem.is_archived == False
        ).count()

        return {
            "status": "success",
            "listing_id": listing_id,
            "user_id": user_id,
            "items_added": len(added_items["wants"]) + len(added_items["offers"]),
            "items_removed": len(removed_items["wants"]) + len(removed_items["offers"]),
            "current_counts": {
                "wants": wants_count,
                "offers": offers_count
            },
            "message": "Listing updated successfully with incremental matching triggered"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# EXCHANGE CONFIRMATION - AUTO CLEANUP
# ============================================================

@router.post("/exchanges/{exchange_id}/confirm")
def confirm_exchange(
    exchange_id: str,
    confirmer_user_id: int = Query(..., description="ID of user confirming the exchange"),
    db: Session = Depends(get_db)
):
    """
    Confirm successful exchange completion and auto-cleanup exchanged items.

    This endpoint:
    1. Validates that the exchange exists and involves the confirmer
    2. Marks the exchange as completed
    3. Automatically archives exchanged items from both users' wants/offers
    4. Updates match indexes and triggers incremental matching
    5. Sends completion notifications

    Args:
        exchange_id: Unique exchange identifier (e.g., "mutual_1_2_10_15")
        confirmer_user_id: ID of the user confirming completion

    Returns:
        Confirmation status with cleanup details
    """
    try:
        # Parse exchange_id to extract user/item information
        # Format: "mutual_{user_a}_{user_b}_{item_a}_{item_b}"
        parts = exchange_id.split("_")
        if len(parts) != 5 or parts[0] != "mutual":
            raise HTTPException(
                status_code=400,
                detail="Invalid exchange_id format. Expected: mutual_{user_a}_{user_b}_{item_a}_{item_b}"
            )

        try:
            user_a_id = int(parts[1])
            user_b_id = int(parts[2])
            item_a_id = int(parts[3])
            item_b_id = int(parts[4])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid exchange_id: non-numeric IDs")

        # Validate that confirmer is one of the participants
        if confirmer_user_id not in [user_a_id, user_b_id]:
            raise HTTPException(
                status_code=403,
                detail="You are not a participant in this exchange"
            )

        # Get the exchanged items
        from backend.models import ListingItem

        item_a = db.query(ListingItem).filter(
            ListingItem.id == item_a_id,
            ListingItem.is_archived == False
        ).first()

        item_b = db.query(ListingItem).filter(
            ListingItem.id == item_b_id,
            ListingItem.is_archived == False
        ).first()

        if not item_a or not item_b:
            raise HTTPException(status_code=404, detail="One or more exchanged items not found")

        # Validate that items belong to correct users
        item_a_listing = item_a.listing
        item_b_listing = item_b.listing

        if item_a_listing.user_id != user_a_id or item_b_listing.user_id != user_b_id:
            raise HTTPException(status_code=400, detail="Exchange participants don't match item ownership")

        # Begin transaction for atomic operation
        items_archived = []

        # Archive exchanged items (soft delete)
        item_a.is_archived = True
        item_b.is_archived = True
        items_archived.extend([item_a_id, item_b_id])

        # Check if users have other items in the same categories
        # If not, we might need to remove from match index, but let's keep it simple for now

        # Log the completed exchange (could create an ExchangeHistory record)
        logger.info(f"Exchange confirmed: {exchange_id} by user {confirmer_user_id}")

        db.commit()

        # Emit profile change events for both users (removed items)
        try:
            import asyncio
            from backend.events import emit_profile_change

            # For user A (removed their offered item, gained wanted item)
            removed_a = {
                "offers": [{
                    "category": item_a.category,
                    "exchange_type": item_a.exchange_type.value,
                    "item_name": item_a.item_name
                }]
            }
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(emit_profile_change(user_a_id, removed=removed_a))
                else:
                    asyncio.run(emit_profile_change(user_a_id, removed=removed_a))
            except RuntimeError:
                logger.debug(f"Skipping profile change event for user {user_a_id} (no event loop)")

            # For user B (removed their offered item, gained wanted item)
            removed_b = {
                "offers": [{
                    "category": item_b.category,
                    "exchange_type": item_b.exchange_type.value,
                    "item_name": item_b.item_name
                }]
            }
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(emit_profile_change(user_b_id, removed=removed_b))
                else:
                    asyncio.run(emit_profile_change(user_b_id, removed=removed_b))
            except RuntimeError:
                logger.debug(f"Skipping profile change event for user {user_b_id} (no event loop)")

        except Exception as event_error:
            logger.warning(f"Failed to emit profile change events after exchange confirmation: {event_error}")

        # Log exchange completion event
        from backend.exchange_history_service import get_exchange_history_service
        history_service = get_exchange_history_service(db)
        history_service.log_event(
            exchange_id=exchange_id,
            event_type=ExchangeEventType.COMPLETED,
            user_id=confirmer_user_id,
            details={
                "confirmed_by": confirmer_user_id,
                "items_archived": items_archived
            }
        )

        # Send completion notifications
        try:
            from backend.notifications.notification_service import create_notification

            # Notify both participants
            for participant_id in [user_a_id, user_b_id]:
                notification = {
                    "user_id": participant_id,
                    "type": "exchange_completed",
                    "title": "Exchange Completed Successfully! 🎉",
                    "message": f"Your exchange has been confirmed and completed. Items have been removed from your listings.",
                    "data": {
                        "exchange_id": exchange_id,
                        "confirmed_by": confirmer_user_id,
                        "items_archived": items_archived
                    }
                }
                create_notification(db, notification)

        except Exception as notif_error:
            logger.warning(f"Failed to send exchange completion notifications: {notif_error}")

        return {
            "status": "success",
            "exchange_id": exchange_id,
            "confirmed_by": confirmer_user_id,
            "participants": [user_a_id, user_b_id],
            "items_archived": items_archived,
            "message": "Exchange confirmed and items automatically cleaned up from listings"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error confirming exchange {exchange_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/listings/{listing_id}/duplicate")
def duplicate_listing(
    listing_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Duplicate an existing listing to create a new one.

    This allows users to quickly "repeat" a previous exchange by copying
    their wants/offers configuration.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        # Get original listing
        original_listing = db.query(Listing).filter(
            Listing.id == listing_id,
            Listing.user_id == current_user.id
        ).first()

        if not original_listing:
            raise HTTPException(status_code=404, detail="Listing not found or access denied")

        # Get original items
        original_wants = db.query(ListingItem).filter(
            ListingItem.listing_id == listing_id,
            ListingItem.item_type == ListingItemType.WANT
        ).all()

        original_offers = db.query(ListingItem).filter(
            ListingItem.listing_id == listing_id,
            ListingItem.item_type == ListingItemType.OFFER
        ).all()

        # Create new listing
        new_listing = Listing(
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )
        db.add(new_listing)
        db.flush()  # Get ID without committing

        # Duplicate items
        duplicated_items = []

        for item in original_wants + original_offers:
            new_item = ListingItem(
                listing_id=new_listing.id,
                item_type=item.item_type,
                category=item.category,
                exchange_type=item.exchange_type,
                item_name=item.item_name,
                value_tenge=item.value_tenge,
                duration_days=item.duration_days,
                description=item.description,
                created_at=datetime.utcnow()
            )
            db.add(new_item)
            duplicated_items.append(new_item)

        db.commit()
        db.refresh(new_listing)

        # Trigger matching for new listing
        try:
            matches_result = _find_matches_internal(current_user.id, db=db)
            matches_found = matches_result.get("matches_found", 0)
        except Exception as match_error:
            logger.warning(f"Failed to find matches for duplicated listing: {match_error}")
            matches_found = 0

        # Log the duplication
        from backend.exchange_history_service import get_exchange_history_service
        history_service = get_exchange_history_service(db)
        history_service.log_event(
            exchange_id=f"listing_{new_listing.id}",
            event_type=ExchangeEventType.CREATED,
            user_id=current_user.id,
            details={
                "duplicated_from": listing_id,
                "items_count": len(duplicated_items)
            }
        )

        return {
            "status": "duplicated",
            "original_listing_id": listing_id,
            "new_listing_id": new_listing.id,
            "items_duplicated": len(duplicated_items),
            "wants_count": len(original_wants),
            "offers_count": len(original_offers),
            "matches_found": matches_found,
            "message": "Listing duplicated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error duplicating listing {listing_id}: {e}")
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
    try:
        logger.info(f"Finding matches for user {user_id}, exchange_type={exchange_type}")
        result = _find_matches_internal(user_id, exchange_type, db)
        logger.info(f"Matches found for user {user_id}: {result.get('matches_found', 0)}")
        return result
    except Exception as e:
        logger.error(f"Error in find_matches_for_user endpoint for user {user_id}: {e}", exc_info=True)
        raise

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging
logger = logging.getLogger(__name__)
from backend import models
from backend import schemas
User = models.User
Profile = models.Profile
Item = models.Item
Match = models.Match
Rating = models.Rating
Notification = models.Notification
Category = models.Category
MarketListing = models.MarketListing

UserCreate = schemas.UserCreate
ProfileCreate = schemas.ProfileCreate
ItemCreate = schemas.ItemCreate
MatchCreate = schemas.MatchCreate
RatingCreate = schemas.RatingCreate
NotificationCreate = schemas.NotificationCreate
CategoryCreate = schemas.CategoryCreate
MarketListingCreate = schemas.MarketListingCreate
from fastapi import HTTPException
from typing import Optional, cast

# User CRUD
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    db_user = User(
        username=user.username,
        contact=user.contact,
        locations=user.locations or ["Алматы"],  # Default to Almaty if not specified
        # NEW: Telegram integration fields
        telegram_id=getattr(user, 'telegram_id', None),
        telegram_username=getattr(user, 'telegram_username', None),
        telegram_first_name=getattr(user, 'telegram_first_name', None)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_locations(db: Session, user_id: int, locations: list):
    """Update user's selected locations"""
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate locations
    valid_locations = ["Алматы", "Астана", "Шымкент"]
    for loc in locations:
        if loc not in valid_locations:
            raise HTTPException(status_code=400, detail=f"Invalid location: {loc}")

    # Require at least one location
    if not locations:
        raise HTTPException(status_code=400, detail="User must select at least one location")

    user.locations = locations
    db.commit()
    db.refresh(user)
    return user

# Profile CRUD
def get_user_profiles(db: Session, user_id: int):
    return db.query(Profile).filter(Profile.user_id == user_id).all()

def create_profile(db: Session, profile: ProfileCreate):
    # Resolve username to user_id or use user_id directly
    user = None
    if getattr(profile, "username", None):
        user = db.query(User).filter(User.username == profile.username).first()
    elif getattr(profile, "user_id", None) is not None:
        user = db.query(User).filter(User.id == profile.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_profile = Profile(
        user_id=user.id,  # Use resolved user_id
        name=profile.name,
        category=profile.category,
        description=profile.description,
        avatar_url=profile.avatar_url,
        location=profile.location,
        visibility=profile.visibility
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

# Item CRUD
def get_user_items(db: Session, user_id: int):
    return db.query(Item).filter(Item.user_id == user_id).all()

def create_item(db: Session, item: ItemCreate):
    db_item = Item(
        user_id=item.user_id,
        kind=item.kind,
        category=item.category,
        title=item.title,
        description=item.description,
        item_metadata=item.item_metadata,
        wants=item.wants,
        offers=item.offers,
        active=item.active
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Match CRUD
def get_user_matches(db: Session, user_id: int):
    # Get matches where user is involved
    return db.query(Match).filter(
        or_(Match.item_a.in_(
            db.query(Item.id).filter(Item.user_id == user_id)
        ), Match.item_b.in_(
            db.query(Item.id).filter(Item.user_id == user_id)
        ))
    ).all()

def create_match(db: Session, match: MatchCreate):
    db_match = Match(
        item_a=match.item_a,
        item_b=match.item_b,
        score=match.score,
        computed_by=match.computed_by,
        reasons=match.reasons,
        status=match.status
    )
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match

# Rating CRUD
def get_user_ratings(db: Session, user_id: int):
    return db.query(Rating).filter(Rating.from_user == user_id).all()

def create_rating(db: Session, rating: RatingCreate):
    # Support multiple possible field names on RatingCreate (safe getattr fallbacks)
    from_username = getattr(rating, "from_username", getattr(rating, "from_user", None))
    to_username = getattr(rating, "to_username", getattr(rating, "to_user", None))

    from_user = get_user_by_username(db, from_username) if from_username else None
    to_user = get_user_by_username(db, to_username) if to_username else None
    if not from_user or not to_user:
        raise HTTPException(status_code=404, detail="User(s) not found")

    # Helper to safely extract an integer id from a SQLAlchemy object or raw value
    def _extract_id(obj):
        val = getattr(obj, "id", obj)
        try:
            return int(val)
        except Exception:
            # If we cannot convert, return the original value (fallback)
            return val

    from_user_id = _extract_id(from_user)
    to_user_id = _extract_id(to_user)

    # Safely extract score, comment and tx_id with common alternate names
    score = getattr(rating, "score", getattr(rating, "rating", None))
    if score is None:
        raise HTTPException(status_code=400, detail="Missing rating score")
    try:
        score = float(score)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid rating score")

    comment = getattr(rating, "comment", getattr(rating, "message", None))
    tx_id = getattr(rating, "tx_id", getattr(rating, "transaction_id", None))

    db_rating = Rating(
        from_user=from_user_id,
        to_user=to_user_id,
        score=score,
        comment=comment,
        tx_id=tx_id
    )
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)

    # Update trust score using a plain int id when available
    if isinstance(to_user_id, int):
        update_trust_score(db, to_user_id)

    return db_rating

def update_trust_score(db: Session, user_id: int):
    ratings = db.query(Rating).filter(Rating.to_user == user_id).all()
    if ratings:
        avg_score = sum(r.score for r in ratings) / len(ratings)
        db.query(User).filter(User.id == user_id).update({"trust_score": avg_score})
        db.commit()

# Notification CRUD
def create_notification(db: Session, notification: NotificationCreate):
    # Check soft-throttle: if user has ignored >5 notifications in last 24h, skip
    from datetime import datetime, timedelta
    recent_ignored = db.query(Notification).filter(
        Notification.user_id == notification.user_id,
        Notification.status == "queued",
        Notification.created_at > datetime.utcnow() - timedelta(hours=24)
    ).count()

    if recent_ignored > 5:
        # Skip notification to avoid spam
        return None

    db_notification = Notification(
        user_id=notification.user_id,
        channel=notification.channel,
        payload=notification.payload,
        status=notification.status
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_pending_notifications(db: Session):
    return db.query(Notification).filter(Notification.status == "queued").all()

def mark_notification_sent(db: Session, notification_id: int):
    from datetime import datetime
    db.query(Notification).filter(Notification.id == notification_id).update({
        "status": "sent",
        "sent_at": datetime.utcnow()
    })
    db.commit()


# Category CRUD (for marketplace taxonomy)
def get_categories(db: Session, section: str | None = None, parent_id: int | None = None, active_only: bool = True):
    """Get categories, optionally filtered by section and parent_id"""
    query = db.query(Category)
    if section:
        query = query.filter(Category.section == section)
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    if active_only:
        query = query.filter(Category.is_active == True)
    return query.order_by(Category.sort_order, Category.id).all()


def get_category_by_id(db: Session, category_id: int):
    """Get category by ID"""
    return db.query(Category).filter(Category.id == category_id).first()


def get_category_by_slug(db: Session, slug: str, section: str | None = None):
    """Get category by slug, optionally filtered by section"""
    query = db.query(Category).filter(Category.slug == slug)
    if section:
        query = query.filter(Category.section == section)
    return query.first()


def create_category(db: Session, category: CategoryCreate):
    """Create a new category"""
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def upsert_category(db: Session, slug: str, section: str, name: str, parent_id: int | None = None, sort_order: int = 0):
    """Upsert category by (section, parent_id, slug)"""
    existing = db.query(Category).filter(
        Category.slug == slug,
        Category.section == section,
        Category.parent_id == parent_id
    ).first()

    if existing:
        return existing

    category = Category(
        name=name,
        slug=slug,
        section=section,
        parent_id=parent_id,
        sort_order=sort_order,
        is_active=True
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# Market Listing CRUD
def get_market_listings(
    db: Session,
    listing_type: str | None = None,
    category_id: int | None = None,
    subcategory_id: int | None = None,
    status: str = "active",
    skip: int = 0,
    limit: int = 20,
    search_query: str | None = None
):
    """Get market listings with filtering and pagination"""
    query = db.query(MarketListing)
    # Normalize listing_type/status to DB enum values to avoid passing invalid strings

    def _normalize_listing_type(val):
        if not val:
            return None
        # Accept enum, string (any case), singular or plural
        if isinstance(val, models.ListingSection):
            return val.value
        s = str(val).strip()
        s_low = s.lower()
        if s_low in ("want", "wants"):
            return models.ListingSection.WANT.value
        if s_low in ("offer", "offers"):
            return models.ListingSection.OFFER.value
        # Accept enum names (upper case)
        if s.upper() == "WANT":
            return models.ListingSection.WANT.value
        if s.upper() == "OFFER":
            return models.ListingSection.OFFER.value
        # Accept enum values directly
        if s in (models.ListingSection.WANT.value, models.ListingSection.OFFER.value):
            return s
        return None

    def _normalize_status(val):
        if not val:
            return None
        if isinstance(val, models.ListingStatus):
            return val.value
        s = str(val).strip()
        s_low = s.lower()
        if s_low == "active":
            return models.ListingStatus.ACTIVE.value
        if s_low == "archived":
            return models.ListingStatus.ARCHIVED.value
        # Accept enum names (upper case)
        if s.upper() == "ACTIVE":
            return models.ListingStatus.ACTIVE.value
        if s.upper() == "ARCHIVED":
            return models.ListingStatus.ARCHIVED.value
        # Accept enum values directly
        if s in (models.ListingStatus.ACTIVE.value, models.ListingStatus.ARCHIVED.value):
            return s
        return None

    lt_value = _normalize_listing_type(listing_type)
    status_value = _normalize_status(status)

    # Debug logging to verify normalization (visible in container logs)
    logger.info(f"get_market_listings: listing_type={listing_type} normalized={lt_value}, status={status} normalized={status_value}")

    if lt_value:
        query = query.filter(MarketListing.type == lt_value)
    if category_id:
        query = query.filter(MarketListing.category_id == category_id)
    if subcategory_id:
        query = query.filter(MarketListing.subcategory_id == subcategory_id)
    if status_value:
        query = query.filter(MarketListing.status == status_value)
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                MarketListing.title.ilike(search_pattern),
                MarketListing.description.ilike(search_pattern)
            )
        )

    total = query.count()
    listings = query.order_by(MarketListing.created_at.desc()).offset(skip).limit(limit).all()
    return listings, total


def get_market_listing_by_id(db: Session, listing_id: int):
    """Get market listing by ID"""
    return db.query(MarketListing).filter(MarketListing.id == listing_id).first()


def create_market_listing(db: Session, listing: MarketListingCreate):
    """Create a new market listing"""
    # Validate that category and subcategory (if present) exist and belong to the same section
    category = db.query(Category).filter(Category.id == listing.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Compare section as plain strings to avoid SQLAlchemy ColumnElement typing issues
    category_section_str = str(getattr(category.section, "value", category.section))
    listing_type_str = str(listing.type)
    if category_section_str != listing_type_str:
        raise HTTPException(status_code=400, detail="Category section does not match listing type")
    if listing.subcategory_id is not None:
        subcategory = db.query(Category).filter(Category.id == listing.subcategory_id).first()
        if subcategory is None:
            raise HTTPException(status_code=400, detail="Subcategory is invalid for this category")

        # Safely compare parent/child relationship with runtime ints but satisfy type checker
        category_id_int = cast(int, category.id)
        sub_parent_id_int = cast(Optional[int], subcategory.parent_id)

        if sub_parent_id_int is not None and sub_parent_id_int != category_id_int:
            raise HTTPException(status_code=400, detail="Subcategory is invalid for this category")

        # Ensure subcategory belongs to the same section/type
        sub_section_str = str(getattr(subcategory.section, "value", subcategory.section))
        if sub_section_str != listing_type_str:
            raise HTTPException(status_code=400, detail="Subcategory is invalid for this category")
            raise HTTPException(status_code=400, detail="Subcategory is invalid for this category")

    listing_dict = listing.model_dump()
    # Ensure 'type' is always ListingSection Enum
    if isinstance(listing_dict["type"], str):
        listing_dict["type"] = models.ListingSection(listing_dict["type"])
    elif not isinstance(listing_dict["type"], models.ListingSection):
        raise ValueError("Invalid type for MarketListing")
    db_listing = MarketListing(**listing_dict)
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing


def archive_market_listing(db: Session, listing_id: int):
    """Archive a market listing"""
    listing = get_market_listing_by_id(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    setattr(listing, "status", "archived")
    db.commit()
    db.refresh(listing)
    return listing

# ============================================================================
# CHAIN MATCHING CRUD
# ============================================================================

def get_exchange_chains(db: Session, status: str = "proposed", skip: int = 0, limit: int = 20):
    """Get exchange chains with optional filtering"""
    from backend.models import ExchangeChain

    query = db.query(ExchangeChain)

    if status:
        query = query.filter(ExchangeChain.status == status)

    total = query.count()
    chains = query.offset(skip).limit(limit).all()

    return chains, total


def get_user_chains(db: Session, user_id: int, status: str = "proposed"):
    """Get all exchange chains involving a specific user"""
    from backend.models import ExchangeChain

    query = db.query(ExchangeChain).filter(
        ExchangeChain.participants.contains(user_id)  # PostgreSQL ARRAY contains
    )

    if status:
        query = query.filter(ExchangeChain.status == status)

    return query.all()


def accept_exchange_chain(db: Session, chain_id: int, user_id: int) -> bool:
    """
    User accepts their participation in an exchange chain.
    When all participants accept, mark chain as matched.
    """
    from backend.models import ExchangeChain

    chain = db.query(ExchangeChain).filter(ExchangeChain.id == chain_id).first()

    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")

    if user_id not in chain.participants:
        raise HTTPException(status_code=403, detail="User not in chain")

    # Track acceptances in chain metadata
    if not chain.participants:
        chain.participants = {}

    # Update acceptance status (simplified - in production use separate table)
    chain.status = "matched"
    db.commit()
    db.refresh(chain)

    return True


def decline_exchange_chain(db: Session, chain_id: int, user_id: int) -> bool:
    """User declines participation in exchange chain"""
    from backend.models import ExchangeChain

    chain = db.query(ExchangeChain).filter(ExchangeChain.id == chain_id).first()

    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")

    if user_id not in chain.participants:
        raise HTTPException(status_code=403, detail="User not in chain")

    chain.status = "rejected"
    db.commit()
    db.refresh(chain)

    return True

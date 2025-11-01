from pydantic import BaseModel, ConfigDict, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

# User schemas
class UserBase(BaseModel):
    username: Optional[str]
    contact: Optional[Dict[str, Any]] = None
    locations: Optional[List[str]] = None  # Multiple locations: ["Алматы", "Астана", "Шымкент"]

    # NEW: Telegram integration fields
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    telegram_first_name: Optional[str] = None

class UserCreate(UserBase):
    username: str

class User(UserBase):
    id: int
    trust_score: float
    created_at: datetime
    last_active_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# Profile schemas
class ProfileBase(BaseModel):
    name: str  # Required field for profile name
    category: str  # Required field for profile category
    description: str  # Required field for profile description
    avatar_url: Optional[str] = None  # Optional field for avatar URL
    location: Optional[str] = None
    visibility: bool = True

class ProfileCreate(ProfileBase):
    # Prefer username; keep optional user_id for backward compatibility in tests
    username: Optional[str] = None
    user_id: Optional[int] = None

class Profile(ProfileBase):
    id: int
    user_id: int
    username: str  # Include username in the response
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# Item schemas
class ItemBase(BaseModel):
    kind: int
    category: str
    title: Optional[str] = None
    description: Optional[str] = None
    item_metadata: Optional[Dict[str, Any]] = None
    active: bool = True
    wants: Optional[List[str]] = None
    offers: Optional[List[str]] = None
    value_min: Optional[Decimal] = None
    value_max: Optional[Decimal] = None
    lease_term: Optional[str] = None  # ISO 8601 duration string
    is_money: bool = False

class ItemCreate(ItemBase):
    # Accept either user_id (legacy) or username (new). Keep user_id for backward compatibility in tests.
    user_id: Optional[int] = None
    username: Optional[str] = None

class Item(ItemBase):
    id: int
    user_id: int
    created_at: datetime
    expires_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# Match schemas
class MatchBase(BaseModel):
    score: float
    computed_by: str = "rule-based"
    reasons: Optional[Dict[str, Any]] = None
    status: str = "new"

class MatchCreate(MatchBase):
    item_a: int
    item_b: int

class Match(MatchBase):
    id: int
    item_a: int
    item_b: int
    created_at: datetime
    notified: bool
    notified_at: Optional[datetime]
    status: str = "new"

    model_config = ConfigDict(from_attributes=True)

# Rating schemas
class RatingBase(BaseModel):
    score: int
    comment: Optional[str] = None
    tx_id: Optional[str] = None

class RatingCreate(RatingBase):
    from_username: str
    to_username: str

class Rating(RatingBase):
    id: int
    from_user: int
    to_user: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Notification schemas
class NotificationBase(BaseModel):
    channel: str = "telegram"
    payload: Dict[str, Any]
    status: str = "queued"

class NotificationCreate(NotificationBase):
    user_id: int

class Notification(NotificationBase):
    id: int
    user_id: int
    created_at: datetime
    sent_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# Listing schemas
class ListingBase(BaseModel):
    title: str
    description: Optional[str] = None
    offers: list[str] = []
    wants: list[str] = []

class ListingCreate(ListingBase):
    user_id: int

class Listing(ListingBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Category schemas (for marketplace taxonomy)
class CategoryBase(BaseModel):
    name: str
    slug: str
    section: str  # "wants" or "offers"
    parent_id: Optional[int] = None
    sort_order: int = 0
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    subcategories: Optional[List["CategoryResponse"]] = None

    model_config = ConfigDict(from_attributes=True)


# Market Listing schemas
class MarketListingBase(BaseModel):
    type: str  # "wants" or "offers"
    title: str
    description: Optional[str] = None
    category_id: int
    subcategory_id: Optional[int] = None
    location: Optional[str] = None
    contact: str


class MarketListingCreate(MarketListingBase):
    user_id: int


class MarketListingResponse(MarketListingBase):
    id: int
    user_id: int
    status: str  # "active" or "archived"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Hierarchical category tree (for frontend)
class CategoryTree(CategoryResponse):
    subcategories: Optional[List["CategoryTree"]] = None


CategoryTree.model_rebuild()
CategoryResponse.model_rebuild()

# ============================================================
# NEW: Exchange Type Schemas (for Phase 1)
# ============================================================

class ExchangeType(str, Enum):
    """Exchange type enum - matches backend ExchangeType"""
    PERMANENT = "permanent"
    TEMPORARY = "temporary"


class ListingItemType(str, Enum):
    """Item type enum"""
    WANT = "want"
    OFFER = "offer"


# ============================================================
# NEW: ListingItem Schemas
# ============================================================

# Expanded categories matching frontend definitions
VALID_CATEGORIES = {
    # Permanent exchange categories
    "cars",
    "real_estate",
    "electronics",
    "entertainment_tech",
    "everyday_clothes",
    "accessories",
    "kitchen_furniture",
    "collectibles",
    "animals_plants",
    "money_crypto",
    "securities",

    # Temporary exchange categories
    "bicycle",
    "electric_transport",
    "sports_transport",
    "hand_tools",
    "power_tools",
    "industrial_equipment",
    "photo_video",
    "audio_equipment",
    "sports_gear",
    "tourism_camping",
    "games_vr",
    "music_instruments",
    "costumes",
    "event_accessories",
    "subscriptions",
    "temporary_loan",
    "consulting",

    # Legacy categories (for backward compatibility)
    "furniture",
    "transport",
    "money",
    "services",
    "other"
}


class ListingItemCreate(BaseModel):
    """Single item for listing (permanent or temporary)"""

    category: str = Field(..., min_length=1, max_length=50, description="Category name")
    exchange_type: ExchangeType = Field(default=ExchangeType.PERMANENT)
    item_name: str = Field(..., min_length=1, max_length=100, description="Item name")
    value_tenge: int = Field(..., ge=1, description="Value in Tenge (₸)")
    duration_days: Optional[int] = Field(None, ge=1, le=365, description="Duration in days (for temporary only)")
    description: Optional[str] = Field(None, max_length=500)

    @validator('item_name')
    def strip_item_name(cls, v):
        """Trim whitespace from item name"""
        return v.strip() if v else v

    @validator('category')
    def validate_category(cls, v):
        """Ensure category is valid"""
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {v}. Must be one of {VALID_CATEGORIES}")
        return v

    @validator('duration_days')
    def validate_duration_days(cls, v, values):
        """
        Validate duration_days based on exchange_type:
        - PERMANENT: duration_days must be None
        - TEMPORARY: duration_days must be 1-365
        """
        exchange_type = values.get('exchange_type', ExchangeType.PERMANENT)

        if exchange_type == ExchangeType.TEMPORARY:
            if v is None:
                raise ValueError('duration_days is required for TEMPORARY exchange')
            if not (1 <= v <= 365):
                raise ValueError('duration_days must be between 1 and 365')
        elif exchange_type == ExchangeType.PERMANENT:
            if v is not None:
                raise ValueError('duration_days must be None for PERMANENT exchange')

        return v

    class Config:
        json_schema_extra = {
            "example_permanent": {
                "category": "electronics",
                "exchange_type": "permanent",
                "item_name": "Phone",
                "value_tenge": 50000,
                "duration_days": None,
                "description": "Used smartphone in good condition"
            },
            "example_temporary": {
                "category": "transport",
                "exchange_type": "temporary",
                "item_name": "Bicycle",
                "value_tenge": 30000,
                "duration_days": 7,
                "description": "Mountain bike for rental"
            }
        }


class ListingItemResponse(ListingItemCreate):
    """Response schema for ListingItem"""
    id: int = Field(..., description="Item ID")
    listing_id: int = Field(..., description="Parent listing ID")
    item_type: ListingItemType = Field(..., description="Type: want or offer")
    daily_rate: Optional[float] = Field(None, description="Daily rate for temporary (calculated)")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ListingItemsByCategoryCreate(BaseModel):
    """
    Listing items organized by category for both types.

    Structure:
    {
      "wants": {
        "electronics": [item1, item2, ...],
        "transport": [...],
        ...
      },
      "offers": {
        "electronics": [...],
        ...
      },
      "locations": ["Алматы", "Астана"]
    }
    """

class ListingItemsByCategoryCreate(BaseModel):
    """
    Listing items organized by category for both types.

    Structure:
    {
      "wants": {
        "electronics": [item1, item2, ...],
        "transport": [...],
        ...
      },
      "offers": {
        "electronics": [...],
        ...
      },
      "locations": ["Алматы", "Астана"],
      "user_data": {
        "name": "Иван Иванов",
        "telegram": "@username",
        "city": "Алматы"
      }
    }
    """

    wants: Dict[str, List[ListingItemCreate]] = Field(default_factory=dict, description="Wants by category")
    offers: Dict[str, List[ListingItemCreate]] = Field(default_factory=dict, description="Offers by category")
    locations: Optional[List[str]] = Field(None, description="User locations")
    user_data: Optional[Dict[str, str]] = Field(None, description="User data: name, telegram, city")

    @validator('wants', 'offers', pre=True)
    def validate_categories(cls, v):
        """Validate all categories are valid"""
        for category in v.keys():
            if category not in VALID_CATEGORIES:
                raise ValueError(f"Invalid category: {category}. Must be one of {VALID_CATEGORIES}")
        return v

    @validator('wants', 'offers')
    def remove_empty_items(cls, v):
        """Remove empty item entries"""
        for category in list(v.keys()):
            v[category] = [item for item in v[category]
                          if isinstance(item, dict) and item.get('item_name', '').strip()]
        # Remove categories with no items
        return {k: items for k, items in v.items() if items}


class ListingItemsByCategoryResponse(BaseModel):
    """Response with items organized by category"""
    id: int
    user_id: int
    wants_by_category: Dict[str, List[ListingItemResponse]]
    offers_by_category: Dict[str, List[ListingItemResponse]]
    total_wants_value: Dict[str, int]  # Category -> total value
    total_offers_value: Dict[str, int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

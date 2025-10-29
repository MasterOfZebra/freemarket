from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

# User schemas
class UserBase(BaseModel):
    username: Optional[str]
    contact: Optional[Dict[str, Any]] = None
    locations: Optional[List[str]] = None  # Multiple locations: ["Алматы", "Астана", "Шымкент"]

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

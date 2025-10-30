from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, ARRAY, Numeric, Interval, text, Enum as SQLEnum, UniqueConstraint, Index

from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from backend.database import Base
from datetime import datetime
from typing import Optional
import enum


# Enums for listing sections and statuses
class ListingSection(str, enum.Enum):
    WANT = "wants"
    OFFER = "offers"


class ListingStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


# Enum for supported locations
class Location(str, enum.Enum):
    ALMATY = "Алматы"
    ASTANA = "Астана"
    SHYMKENT = "Шымкент"


# NEW: Enum for exchange types (PERMANENT | TEMPORARY)
class ExchangeType(str, enum.Enum):
    """
    Two exchange types with different equivalence logic:
    - PERMANENT: value_a ≈ value_b (within ±15%)
    - TEMPORARY: (value_a/days_a) ≈ (value_b/days_b) = daily_rate matching
    """
    PERMANENT = "permanent"
    TEMPORARY = "temporary"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    contact = Column(JSON)
    locations = Column(ARRAY(String), default=["Алматы"], nullable=False)  # Multiple cities: ["Алматы", "Астана", ...]
    trust_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True))

    # NEW: Telegram integration fields for notifications
    telegram_id = Column(Integer, unique=True, nullable=True)           # chat_id for Bot API
    telegram_username = Column(String, nullable=True)                   # username (without @)
    telegram_first_name = Column(String, nullable=True)                 # first_name from Telegram

    profiles = relationship("Profile", back_populates="user")
    items = relationship("Item", back_populates="user")
    ratings_given = relationship("Rating", foreign_keys="Rating.from_user", back_populates="from_user_rel")
    ratings_received = relationship("Rating", foreign_keys="Rating.to_user", back_populates="to_user_rel")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    avatar_url = Column(String)
    location = Column(String)
    visibility = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="profiles")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kind = Column(Integer, nullable=False, default=1, server_default=text("1"))  # 1=offer, 2=want
    category = Column(String, nullable=False)
    title = Column(String)
    description = Column(Text)
    item_metadata = Column(JSON)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    wants = Column(JSON, nullable=True)  # List of desired items
    offers = Column(JSON, nullable=True)  # List of offered items
    value_min = Column(Numeric)
    value_max = Column(Numeric)
    lease_term = Column(Interval)
    is_money = Column(Boolean, default=False)

    user = relationship("User", back_populates="items")

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    item_a = Column(Integer, ForeignKey("items.id"))
    item_b = Column(Integer, ForeignKey("items.id"))
    score = Column(Float, nullable=False)
    computed_by = Column(String, default="rule-based")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notified = Column(Boolean, default=False)
    notified_at = Column(DateTime(timezone=True))
    reasons = Column(JSON, nullable=True)  # Explanation for the match
    status = Column(String, default="new")  # new, notified, accepted_a, accepted_b, matched, rejected, expired
    matched_at = Column(DateTime(timezone=True), nullable=True)  # Timestamp for mutual acceptance

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    from_user = Column(Integer, ForeignKey("users.id"))
    to_user = Column(Integer, ForeignKey("users.id"))
    score = Column(Integer, nullable=False)
    comment = Column(Text)
    tx_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    from_user_rel = relationship("User", foreign_keys=[from_user], back_populates="ratings_given")
    to_user_rel = relationship("User", foreign_keys=[to_user], back_populates="ratings_received")

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(nullable=True)
    channel: Mapped[str] = mapped_column(default="telegram")
    is_sent: Mapped[bool] = mapped_column(default=False)
    is_read: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(default="queued")  # queued, sent, failed
    payload = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

class MutualMatch(Base):
    __tablename__ = "mutual_matches"

    id = Column(Integer, primary_key=True, index=True)
    item_a = Column(Integer, ForeignKey("items.id"))
    item_b = Column(Integer, ForeignKey("items.id"))
    matched_at = Column(DateTime(timezone=True), server_default=func.now())

class AbMetric(Base):
    __tablename__ = "ab_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    config_key = Column(String, nullable=False)
    match_accept_rate = Column(Float)
    conversion_rate = Column(Float)
    time_to_match = Column(Interval)
    match_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ExchangeChain(Base):
    __tablename__ = "exchange_chains"

    id = Column(Integer, primary_key=True, index=True)
    participants = Column(JSON, nullable=False)
    items = Column(JSON, nullable=False)
    total_score = Column(Float, nullable=False)
    status = Column(String, default="proposed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

class ApiMetric(Base):
    __tablename__ = "api_metrics"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    response_time = Column(Float, nullable=False)
    status_code = Column(Integer, nullable=False)
    user_id = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


# Categories for Wants/Offers taxonomy
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    section = Column(SQLEnum(ListingSection), nullable=False)  # wants or offers
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  # For subcategories
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subcategories = relationship("Category", remote_side=[id], backref="parent")
    listings = relationship("MarketListing", foreign_keys="MarketListing.category_id", back_populates="category")

    __table_args__ = (
        UniqueConstraint("section", "parent_id", "slug", name="uq_category_section_parent_slug"),
        Index("ix_category_section_parent", "section", "parent_id"),
    )


# New listing models to support wants/offers marketplace
class MarketListing(Base):
    __tablename__ = "market_listings"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(SQLEnum(ListingSection), nullable=False)  # wants or offers
    title = Column(String, nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    location = Column(String)
    contact = Column(String)  # user phone/telegram/etc
    status = Column(SQLEnum(ListingStatus), default=ListingStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="market_listings")
    category = relationship("Category", foreign_keys=[category_id], back_populates="listings")

    __table_args__ = (
        Index("ix_market_listing_type_category_status", "type", "category_id", "status"),
        Index("ix_market_listing_created_desc", "created_at", "status"),
    )


# New listing models to support offers/wants per listing
class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    offers = relationship("ListingOffer", back_populates="listing", cascade="all, delete-orphan")
    wants = relationship("ListingWant", back_populates="listing", cascade="all, delete-orphan")

class ListingOffer(Base):
    __tablename__ = "listing_offers"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(String)

    listing = relationship("Listing", back_populates="offers")

class ListingWant(Base):
    __tablename__ = "listing_wants"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(String)

    listing = relationship("Listing", back_populates="wants")


# ============================================================
# NEW: ListingItem Model for Category-Based Matching
# Supports both PERMANENT and TEMPORARY exchange types
# ============================================================

class ListingItemType(str, enum.Enum):
    """Type of item in listing (want vs offer)"""
    WANT = "want"
    OFFER = "offer"


class ListingItemCategory(str, enum.Enum):
    """Available categories for both exchange types"""
    ELECTRONICS = "electronics"      # 🏭 Техника
    MONEY = "money"                  # 💰 Деньги
    FURNITURE = "furniture"          # 🛋️ Мебель
    TRANSPORT = "transport"          # 🚗 Транспорт
    SERVICES = "services"            # 🔧 Услуги
    OTHER = "other"                  # 📦 Прочее


class ListingItem(Base):
    """
    Universal item model for both permanent and temporary exchanges.
    
    PERMANENT EXCHANGE:
      - exchange_type = "permanent"
      - duration_days = NULL
      - value_tenge = equivalent monetary value
      - Matching: value_a ≈ value_b (within ±15%)
    
    TEMPORARY EXCHANGE:
      - exchange_type = "temporary"
      - duration_days = 1-365 (rental duration)
      - value_tenge = daily rate base
      - Matching: (value_a/days_a) ≈ (value_b/days_b)
    """
    __tablename__ = "listing_items"
    
    __table_args__ = (
        # Composite indexes for fast filtering
        Index("ix_listing_exchange_type", "listing_id", "exchange_type"),
        Index("ix_category_exchange_type", "category", "exchange_type"),
        Index("ix_item_type_category", "item_type", "category"),
        # For temporal queries
        Index("ix_created_at_exchange", "created_at", "exchange_type"),
        # For matching queries
        Index("ix_category_value_exchange", "category", "value_tenge", "exchange_type"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    
    # Item classification
    item_type = Column(SQLEnum(ListingItemType), nullable=False)  # want | offer
    category = Column(String(50), nullable=False)                 # electronics, money, furniture, etc.
    
    # Exchange type (NEW - core for Phase 1)
    exchange_type = Column(
        SQLEnum(ExchangeType), 
        nullable=False, 
        default=ExchangeType.PERMANENT,
        index=True
    )
    
    # Item details
    item_name = Column(String(100), nullable=False)
    value_tenge = Column(Integer, nullable=False)  # ₸ (Tenge) - always required
    
    # Duration for TEMPORARY exchange (NEW - core for Phase 1)
    duration_days = Column(Integer, nullable=True)  # NULL for permanent, 1-365 for temporary
    
    description = Column(Text, nullable=True, default="")
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    listing = relationship("Listing", backref="items")
    
    def __repr__(self):
        return (
            f"<ListingItem "
            f"id={self.id} "
            f"type={self.item_type} "
            f"category={self.category} "
            f"exchange={self.exchange_type} "
            f"value={self.value_tenge}₸"
            f"{f' days={self.duration_days}' if self.duration_days else ''}"
            f">"
        )
    
    # ========== PROPERTIES FOR MATCHING ==========
    
    @property
    def daily_rate(self) -> float:
        """
        Calculate daily rate for TEMPORARY exchange only.
        For PERMANENT: returns None
        Formula: value_tenge / duration_days
        """
        if self.exchange_type == ExchangeType.TEMPORARY and self.duration_days:
            return self.value_tenge / self.duration_days
        return None
    
    @property
    def is_valid(self) -> bool:
        """
        Validate item data:
        - value_tenge must be > 0
        - TEMPORARY: duration_days must be 1-365
        - PERMANENT: duration_days must be NULL
        """
        if self.value_tenge <= 0:
            return False
        
        if self.exchange_type == ExchangeType.TEMPORARY:
            return 1 <= self.duration_days <= 365 if self.duration_days else False
        else:  # PERMANENT
            return self.duration_days is None
    
    @property
    def equivalence_key(self) -> tuple:
        """
        Create unique key for matching algorithm.
        Used to identify duplicate matching criteria.
        """
        if self.exchange_type == ExchangeType.TEMPORARY:
            return (self.category, self.exchange_type, round(self.daily_rate, 2))
        else:  # PERMANENT
            return (self.category, self.exchange_type, self.value_tenge)

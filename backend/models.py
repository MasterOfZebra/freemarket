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

    # Authentication fields
    username = Column(String(50), unique=True, index=True, nullable=True)  # Optional, can be email or username
    email = Column(String(100), unique=True, index=True, nullable=True)    # For email-based auth
    phone = Column(String(20), unique=True, index=True, nullable=True)     # For phone-based auth
    password_hash = Column(String(255), nullable=True)                     # Argon2id/bcrypt hash

    # Profile fields
    full_name = Column(String(100), nullable=True)
    telegram_contact = Column(String(100), nullable=True)                  # @username or phone
    city = Column(String(50), default="Алматы", nullable=False)            # Single city for now
    bio = Column(Text, nullable=True)

    # Trust and reputation
    trust_score = Column(Float, default=0.0)
    exchange_count = Column(Integer, default=0)
    rating_avg = Column(Float, default=0.0)

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_active_at = Column(DateTime(timezone=True), nullable=True)

    # Legacy fields (for backward compatibility)
    contact = Column(JSON, nullable=True)                                  # Legacy contact info
    locations = Column(ARRAY(String), default=["Алматы"], nullable=True)  # Legacy multiple cities

    # Telegram integration fields
    telegram_id = Column(Integer, unique=True, nullable=True)             # chat_id for Bot API
    telegram_username = Column(String(50), nullable=True)                 # username (without @)
    telegram_first_name = Column(String(50), nullable=True)               # first_name from Telegram

    # Relationships
    profiles = relationship("Profile", back_populates="user")
    items = relationship("Item", back_populates="user")
    listings = relationship("Listing", back_populates="user")
    ratings_given = relationship("Rating", foreign_keys="Rating.from_user", back_populates="from_user_rel")
    ratings_received = relationship("Rating", foreign_keys="Rating.to_user", back_populates="to_user_rel")

    __table_args__ = (
        Index("ix_user_auth", "email", "phone", "username"),  # For auth lookups
    )

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


# ==============================================
# CATEGORIES SYSTEM v6 - VERSIONED CATEGORIES
# ==============================================

class CategoryVersion(Base):
    """Version control for category system changes"""
    __tablename__ = "category_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(20), nullable=False, unique=True)  # e.g., "v6.0", "v6.1"
    is_active = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    categories = relationship("CategoryV6", back_populates="version")


class CategoryV6(Base):
    """New versioned category system (v6)"""
    __tablename__ = "categories_v6"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("category_versions.id"), nullable=False)

    # Category metadata
    slug = Column(String(50), nullable=False, index=True)  # e.g., "bicycles", "electronics"
    name = Column(String(100), nullable=False)             # Display name in Russian
    group = Column(String(100), nullable=False)            # Group/parent category
    emoji = Column(String(10), nullable=False)             # Icon emoji

    # Exchange type this category belongs to
    exchange_type = Column(SQLEnum(ExchangeType), nullable=False, index=True)

    # Form configuration (JSON schema for dynamic forms)
    form_schema = Column(JSON, nullable=True)  # Field definitions, validation rules

    # Ordering and status
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    version = relationship("CategoryVersion", back_populates="categories")

    __table_args__ = (
        UniqueConstraint("version_id", "exchange_type", "slug", name="uq_category_version_exchange_slug"),
        Index("ix_category_active_version", "version_id", "is_active", "exchange_type"),
    )


class CategoryMapping(Base):
    """Legacy to new category mappings for migration"""
    __tablename__ = "category_mappings"

    id = Column(Integer, primary_key=True, index=True)
    legacy_category = Column(String(50), nullable=False)    # Old category slug
    new_category_slug = Column(String(50), nullable=False)  # New v6 category slug
    exchange_type = Column(SQLEnum(ExchangeType), nullable=False)
    confidence = Column(Float, default=1.0)                 # Mapping confidence 0-1
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("legacy_category", "exchange_type", name="uq_legacy_mapping"),
        Index("ix_mapping_exchange_type", "exchange_type"),
    )


# ==============================================
# AUTHENTICATION SYSTEM - JWT + Refresh Tokens
# ==============================================

class RefreshToken(Base):
    """Refresh tokens for JWT authentication"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Token data
    token_hash = Column(String(128), nullable=False, unique=True)  # SHA-256 hash of refresh token
    device_id = Column(String(64), nullable=False)                  # Client device identifier
    user_agent = Column(String(255), nullable=True)                 # Client user agent

    # Validity
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, index=True)

    # Security
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_reason = Column(String(100), nullable=True)

    # Relationships
    user = relationship("User", backref="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_user_device", "user_id", "device_id"),
        Index("ix_refresh_expires", "expires_at", "is_revoked"),
    )

    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return self.expires_at < func.now()

    @property
    def is_valid(self) -> bool:
        """Check if token is still valid"""
        return not self.is_revoked and not self.is_expired


class AuthEvent(Base):
    """Audit log for authentication events"""
    __tablename__ = "auth_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)  # login, logout, refresh, failed_login, etc.

    # Event details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    device_id = Column(String(64), nullable=True)
    success = Column(Boolean, default=True)
    details = Column(JSON, nullable=True)  # Additional event data

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="auth_events")

    __table_args__ = (
        Index("ix_auth_user_time", "user_id", "created_at"),
        Index("ix_auth_event_type", "event_type", "created_at"),
    )


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

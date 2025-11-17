from sqlalchemy import Column, Integer, BigInteger, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, ARRAY, Numeric, Interval, text as sa_text, Enum as SQLEnum, UniqueConstraint, Index

from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from backend.database import Base
from datetime import datetime
from typing import Optional, Dict, Any
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
    rating_count = Column(Integer, default=0)
    last_rating_update = Column(DateTime(timezone=True), nullable=True)

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
    telegram_id = Column(BigInteger, unique=True, nullable=True)             # chat_id for Bot API (can be very large)
    telegram_username = Column(String(50), nullable=True)                 # username (without @)
    telegram_first_name = Column(String(50), nullable=True)               # first_name from Telegram

    # RBAC fields
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationships
    profiles = relationship("Profile", back_populates="user")
    items = relationship("Item", back_populates="user")
    listings = relationship("Listing", back_populates="user")
    match_indexes = relationship("MatchIndex", back_populates="user")
    sent_messages = relationship("ExchangeMessage", back_populates="sender")
    events = relationship("UserEvent", back_populates="user")
    reviews_given = relationship(
        "UserReview",
        foreign_keys="[UserReview.author_id]",
        back_populates="author"
    )
    reviews_received = relationship(
        "UserReview",
        foreign_keys="[UserReview.target_id]",
        back_populates="target"
    )
    exchange_actions = relationship("ExchangeHistory", back_populates="user")
    action_logs = relationship("UserActionLog", back_populates="user")
    trust_index = relationship("UserTrustIndex", back_populates="user", uselist=False)
    reports_filed = relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter")
    reports_received = relationship("Report", foreign_keys="Report.target_user_id", back_populates="target_user")
    reports_moderated = relationship("Report", foreign_keys="Report.admin_id", back_populates="admin")
    ratings_given = relationship(
        "Rating",
        foreign_keys="[Rating.from_user]",
        back_populates="from_user_rel"
    )
    ratings_received = relationship(
        "Rating",
        foreign_keys="[Rating.to_user]",
        back_populates="to_user_rel"
    )
    role = relationship("Role", back_populates="users")

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
    kind = Column(Integer, nullable=False, default=1, server_default=sa_text("1"))  # 1=offer, 2=want
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
    exchange_type = Column(String(20), nullable=False, index=True)  # VARCHAR to match migration

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
    exchange_type = Column(String(20), nullable=False)  # VARCHAR to match migration
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
        from datetime import datetime, timezone
        # ensure that expires_at and now are both timezone-aware
        now = datetime.now(timezone.utc)
        # expires_at may or may not be tz-aware depending on backend engine, handle accordingly
        expires_at = self.expires_at
        if not isinstance(expires_at, datetime) or not isinstance(now, datetime):
            # Defensive: if either is not a datetime, return expired
            return True
        # Ensure both times are naive or both are aware for correct comparison
        if expires_at.tzinfo is None and now.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=now.tzinfo)
        elif expires_at.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=expires_at.tzinfo)
        # Ensure proper bool return: don't return SQLAlchemy Column expressions!
        return bool(expires_at < now)

    @property
    def is_valid(self) -> bool:
        """Check if token is still valid"""
        # self.is_revoked is a SQLAlchemy Column, not a Python bool
        # To get the actual value, use getattr if necessary
        is_revoked = getattr(self, "is_revoked", None)
        # Defensive: treat None as revoked (invalid)
        if is_revoked is None:
            return False
        # Defensive: handle SQLAlchemy-instrumented attributes vs. loaded values
        try:
            if hasattr(is_revoked, '__bool__'):
                revoked = bool(is_revoked)
            else:
                revoked = is_revoked
        except Exception:
            revoked = True  # If evaluation fails, revoke for safety

        return not revoked and not self.is_expired


class AuthEvent(Base):
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

    # Soft delete fields
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationships
    user = relationship("User", back_populates="listings")
    items = relationship("ListingItem", back_populates="listing", cascade="all, delete-orphan")
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

    # Soft delete for completed exchanges
    is_archived = Column(Boolean, nullable=False, default=False, index=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    listing = relationship("Listing", backref="items")
    reports = relationship("Report", back_populates="target_listing")

    def __repr__(self):
        duration = getattr(self, "duration_days", None)
        duration_str = f" days={duration}" if duration not in (None, 0) else ""

        return (
            f"<ListingItem "
            f"id={self.id} "
            f"type={self.item_type} "
            f"category={self.category} "
            f"exchange={self.exchange_type} "
            f"value={self.value_tenge}₸"
            f"{duration_str}"
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
        exchange_type = getattr(self, "exchange_type", None)
        duration_days = getattr(self, "duration_days", None)
        value = getattr(self, "value_tenge", None)

        if exchange_type == ExchangeType.TEMPORARY:
            if duration_days in (None, 0) or value is None:
                return 0.0
            try:
                return float(value) / float(duration_days)
            except (ZeroDivisionError, TypeError, ValueError):
                return 0.0

        return 0.0

    @property
    def is_valid(self) -> bool:
        """
        Validate item data:
        - value_tenge must be > 0
        - TEMPORARY: duration_days must be 1-365
        - PERMANENT: duration_days must be None
        """
        value = getattr(self, "value_tenge", None)
        exchange_type = getattr(self, "exchange_type", None)
        duration = getattr(self, "duration_days", None)

        if value is not None and value <= 0:
            return False

        if exchange_type == ExchangeType.TEMPORARY:
            if duration is None:
                return False
            try:
                duration_int = int(duration)
            except (TypeError, ValueError):
                return False
            return 1 <= duration_int <= 365

        if exchange_type == ExchangeType.PERMANENT:
            return duration is None

        # If exchange_type is unknown, default to False for safety
        return False

    @property
    def equivalence_key(self) -> tuple:
        """
        Create unique key for matching algorithm.
        Used to identify duplicate matching criteria.
        """
        exchange_type = getattr(self, "exchange_type", None)
        category = getattr(self, "category", None)
        value = getattr(self, "value_tenge", None)

        if exchange_type == ExchangeType.TEMPORARY:
            daily_rate = self.daily_rate
            normalized_rate = round(daily_rate, 2) if isinstance(daily_rate, (int, float)) else None
            return (
                category,
                exchange_type,
                normalized_rate
            )

        if exchange_type == ExchangeType.PERMANENT:
            return (
                category,
                exchange_type,
                value
            )

        # Fallback for unknown exchange types
        return (
            category,
            exchange_type,
            value
        )


class ItemType(str, enum.Enum):
    """Type of listing item"""
    WANT = "want"
    OFFER = "offer"


class MatchIndex(Base):
    """
    Incremental matching index for optimized performance.

    Stores user preferences by category and tags for fast matching queries.
    Prevents full N×N recalculation by tracking only changed categories.
    """
    __tablename__ = "match_index"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(10), nullable=False, index=True)  # 'want' | 'offer'
    exchange_type = Column(String(20), nullable=False, index=True)  # 'PERMANENT' | 'TEMPORARY'
    category = Column(String(50), nullable=False, index=True)
    tags = Column(JSON, nullable=True)  # Array of tags for advanced filtering
    updated_at = Column(DateTime(timezone=True), server_default=sa_text('now()'), onupdate=sa_text('now()'))
    created_at = Column(DateTime(timezone=True), server_default=sa_text('now()'))

    # Relationships
    user = relationship("User", back_populates="match_indexes")

    # Unique constraint to prevent duplicates
    __table_args__ = (
        UniqueConstraint('user_id', 'category', 'item_type', 'exchange_type',
                        name='uq_match_index_user_category_type'),
    )

    def __repr__(self):
        return f"<MatchIndex(user_id={self.user_id}, category='{self.category}', type='{self.item_type}')>"


class MessageType(str, enum.Enum):
    """Type of chat message"""
    TEXT = "text"
    IMAGE = "image"
    SYSTEM = "system"  # Auto-generated messages


class ExchangeMessage(Base):
    """
    Chat messages for exchange conversations.

    Each exchange (mutual_X_Y_A_B) has its own chat thread.
    Only participants can send/receive messages.
    """
    __tablename__ = "exchange_messages"

    id = Column(Integer, primary_key=True, index=True)
    exchange_id = Column(String(100), nullable=False, index=True)  # mutual_X_Y_A_B format
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message_text = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), nullable=False, default=MessageType.TEXT)
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)  # When message was delivered to recipient
    read_at = Column(DateTime(timezone=True), nullable=True)  # When message was read by recipient
    created_at = Column(DateTime(timezone=True), server_default=sa_text('now()'), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=sa_text('now()'))

    # Relationships
    sender = relationship("User", back_populates="sent_messages")

    def __repr__(self):
        return f"<ExchangeMessage(id={self.id}, exchange='{self.exchange_id}', sender={self.sender_id})>"


class EventType(str, enum.Enum):
    """Types of user events/notifications"""
    MESSAGE_RECEIVED = "MessageReceived"
    OFFER_MATCHED = "OfferMatched"
    EXCHANGE_CREATED = "ExchangeCreated"
    EXCHANGE_CONFIRMED = "ExchangeConfirmed"
    EXCHANGE_COMPLETED = "ExchangeCompleted"
    REVIEW_RECEIVED = "ReviewReceived"
    SYSTEM_WARNING = "SystemWarning"
    BAN_ISSUED = "BanIssued"
    PROFILE_VIEWED = "ProfileViewed"
    LISTING_UPDATED = "ListingUpdated"


class UserEvent(Base):
    """
    User notifications and events.

    Tracks all user-facing events like messages, matches, completions, etc.
    """
    __tablename__ = "user_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    related_id = Column(Integer, nullable=True)  # ID of related object
    payload = Column(JSON, nullable=True)  # Additional event data
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=sa_text('now()'), index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="events")

    def __repr__(self):
        return f"<UserEvent(id={self.id}, user={self.user_id}, type='{self.event_type.value}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API responses"""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "related_id": self.related_id,
            "payload": self.payload,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if getattr(self, "created_at", None) else None,
            "read_at": self.read_at.isoformat() if getattr(self, "read_at", None) else None,
        }

class UserReview(Base):
    """
    User reviews and ratings after exchange completion.
    """
    __tablename__ = "user_reviews"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exchange_id = Column(String(100), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    text = Column(Text, nullable=True)
    is_public = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=sa_text('now()'), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=sa_text('now()'), onupdate=sa_text('now()'))

    # Relationships
    author = relationship("User", foreign_keys=[author_id], back_populates="reviews_given")
    target = relationship("User", foreign_keys=[target_id], back_populates="reviews_received")

    def __repr__(self):
        return f"<UserReview(id={self.id}, author={self.author_id}, target={self.target_id}, rating={self.rating})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API responses"""
        created = getattr(self, "created_at", None)
        created_str = created.isoformat() if isinstance(created, datetime) else None

        return {
            "id": self.id,
            "author_id": self.author_id,
            "author_name": self.author.full_name if self.author else "Unknown",
            "target_id": self.target_id,
            "target_name": self.target.full_name if self.target else "Unknown",
            "exchange_id": self.exchange_id,
            "rating": self.rating,
            "text": self.text,
            "is_public": self.is_public,
            "created_at": created_str,
        }


class ExchangeEventType(str, enum.Enum):
    """Types of exchange lifecycle events"""
    CREATED = "created"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REVIEWED = "reviewed"


class ExchangeHistory(Base):
    """
    Audit trail for exchange lifecycle events.
    """
    __tablename__ = "exchange_history"

    id = Column(Integer, primary_key=True, index=True)
    exchange_id = Column(String(100), nullable=False, index=True)
    event_type = Column(SQLEnum(ExchangeEventType), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    details = Column(JSON, nullable=True)  # Additional event data
    created_at = Column(DateTime(timezone=True), server_default=sa_text('now()'), index=True)

    # Relationships
    user = relationship("User", back_populates="exchange_actions")

    def __repr__(self):
        return f"<ExchangeHistory(id={self.id}, exchange='{self.exchange_id}', event='{self.event_type.value}')>"


class UserActionType(str, enum.Enum):
    """Types of user actions for audit logging"""
    LOGIN = "login"
    LOGOUT = "logout"
    PROFILE_UPDATE = "profile_update"
    LISTING_CREATE = "listing_create"
    LISTING_UPDATE = "listing_update"
    EXCHANGE_MATCH = "exchange_match"
    EXCHANGE_CONFIRM = "exchange_confirm"
    EXCHANGE_COMPLETE = "exchange_complete"
    REVIEW_CREATE = "review_create"
    MESSAGE_SEND = "message_send"
    REPORT_CREATE = "report_create"


class UserActionLog(Base):
    """
    Unified audit log for all user actions.
    """
    __tablename__ = "user_action_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(SQLEnum(UserActionType), nullable=False, index=True)
    target_id = Column(Integer, nullable=True)  # ID of affected object
    action_metadata = Column(JSON, nullable=True)  # Additional action data
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=sa_text('now()'), index=True)

    # Relationships
    user = relationship("User", back_populates="action_logs")

    def __repr__(self):
        return f"<UserActionLog(id={self.id}, user={self.user_id}, action='{self.action_type.value}')>"


class UserTrustIndex(Base):
    """
    Trust index calculation for users based on activity and reputation.
    """
    __tablename__ = "user_trust_index"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    trust_score = Column(Float, nullable=False, default=50.0)  # 0-100 scale
    weighted_rating = Column(Float, nullable=False, default=0.0)

    # Activity metrics
    exchanges_completed = Column(Integer, nullable=False, default=0)
    reviews_received = Column(Integer, nullable=False, default=0)
    reports_filed = Column(Integer, nullable=False, default=0)
    reports_received = Column(Integer, nullable=False, default=0)

    # Risk factors
    account_age_days = Column(Integer, nullable=False, default=0)
    last_activity_days = Column(Integer, nullable=False, default=0)

    # Cache timestamps
    last_calculated = Column(DateTime(timezone=True), server_default=sa_text('now()'), index=True)
    created_at = Column(DateTime(timezone=True), server_default=sa_text('now()'), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=sa_text('now()'))

    # Relationships
    user = relationship("User", back_populates="trust_index")

    def __repr__(self):
        return f"<UserTrustIndex(user={self.user_id}, trust={self.trust_score:.1f}, rating={self.weighted_rating:.2f})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API responses"""
        last_calculated_value = getattr(self, "last_calculated", None)
        last_calculated_str = (
            last_calculated_value.isoformat()
            if isinstance(last_calculated_value, datetime)
            else None
        )

        return {
            "id": self.id,
            "user_id": self.user_id,
            "trust_score": self.trust_score,
            "weighted_rating": self.weighted_rating,
            "exchanges_completed": self.exchanges_completed,
            "reviews_received": self.reviews_received,
            "reports_filed": self.reports_filed,
            "reports_received": self.reports_received,
            "account_age_days": self.account_age_days,
            "last_activity_days": self.last_activity_days,
            "last_calculated": last_calculated_str,
        }


class ReportReason(str, enum.Enum):
    """Reasons for reporting listings or users"""
    PRICE_MISMATCH = "price_mismatch"
    UNAVAILABLE_ITEM = "unavailable_item"
    FAKE_LISTING = "fake_listing"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    SPAM = "spam"
    HARASSMENT = "harassment"
    FRAUD = "fraud"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    """Report processing status"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class Report(Base):
    """
    User reports for moderation.
    """
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_listing_id = Column(Integer, ForeignKey("listing_items.id", ondelete="CASCADE"), nullable=True, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    reason = Column(SQLEnum(ReportReason), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(ReportStatus), nullable=False, default=ReportStatus.PENDING)

    # Moderation fields
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    admin_notes = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=sa_text('now()'), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=sa_text('now()'))

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reports_filed")
    target_listing = relationship("ListingItem", back_populates="reports")
    target_user = relationship("User", foreign_keys=[target_user_id], back_populates="reports_received")
    admin = relationship("User", foreign_keys=[admin_id], back_populates="reports_moderated")

    def __repr__(self):
        return f"<Report(id={self.id}, reporter={self.reporter_id}, reason='{self.reason.value}', status='{self.status.value}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API responses"""
        return {
            "id": self.id,
            "reporter_id": self.reporter_id,
            "reporter_name": self.reporter.full_name if self.reporter else "Unknown",
            "target_listing_id": self.target_listing_id,
            "target_user_id": self.target_user_id,
            "target_user_name": self.target_user.full_name if self.target_user else None,
            "reason": self.reason.value,
            "description": self.description,
            "status": self.status.value,
            "admin_id": self.admin_id,
            "admin_notes": self.admin_notes,
            "resolution": self.resolution,
            "created_at": self._isoformat_datetime("created_at"),
            "resolved_at": self._isoformat_datetime("resolved_at"),
        }

    def _isoformat_datetime(self, attr_name: str) -> Optional[str]:
        value = getattr(self, attr_name, None)
        return value.isoformat() if isinstance(value, datetime) else None


# ==============================================
# RBAC MODELS (Roles, Permissions, Complaints, Audit Log)
# ==============================================

class Role(Base):
    """Role model for RBAC system"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"


class Permission(Base):
    """Permission model for RBAC system"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    
    # Relationships
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}')>"


class RolePermission(Base):
    """Junction table for role-permission many-to-many relationship"""
    __tablename__ = "role_permissions"
    
    role_id = Column(Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey('permissions.id', ondelete="CASCADE"), primary_key=True)


class Complaint(Base):
    """Complaint model for moderation system"""
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True)
    complainant_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    reported_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    reported_listing_id = Column(Integer, ForeignKey('listings.id'), nullable=True)
    complaint_type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default='pending', nullable=True)
    moderator_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=sa_text('now()'), nullable=True)
    
    def __repr__(self):
        return f"<Complaint(id={self.id}, type='{self.complaint_type}', status='{self.status}')>"


class AdminAuditLog(Base):
    """Admin audit log for tracking admin actions"""
    __tablename__ = "admin_audit_log"
    
    id = Column(Integer, primary_key=True)
    request_id = Column(String, nullable=True)
    admin_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(Integer, nullable=True)
    diff = Column(JSON, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=sa_text('now()'), nullable=True)
    
    def __repr__(self):
        return f"<AdminAuditLog(id={self.id}, action='{self.action}', admin={self.admin_user_id})>"

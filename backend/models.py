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

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    contact = Column(JSON)
    trust_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True))

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

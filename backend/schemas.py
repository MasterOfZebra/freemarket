from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    username: Optional[str] = None
    telegram_id: int
    contact: Optional[Dict[str, Any]] = None

class UserCreate(UserBase):
    telegram_id: int

class User(UserBase):
    id: int
    trust_score: float
    created_at: datetime
    last_active_at: Optional[datetime]

    class Config:
        from_attributes = True

# Profile schemas
class ProfileBase(BaseModel):
    data: Dict[str, Any]
    location: Optional[str] = None
    visibility: bool = True

class ProfileCreate(ProfileBase):
    user_id: int

class Profile(ProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Item schemas
class ItemBase(BaseModel):
    kind: int
    category: str
    title: Optional[str] = None
    description: Optional[str] = None
    item_metadata: Optional[Dict[str, Any]] = None
    active: bool = True

class ItemCreate(ItemBase):
    user_id: int

class Item(ItemBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Match schemas
class MatchBase(BaseModel):
    score: float
    computed_by: str = "rule-based"

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

    class Config:
        from_attributes = True

# Rating schemas
class RatingBase(BaseModel):
    score: int
    comment: Optional[str] = None
    tx_id: Optional[str] = None

class RatingCreate(RatingBase):
    from_user: int
    to_user: int

class Rating(RatingBase):
    id: int
    from_user: int
    to_user: int
    created_at: datetime

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

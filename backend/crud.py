from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from .models import User, Profile, Item, Match, Rating, Notification
from .schemas import UserCreate, ProfileCreate, ItemCreate, MatchCreate, RatingCreate, NotificationCreate
from fastapi import HTTPException

# User CRUD
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    db_user = User(
    username=user.username,
        contact=user.contact
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

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

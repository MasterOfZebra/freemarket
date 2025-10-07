from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from .models import User, Profile, Item, Match, Rating, Notification
from .schemas import UserCreate, ProfileCreate, ItemCreate, MatchCreate, RatingCreate, NotificationCreate

# User CRUD
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_telegram(db: Session, telegram: int):
    return db.query(User).filter(User.telegram_id == telegram).first()

def create_user(db: Session, user: UserCreate):
    db_user = User(
        telegram_id=user.telegram_id,
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
    db_profile = Profile(
        user_id=profile.user_id,
        data=profile.data,
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
    db_rating = Rating(
        from_user=rating.from_user,
        to_user=rating.to_user,
        score=rating.score,
        comment=rating.comment,
        tx_id=rating.tx_id
    )
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)

    # Update trust score
    update_trust_score(db, rating.to_user)

    return db_rating

def update_trust_score(db: Session, user_id: int):
    ratings = db.query(Rating).filter(Rating.to_user == user_id).all()
    if ratings:
        avg_score = sum(r.score for r in ratings) / len(ratings)
        db.query(User).filter(User.id == user_id).update({"trust_score": avg_score})
        db.commit()

# Notification CRUD
def create_notification(db: Session, notification: NotificationCreate):
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

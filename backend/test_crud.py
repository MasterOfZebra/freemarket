import pytest
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from .crud import (
    get_user, get_user_by_username, create_user,
    get_user_profiles, create_profile,
    get_user_items, create_item,
    get_user_matches, create_match,
    get_user_ratings, create_rating, update_trust_score,
    create_notification, get_pending_notifications, mark_notification_sent
)
from backend.schemas import UserCreate, ProfileCreate, ItemCreate, MatchCreate, RatingCreate, NotificationCreate
from backend.database import SessionLocal, engine, Base
from backend.models import User, Profile, Item, Match, Rating, Notification

# Setup test database
@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
def test_create_user(test_db: Session):
    user_data = UserCreate(username="testuser", contact={"telegram": "@test"})
    created = create_user(test_db, user_data)
    # refresh the created instance so attributes are concrete Python types
    test_db.refresh(created)
    assert inspect(created).attrs.username.value == "testuser"
    # use SQLAlchemy inspect to get the Python value of the attribute (avoids SQL expression comparison)
    assert inspect(created).attrs.contact.value == {"telegram": "@test"}

def test_get_user_by_username(test_db: Session):
    user_data = UserCreate(username="testuser2", contact={"telegram": "@test2"})
    created_user = create_user(test_db, user_data)
    # ensure created_user attributes are concrete Python values
    test_db.refresh(created_user)
    retrieved_user = get_user_by_username(test_db, "testuser2")
    # ensure retrieved_user exists before accessing attributes
    assert retrieved_user is not None
    # refresh retrieved_user so attributes are concrete Python values
    test_db.refresh(retrieved_user)
    # compare Python id values (avoids comparing SQL expression objects)
    assert inspect(retrieved_user).attrs.id.value == inspect(created_user).attrs.id.value

def test_create_profile(test_db: Session):
    user = create_user(test_db, UserCreate(username="profileuser", contact={}))
    profile_data = ProfileCreate(
        user_id=inspect(user).attrs.id.value,
        name="Test Profile",
        category="Electronics",
        description="A test profile",
        avatar_url=None,
        location="Test City",
        visibility=True
    )
    profile = create_profile(test_db, profile_data)
    # refresh the created instance so attributes are concrete Python types
    test_db.refresh(profile)
    assert inspect(profile).attrs.user_id.value == inspect(user).attrs.id.value
    assert inspect(profile).attrs.name.value == "Test Profile"

def test_create_item(test_db: Session):
    user = create_user(test_db, UserCreate(username="itemuser", contact={}))
    # ensure user attributes are loaded as concrete Python values
    test_db.refresh(user)
    item_data = ItemCreate(
        user_id=inspect(user).attrs.id.value,
        kind=1,
        category="electronics",
        title="Test Item",
        description="A test item",
        item_metadata={},
        wants=["phone"],
        offers=["laptop"],
        active=True
    )
    item = create_item(test_db, item_data)
    # refresh the created instance so attributes are concrete Python types
    test_db.refresh(item)
    assert inspect(item).attrs.user_id.value == inspect(user).attrs.id.value
    assert inspect(item).attrs.title.value == "Test Item"

def test_create_rating(test_db: Session):
    user1 = create_user(test_db, UserCreate(username="rater", contact={}))
    user2 = create_user(test_db, UserCreate(username="rated", contact={}))
    # ensure username and id attributes are concrete Python values
    test_db.refresh(user1)
    test_db.refresh(user2)
    rating_data = RatingCreate(
        from_username=inspect(user1).attrs.username.value,
        to_username=inspect(user2).attrs.username.value,
        score=5,
        comment="Great!",
        tx_id="tx123"
    )
    rating = create_rating(test_db, rating_data)
    # If create_rating returned None, try to load the created rating from the DB by tx_id
    if rating is None:
        rating = test_db.query(Rating).filter_by(tx_id="tx123").first()
    # Ensure we have a rating before refreshing or accessing attributes
    assert rating is not None
    # refresh rating and compare against concrete id values
    test_db.refresh(rating)
    assert rating.from_user == inspect(user1).attrs.id.value
    assert inspect(rating).attrs.score.value == 5
    # Check trust score update
    updated_user = get_user(test_db, inspect(user2).attrs.id.value)
    # ensure the user was actually retrieved
    assert updated_user is not None
    # refresh the instance so attributes are concrete Python types
    test_db.refresh(updated_user)
    # compare the concrete Python trust_score value
    assert inspect(updated_user).attrs.trust_score.value == 5.0

def test_create_notification(test_db: Session):
    user = create_user(test_db, UserCreate(username="notifuser", contact={}))
    notif_data = NotificationCreate(
        user_id=inspect(user).attrs.id.value,
        channel="telegram",
        payload={"type": "test"},
        status="queued"
    )
    notif = create_notification(test_db, notif_data)
    # If create_notification returns None, try to retrieve the created notification from pending notifications
    if notif is None:
        user_id = inspect(user).attrs.id.value
        pending = get_pending_notifications(test_db)
        notif = next((n for n in pending if n.user_id == user_id), None)
    # Ensure we have a notification before accessing attributes
    assert notif is not None
    assert notif.user_id == inspect(user).attrs.id.value
    assert notif.payload == {"type": "test"}

def test_get_pending_notifications(test_db: Session):
    user = create_user(test_db, UserCreate(username="pendinguser", contact={}))
    create_notification(
        test_db,
        NotificationCreate(
            user_id=inspect(user).attrs.id.value,
            status="queued",
            payload={}  # Empty payload for now
        )
    )
    pending = get_pending_notifications(test_db)
    assert len(pending) >= 1
    assert any(n.user_id == inspect(user).attrs.id.value for n in pending)

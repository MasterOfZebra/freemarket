"""
End-to-end test for the complete barter flow:
1. Create offer
2. Match and find mutual match
3. Send notifications
"""

import pytest
from sqlalchemy.orm import Session
from backend.database import SessionLocal, redis_client
from backend.models import Item, User, Match, MutualMatch, Notification
from backend.schemas import ItemCreate, UserCreate
from backend.crud import create_user, create_item
from backend.tasks import enqueue_task, process_task_queue
from typing import cast
import json
import time
from decimal import Decimal


def test_complete_barter_flow():
    """Test the complete flow from offer creation to mutual match notification."""
    # Create tables for this test
    from backend.database import engine, Base
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    user1 = user2 = None
    item1 = item2 = item3 = None
    try:
        # Clear Redis
        redis_client.flushdb()
    finally:
        pass

    # Create two users
    user1_data = UserCreate(username="testuser1", contact={"phone": "contact1"})
    user2_data = UserCreate(username="testuser2", contact={"phone": "contact2"})

    user1 = create_user(db, user1_data)
    user2 = create_user(db, user2_data)
    db.commit()
    db.refresh(user1)
    db.refresh(user2)

    # IDs
    user1_id: int = cast(int, user1.id)
    user2_id: int = cast(int, user2.id)

    # User 1 creates an offer
    item1_data = ItemCreate(
        user_id=user1_id,
        title="Programming Services",
        description="I can help with Python development",
        category="services",
        kind=1,
        offers=["programming", "python"],
        wants=["laptop", "smartphone"],
        value_min=Decimal("50.0"),
        value_max=Decimal("200.0"),
    )
    item1 = create_item(db, item1_data)
    db.commit()
    db.refresh(item1)

    # User 2 creates a complementary offer
    item2_data = ItemCreate(
        user_id=user2_id,
        title="Used Laptop",
        description="Good condition laptop for sale",
        category="electronics",
        kind=1,
        offers=["laptop"],
        wants=["programming", "web_development"],
        value_min=Decimal("100.0"),
        value_max=Decimal("300.0"),
    )
    item2 = create_item(db, item2_data)
    db.commit()
    db.refresh(item2)

    item1_id: int = cast(int, item1.id)
    item2_id: int = cast(int, item2.id)

    # Process matching for item1
    enqueue_task("match_offer", {"offer_id": item1_id})
    process_task_queue()

    # Match should exist
    match = (
        db.query(Match)
        .filter(
            ((Match.item_a == item1_id) & (Match.item_b == item2_id))
            | ((Match.item_a == item2_id) & (Match.item_b == item1_id))
        )
        .first()
    )
    assert match is not None, "Match should be created"
    assert float(getattr(match, "score")) > 0.5, f"Match score should be > 0.5, got {getattr(match, 'score')}"

    # Create item3 from user1
    item3_data = ItemCreate(
        user_id=user1_id,
        title="Web Development Services",
        description="Full-stack web development",
        category="services",
        kind=1,
        offers=["web_development", "programming"],
        wants=["laptop"],
        value_min=Decimal("150.0"),
        value_max=Decimal("250.0"),
    )
    item3 = create_item(db, item3_data)
    db.commit()
    db.refresh(item3)
    item3_id: int = cast(int, item3.id)

    # Process matching for item3
    enqueue_task("match_offer", {"offer_id": item3_id})
    process_task_queue()

    # Mutual match check
    mutual_match = (
        db.query(MutualMatch)
        .filter(
            ((MutualMatch.item_a == item3_id) & (MutualMatch.item_b == item2_id))
            | ((MutualMatch.item_a == item2_id) & (MutualMatch.item_b == item3_id))
        )
        .first()
    )
    assert mutual_match is not None, "Mutual match should be created"

    # Notifications
    notifications = db.query(Notification).filter(
        Notification.user_id.in_([user1_id, user2_id])
    ).all()
    assert len(notifications) >= 2, f"Should have at least 2 notifications, got {len(notifications)}"

    notification_types = [n.payload.get("type") for n in notifications]
    assert "mutual_match" in notification_types, "Should have mutual_match notification"
    for n in notifications:
        if n.payload.get("type") == "mutual_match":
            partner_user = n.payload.get("partner_user", {})
            assert partner_user.get("contact"), "Partner contact must be present in mutual_match payload"

    print("✅ Complete barter flow test passed!")

    # Cleanup
    uids = []
    if user1 and getattr(user1, "id", None):
        uids.append(user1.id)
    if user2 and getattr(user2, "id", None):
        uids.append(user2.id)

    item_ids = []
    if item1 and getattr(item1, "id", None):
        item_ids.append(item1.id)
    if item2 and getattr(item2, "id", None):
        item_ids.append(item2.id)
    if item3 and getattr(item3, "id", None):
        item_ids.append(item3.id)

    if uids:
        db.query(Notification).filter(Notification.user_id.in_(uids)).delete(synchronize_session=False)

    if item_ids:
        db.query(MutualMatch).filter(
            (MutualMatch.item_a.in_(item_ids)) | (MutualMatch.item_b.in_(item_ids))
        ).delete(synchronize_session=False)
        db.query(Match).filter(
            (Match.item_a.in_(item_ids)) | (Match.item_b.in_(item_ids))
        ).delete(synchronize_session=False)
        db.query(Item).filter(Item.id.in_(item_ids)).delete(synchronize_session=False)

    if uids:
        db.query(User).filter(User.id.in_(uids)).delete(synchronize_session=False)

    db.commit()
    db.close()

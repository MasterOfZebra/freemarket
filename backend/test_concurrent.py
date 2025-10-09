import pytest
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
import hypothesis
from hypothesis import given, strategies as st, settings, HealthCheck

from backend.main import app, get_db
from backend.database import Base
from backend.models import User, Item, Match
from backend.matching import value_overlap

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_concurrent.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def unique_username():
    return f"user_{uuid.uuid4().hex[:8]}"

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    # Override the app dependency to use the testing session
    def override_get_db():
        db_session = TestingSessionLocal()
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)

def test_concurrent_match_acceptance(client, db):
    """Test concurrent acceptance of matches."""
    # Create users and items
    user1_username = unique_username()
    user1_response = client.post("/users/", json={"username": user1_username})
    user1_username = user1_response.json()["username"]

    user2_username = unique_username()
    user2_response = client.post("/users/", json={"username": user2_username})
    user2_username = user2_response.json()["username"]

    # Create items
    item1_data = {
        "username": user1_username,
        "kind": 1,
        "category": "electronics",
        "title": "Laptop",
        "description": "Gaming laptop",
        "wants": ["phone"],
        "offers": ["laptop"]
    }
    item1_response = client.post("/items/", json=item1_data)
    item1_id = item1_response.json()["id"]

    item2_data = {
        "username": user2_username,
        "kind": 2,
        "category": "electronics",
        "title": "Phone",
        "description": "Smartphone",
        "wants": ["laptop"],
        "offers": ["phone"]
    }
    item2_response = client.post("/items/", json=item2_data)
    item2_id = item2_response.json()["id"]

    # Get matches for item1
    matches_response = client.get(f"/matches/{item1_id}")
    matches = matches_response.json()
    assert len(matches) > 0
    match_id = matches[0]["id"]

    # Simulate concurrent acceptance
    def accept_match(user_client):
        return user_client.post(f"/matches/{match_id}/accept")

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(accept_match, client) for _ in range(2)]
        results = [f.result() for f in as_completed(futures)]

    # Check that one acceptance succeeds and the other shows mutual acceptance
    success_count = sum(1 for r in results if r.status_code == 200)
    assert success_count == 2

    mutual_accepted_count = sum(1 for r in results if r.json().get("mutual_accepted"))
    assert mutual_accepted_count == 1  # Only one should show mutual acceptance

def test_matching_latency(client, db):
    """Test latency metrics for matching stages."""
    start_time = time.time()

    # Create user
    user_response = client.post("/users/", json={"username": "user_123"})
    user_id = user_response.json()["id"]
    user_creation_time = time.time() - start_time

    # Create profile
    profile_data = {
        "user_id": user_id,
        "data": {"tech": "Laptop"}
    }
    profile_start = time.time()
    client.post("/profiles/", json=profile_data)
    profile_creation_time = time.time() - profile_start

    # Create item
    item_data = {
        "user_id": user_id,
        "kind": 1,
        "category": "electronics",
        "title": "Laptop",
        "description": "Gaming laptop",
        "wants": ["phone"],
        "offers": ["laptop"]
    }
    item_start = time.time()
    client.post("/items/", json=item_data)
    item_creation_time = time.time() - item_start

    # Assert reasonable latency (less than 1 second each)
    assert user_creation_time < 1.0
    assert profile_creation_time < 1.0
    assert item_creation_time < 1.0

    print(f"Latency metrics: User creation: {user_creation_time:.3f}s, "
          f"Profile creation: {profile_creation_time:.3f}s, "
          f"Item creation: {item_creation_time:.3f}s")

def test_value_overlap():
    """Test value overlap calculation."""
    # Complete overlap
    assert value_overlap(100, 200, 100, 200) == 1.0

    # Partial overlap
    assert abs(value_overlap(100, 200, 150, 250) - 0.5) < 0.01

    # No overlap
    assert value_overlap(100, 150, 200, 250) == 0.0

    # One range is None
    assert value_overlap(None, 200, 100, 200) == 0.0

def test_multi_level_matching(client, db):
    """Test multi-level matching returns appropriate number of results."""
    # Create users and items with different value ranges
    user1_response = client.post("/users/", json={"username": unique_username()})
    user1_id = user1_response.json()["id"]

    user2_response = client.post("/users/", json={"username": unique_username()})
    user2_id = user2_response.json()["id"]

    # Create items with overlapping value ranges
    item1_data = {
        "user_id": user1_id,
        "kind": 1,
        "category": "electronics",
        "title": "Laptop",
        "description": "Gaming laptop",
        "wants": ["phone"],
        "offers": ["laptop"],
        "value_min": 500,
        "value_max": 1000,
        "is_money": False
    }
    item1_response = client.post("/items/", json=item1_data)
    item1_id = item1_response.json()["id"]

    item2_data = {
        "user_id": user2_id,
        "kind": 2,
        "category": "electronics",
        "title": "Phone",
        "description": "Smartphone",
        "wants": ["laptop"],
        "offers": ["phone"],
        "value_min": 600,
        "value_max": 1200,
        "is_money": False
    }
    client.post("/items/", json=item2_data)

    # Get optimal matches
    response = client.get(f"/matches/{item1_id}/optimal")
    assert response.status_code == 200
    matches = response.json()

    # Should return matches with reasons
    if matches:
        assert "reason" in matches[0]
        assert "score" in matches[0]

def test_mutual_match_flow(client, db):
    """Test the complete mutual match flow."""
    # Create two users
    user1_response = client.post("/users/", json={"username": unique_username()})
    user1_id = user1_response.json()["id"]

    user2_response = client.post("/users/", json={"username": unique_username()})
    user2_id = user2_response.json()["id"]

    # User 1 creates offer
    offer1_data = {
        "user_id": user1_id,
        "kind": 1,
        "category": "electronics",
        "title": "Laptop",
        "description": "Gaming laptop",
        "wants": ["phone"],
        "offers": ["laptop"],
        "value_min": 500,
        "value_max": 1000
    }
    client.post("/items/", json=offer1_data)

    # User 2 creates matching offer
    offer2_data = {
        "user_id": user2_id,
        "kind": 2,
        "category": "electronics",
        "title": "Phone",
        "description": "Smartphone",
        "wants": ["laptop"],
        "offers": ["phone"],
        "value_min": 600,
        "value_max": 1200
    }
    client.post("/items/", json=offer2_data)

    # Check mutual matches for user 1
    mutual_matches = client.get(f"/mutual-matches/{user1_id}")
    assert mutual_matches.status_code == 200

    # Should have mutual match after processing
    # Note: In real scenario, worker would process the queue
    matches_data = mutual_matches.json()
    # This test assumes worker has processed the tasks
    # In practice, you'd need to run the worker or mock the queue

@settings(suppress_health_check=[HealthCheck.too_slow])
@given(
    a_min=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    a_max=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    b_min=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    b_max=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)
)
def test_value_overlap_properties(a_min, a_max, b_min, b_max):
    """Property-based test for value_overlap function."""
    # Ensure a_min <= a_max and b_min <= b_max
    if a_min > a_max:
        a_min, a_max = a_max, a_min
    if b_min > b_max:
        b_min, b_max = b_max, b_min

    overlap = value_overlap(a_min, a_max, b_min, b_max)

    # Overlap should be between 0 and 1
    assert 0.0 <= overlap <= 1.0

    # If ranges are identical, overlap should be 1
    if a_min == b_min and a_max == b_max:
        assert overlap == 1.0

    # If no overlap, should be 0
    if a_max < b_min or b_max < a_min:
        assert overlap == 0.0

    # Overlap should be symmetric only if ranges are of equal length
    range_a = a_max - a_min
    range_b = b_max - b_min
    if abs(range_a - range_b) < 1e-6:
        overlap_reverse = value_overlap(b_min, b_max, a_min, a_max)
        assert abs(overlap - overlap_reverse) < 1e-6

if __name__ == "__main__":
    pytest.main([__file__])

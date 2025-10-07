import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from main import app
from database import Base
from models import User, Profile

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_user(client, db):
    user_data = {"telegram_id": 123456789}
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_id"] == 123456789
    assert "id" in data

def test_create_profile(client, db):
    # First create a user
    user_response = client.post("/users/", json={"telegram_id": 123456789})
    user_id = user_response.json()["id"]

    # Create profile
    profile_data = {
        "user_id": user_id,
        "data": {
            "money": "1000 KZT",
            "tech": "Laptop"
        }
    }
    response = client.post("/profiles/", json=profile_data)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert data["data"]["money"] == "1000 KZT"

def test_get_profiles(client, db):
    # Create user and profile
    user_response = client.post("/users/", json={"telegram_id": 123456789})
    user_id = user_response.json()["id"]

    profile_data = {
        "user_id": user_id,
        "data": {"tech": "Phone"}
    }
    client.post("/profiles/", json=profile_data)

    # Get profiles
    response = client.get(f"/profiles/{user_id}")
    assert response.status_code == 200
    profiles = response.json()
    assert len(profiles) == 1
    assert profiles[0]["data"]["tech"] == "Phone"

def test_create_rating(client, db):
    # Create two users
    user1_response = client.post("/users/", json={"telegram_id": 111111111})
    user1_id = user1_response.json()["id"]

    user2_response = client.post("/users/", json={"telegram_id": 222222222})
    user2_id = user2_response.json()["id"]

    # Create rating
    rating_data = {
        "from_user": user1_id,
        "to_user": user2_id,
        "score": 5,
        "comment": "Great exchange!"
    }
    response = client.post("/ratings/", json=rating_data)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 5
    assert data["comment"] == "Great exchange!"

if __name__ == "__main__":
    pytest.main([__file__])

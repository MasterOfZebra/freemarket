"""User management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from backend.database import SessionLocal
from backend.crud import (
    get_user,
    create_user,
    update_user_locations,
    get_user_by_username,
)
from backend.schemas import UserCreate, User

router = APIRouter(prefix="/api/users", tags=["users"])


def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=User)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user with locations.

    Body:
    {
        "username": "alice",
        "contact": {"telegram": "@alice"},
        "locations": ["Алматы", "Астана"]
    }
    """
    existing = get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    return create_user(db, user)


@router.get("/{user_id}", response_model=User)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Get user profile by ID"""
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("/username/{username}", response_model=User)
def get_user_by_name(username: str, db: Session = Depends(get_db)):
    """Get user profile by username"""
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.put("/{user_id}/locations")
def update_locations(
    user_id: int,
    locations: List[str] = Query(..., description="List of locations: Алматы, Астана, Шымкент"),
    db: Session = Depends(get_db)
):
    """
    Update user's selected locations.

    Query Parameters:
        locations: List of selected cities
                  Example: ?locations=Алматы&locations=Астана

    Valid locations:
        - Алматы
        - Астана
        - Шымкент

    User must select at least one location.
    """
    try:
        updated_user = update_user_locations(db, user_id, locations)

        return {
            "success": True,
            "user_id": user_id,
            "locations": updated_user.locations,
            "message": f"Успешно обновлены локации: {', '.join(updated_user.locations)}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

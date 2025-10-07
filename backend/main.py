from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn

from .database import SessionLocal, engine
from .models import Base
from .schemas import *
from .crud import create_user as create_user_crud, create_profile as create_profile_crud, create_rating as create_rating_crud
from .crud import get_user_by_telegram, get_user, get_user_profiles, get_user_matches, get_user_ratings
from .matching import find_matches

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FreeMarket API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "FreeMarket API"}

# User endpoints
@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_telegram(db, telegram=user.telegram_id)  # Corrected attribute name
    if db_user:
        raise HTTPException(status_code=400, detail="Telegram already registered")
    return create_user_crud(db=db, user=user)

@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Profile endpoints
@app.post("/profiles/", response_model=Profile)
def create_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = get_user(db, user_id=profile.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create profile
    db_profile = create_profile_crud(db=db, profile=profile)

    # Trigger matching
    find_matches(db, profile.user_id)

    return db_profile

@app.get("/profiles/{user_id}", response_model=List[Profile])
def read_user_profiles(user_id: int, db: Session = Depends(get_db)):
    profiles = get_user_profiles(db, user_id=user_id)
    return profiles

# Item endpoints
@app.post("/items/", response_model=Item)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = get_user(db, user_id=item.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create item
    db_item = create_item_crud(db=db, item=item)

    # Trigger matching
    from .matching import match_for_item
    matches = match_for_item(db, db_item.id)
    for match in matches:
        create_match(db, MatchCreate(**match))

    return db_item

@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    # Check if item exists
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Update item
    for key, value in item.dict().items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)

    # Trigger matching
    from .matching import match_for_item
    matches = match_for_item(db, db_item.id)
    for match in matches:
        create_match(db, MatchCreate(**match))

    return db_item

@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

# Matches endpoints
@app.get("/matches/{item_id}", response_model=List[Match])
def read_item_matches(item_id: int, db: Session = Depends(get_db)):
    matches = db.query(Match).filter(
        (Match.item_a == item_id) | (Match.item_b == item_id)
    ).all()
    return matches

@app.post("/matches/{match_id}/accept")
def accept_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Logic for accept (simplified)
    match.status = "accepted"
    db.commit()
    return {"message": "Match accepted"}

@app.post("/matches/{match_id}/reject")
def reject_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Logic for reject
    match.status = "rejected"
    db.commit()
    return {"message": "Match rejected"}

# Ratings endpoints
@app.post("/ratings/", response_model=Rating)
def create_rating(rating: RatingCreate, db: Session = Depends(get_db)):
    return create_rating_crud(db=db, rating=rating)

@app.get("/ratings/{user_id}", response_model=List[Rating])
def read_user_ratings(user_id: int, db: Session = Depends(get_db)):
    ratings = get_user_ratings(db, user_id=user_id)
    return ratings

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

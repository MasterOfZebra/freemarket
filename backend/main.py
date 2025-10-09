from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, cast, Dict, Any
import uvicorn
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from .database import SessionLocal, engine
from .models import Base as ModelBase, Item as ItemModel, Match as MatchModel, Rating as RatingModel, Profile as ProfileModel, User as UserModel, Notification
from .schemas import (
    User,
    UserCreate,
    Profile,
    ProfileCreate,
    Item as ItemSchema,
    ItemCreate,
    Match as MatchSchema,
    MatchCreate,
    Rating,
    RatingCreate,
    NotificationCreate,
)
from .crud import create_user as create_user_crud, create_profile as create_profile_crud, create_rating as create_rating_crud, create_item as create_item_crud, create_match, create_notification
from .crud import get_user_by_username as get_user_by_telegram, get_user, get_user_profiles, get_user_matches, get_user_ratings
from .matching import find_matches, match_for_item
from .tasks import enqueue_task

# Create database tables
ModelBase.metadata.create_all(bind=engine)

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
class UserResponse(BaseModel):
    id: int
    username: str
    trust_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Duplicate check
    existing = db.query(UserModel).filter(UserModel.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    db_user = UserModel(username=user.username, contact=user.contact)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # Explicit response dict to ensure fields present
    return {
        "id": db_user.id,
        "username": db_user.username,
        "trust_score": db_user.trust_score or 0.0,
        "created_at": db_user.created_at,
    }


# --- username-based user endpoint ---
@app.get("/users/{username}", response_model=User)
def read_user(username: str, db: Session = Depends(get_db)):
    db_user = get_user_by_telegram(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Profile endpoints
@app.post("/profiles/", response_model=Profile)
def create_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    # Resolve username to user_id or accept user_id directly
    user = None
    if getattr(profile, "username", None):
        user = db.query(UserModel).filter(UserModel.username == profile.username).first()
    elif getattr(profile, "user_id", None) is not None:
        user = db.query(UserModel).filter(UserModel.id == profile.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent duplicate profile per user
    existing_profile = db.query(ProfileModel).filter(ProfileModel.user_id == user.id).first()
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists")

    db_profile = ProfileModel(
        user_id=user.id,
        name=profile.name,
        category=profile.category,
        description=profile.description,
        avatar_url=profile.avatar_url,
        location=profile.location,
        visibility=profile.visibility,
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    # Include username in response
    result = {
        "id": db_profile.id,
        "user_id": db_profile.user_id,
        "username": user.username,
        "name": db_profile.name,
        "category": db_profile.category,
        "description": db_profile.description,
        "avatar_url": db_profile.avatar_url,
        "location": db_profile.location,
        "visibility": db_profile.visibility,
        "created_at": db_profile.created_at,
        "updated_at": db_profile.updated_at,
    }
    return result


# --- username-based profile endpoint ---
@app.get("/profiles/{username}", response_model=Profile)
def get_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = db.query(ProfileModel).filter(ProfileModel.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Add username to the profile data
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "username": user.username,
        "name": profile.name,
        "category": profile.category,
        "description": profile.description,
        "avatar_url": profile.avatar_url,
        "location": profile.location,
        "visibility": profile.visibility,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


# --- username-based profiles list endpoint ---
@app.get("/profiles/{username}/all", response_model=List[Profile])
def read_user_profiles(username: str, db: Session = Depends(get_db)):
    user = get_user_by_telegram(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Ensure user.id is treated as a plain int for the get_user_profiles call
    user_id_val: int = cast(int, user.id)
    profiles = get_user_profiles(db, user_id=user_id_val)
    # Enrich with username for response model compatibility
    result = []
    for p in profiles:
        result.append({
            "id": p.id,
            "user_id": p.user_id,
            "username": user.username,
            "name": p.name,
            "category": p.category,
            "description": p.description,
            "avatar_url": p.avatar_url,
            "location": p.location,
            "visibility": p.visibility,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        })
    return result


# --- username-based profile update endpoint ---
@app.put("/profiles/{username}", response_model=Profile)
def update_profile(username: str, profile: ProfileCreate, db: Session = Depends(get_db)):
    user = get_user_by_telegram(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db_profile = db.query(ProfileModel).filter(ProfileModel.user_id == user.id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    # Only allow updating profile fields, not user linkage
    update_fields = {k: v for k, v in profile.dict().items() if k in {
        "name", "category", "description", "avatar_url", "location", "visibility"
    } and v is not None}
    for key, value in update_fields.items():
        setattr(db_profile, key, value)
    db.commit()
    db.refresh(db_profile)
    # Return enriched response with username
    return {
        "id": db_profile.id,
        "user_id": db_profile.user_id,
        "username": user.username,
        "name": db_profile.name,
        "category": db_profile.category,
        "description": db_profile.description,
        "avatar_url": db_profile.avatar_url,
        "location": db_profile.location,
        "visibility": db_profile.visibility,
        "created_at": db_profile.created_at,
        "updated_at": db_profile.updated_at,
    }

# Item endpoints
class ItemResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    # Resolve user by username or user_id to support different ItemCreate shapes
    username = getattr(item, "username", None)
    user = None
    if username:
        user = db.query(UserModel).filter(UserModel.username == username).first()
    else:
        user_id = getattr(item, "user_id", None)
        if user_id is not None:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_item = ItemModel(
        user_id=user.id,
        title=item.title,
        description=item.description,
        category=item.category,
        kind=item.kind,
        offers=getattr(item, "offers", None),
        wants=getattr(item, "wants", None)
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # Trigger matching for the new item
    try:
        from .matching import find_candidates, score_candidates
        candidates = find_candidates(db, db_item)
        if candidates:
            scored_matches = score_candidates(db_item, candidates)
            # Create top matches
            for match_data in scored_matches[:5]:
                try:
                    match = MatchModel(
                        item_a=match_data["item_a"],
                        item_b=match_data["item_b"],
                        score=match_data["score"],
                        computed_by=match_data.get("computed_by", "auto"),
                        status="new"
                    )
                    db.add(match)
                except Exception as e:
                    pass  # Skip failed matches
            db.commit()
    except Exception as e:
        pass  # Don't fail item creation if matching fails

    return {
        "id": db_item.id,
        "user_id": db_item.user_id,
        "title": db_item.title,
        "description": db_item.description,
        "created_at": db_item.created_at,
    }

@app.put("/items/{item_id}", response_model=ItemSchema)
def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(ItemModel).filter(ItemModel.id == item_id).one_or_none()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in item.dict().items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    # Ensure id is an int for typing
    item_id_val: int | None = cast(int, db_item.id) if db_item.id is not None else None
    # Enqueue background matching task
    if item_id_val is not None:
        enqueue_task("match_for_item", {"item_id": item_id_val})
    return db_item

@app.get("/items/{item_id}", response_model=ItemSchema)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

# Matches endpoints
@app.get("/matches/{item_id}", response_model=List[MatchSchema])
def read_item_matches(item_id: int, db: Session = Depends(get_db)):
    matches = db.query(MatchModel).filter(
        (MatchModel.item_a == item_id) | (MatchModel.item_b == item_id)
    ).all()
    return matches

class AcceptMatchResponse(BaseModel):
    message: str
    mutual_accepted: bool
    status: Optional[str]

@app.post("/matches/{match_id}/accept", response_model=AcceptMatchResponse)
def accept_match(match_id: int, db: Session = Depends(get_db)):
    # Ensure match exists
    match = db.query(MatchModel).filter(MatchModel.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Try to atomically move from 'new' -> 'accepted_a'
    updated = db.query(MatchModel).filter(
        MatchModel.id == match_id,
        MatchModel.status == 'new'
    ).update({"status": 'accepted_a'})
    if updated:
        db.commit()
        match = db.query(MatchModel).filter(MatchModel.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        return {"message": "Match accepted", "mutual_accepted": False, "status": getattr(match, "status", None)}

    # Try to atomically move from 'accepted_a' -> 'matched'
    updated = db.query(MatchModel).filter(
        MatchModel.id == match_id,
        MatchModel.status == 'accepted_a'
    ).update({"status": 'matched', "matched_at": datetime.utcnow()})
    if updated:
        db.commit()
        match = db.query(MatchModel).filter(MatchModel.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        return {"message": "Match accepted", "mutual_accepted": True, "status": getattr(match, "status", None)}

    # Try to atomically move from 'accepted_b' -> 'matched'
    updated = db.query(MatchModel).filter(
        MatchModel.id == match_id,
        MatchModel.status == 'accepted_b'
    ).update({"status": 'matched', "matched_at": datetime.utcnow()})
    if updated:
        db.commit()
        match = db.query(MatchModel).filter(MatchModel.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        return {"message": "Match accepted", "mutual_accepted": True, "status": getattr(match, "status", None)}

    # If we reach here, either status was already 'matched' or an unexpected state
    match = db.query(MatchModel).filter(MatchModel.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    mutual_accepted = getattr(match, "status", None) == 'matched'
    return {"message": "Match accepted", "mutual_accepted": mutual_accepted, "status": getattr(match, "status", None)}

class SimpleMessageResponse(BaseModel):
    message: str

@app.post("/matches/{match_id}/reject", response_model=SimpleMessageResponse)
def reject_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(MatchModel).filter(MatchModel.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    setattr(match, "status", "rejected")
    db.commit()
    return {"message": "Match rejected"}

# Ratings endpoints
@app.post("/ratings/", response_model=Rating)
def create_rating(rating: RatingCreate, db: Session = Depends(get_db)):
    return create_rating_crud(db=db, rating=rating)

@app.get("/ratings/{username}", response_model=List[Rating])
def read_user_ratings(username: str, db: Session = Depends(get_db)):
    user = get_user_by_telegram(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Ensure user.id is treated as a plain int for the get_user_ratings call
    user_id_val: int = cast(int, user.id)
    ratings = get_user_ratings(db, user_id=user_id_val)
    return ratings

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/matches/{item_id}/optimal", response_model=List[Dict[str, Any]])
def get_optimal_matches(item_id: int, db: Session = Depends(get_db)):
    """Get optimal matches for an item with reasons."""
    from .matching import match_for_item
    matches = match_for_item(db, item_id)
    return matches

@app.get("/mutual-matches/{username}", response_model=List[Dict[str, Any]])
def get_mutual_matches(username: str, db: Session = Depends(get_db)):
    # Allow numeric user id in place of username for backward-compat tests
    user = None
    if username.isdigit():
        user = db.query(UserModel).filter(UserModel.id == int(username)).first()
    if not user:
        user = get_user_by_telegram(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user.id
    mutual_matches = db.query(MatchModel).filter(
        (MatchModel.item_a.in_(
            db.query(ItemModel.id).filter(ItemModel.user_id == user_id)
        )) | (MatchModel.item_b.in_(
            db.query(ItemModel.id).filter(ItemModel.user_id == user_id)
        ))
    ).all()

    result = []
    for mm in mutual_matches:
        item_a = db.query(ItemModel).filter(ItemModel.id == mm.item_a).first()
        item_b = db.query(ItemModel).filter(ItemModel.id == mm.item_b).first()
        if item_a and item_b:
            user_a = db.query(UserModel).filter(UserModel.id == item_a.user_id).first()
            user_b = db.query(UserModel).filter(UserModel.id == item_b.user_id).first()
            result.append({
                "mutual_match_id": mm.id,
                "item_a": {
                    "id": item_a.id,
                    "title": item_a.title,
                    "username": user_a.username if user_a else None
                },
                "item_b": {
                    "id": item_b.id,
                    "title": item_b.title,
                    "username": user_b.username if user_b else None
                },
                "matched_at": mm.matched_at
            })

    return result

# Notification worker
from sqlalchemy.orm import Session

def notification_worker(db: Session):
    new_notifications = db.query(Notification).filter(Notification.is_sent.is_(False)).all()
    for n in new_notifications:
        # Extract values directly from the database object and cast to plain Python types
        user_id = cast(int, n.user_id)  # Ensure static type is int
        message = cast(str, n.message)  # Ensure static type is str

        # Ensure channel is a plain Python string before comparing
        channel_attr = getattr(n, "channel", None)
        channel = str(channel_attr) if channel_attr is not None else ""

        if channel == "telegram":
            send_telegram_message(user_id, message)
        elif channel == "web":
            push_to_frontend(user_id, message)
        elif channel == "email":
            send_email(user_id, message)

        n.is_sent = cast(bool, True)  # Mark as sent (cast to satisfy type checker)
    db.commit()

def send_telegram_message(user_id: int, message: str):
    # Ensure proper type handling for user_id and message
    if not isinstance(user_id, int):
        raise ValueError("user_id must be an integer")
    if not isinstance(message, str):
        raise ValueError("message must be a string")

    # Placeholder for Telegram API integration
    print(f"Sending Telegram message to user {user_id}: {message}")

def push_to_frontend(user_id: int, message: str):
    # Placeholder for WebSocket or push notification integration
    print(f"Pushing notification to frontend for user {user_id}: {message}")

def send_email(user_id: int, message: str):
    # Placeholder for email sending logic
    print(f"Sending email to user {user_id}: {message}")

def create_barter_notification(db: Session, barter):
    # Generate notification for the recipient
    message = f"You have a new barter proposal from {barter.from_user.username}: {barter.offer_item} → {barter.request_item}"
    notification = Notification(
        user_id=barter.to_user.id,
        message=message,
        channel="telegram"
    )
    db.add(notification)
    db.commit()

class MatchSearchResult(BaseModel):
    item_a: int
    item_b: int
    score: float
    category: str
    offers_a: list[str]
    wants_a: list[str]
    offers_b: list[str]
    wants_b: list[str]

@app.get("/matches/search/", response_model=List[MatchSearchResult])
def search_matches(
    category: Optional[str] = None,
    location: Optional[str] = None,
    username: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Advanced search for matches by offers/wants, category, location, status, актуальность.
    Returns sorted list of matches with score.
    """
    # 1. Найти пользователя (если задан username)
    user = None
    if username:
        # Use the SQLAlchemy User model (imported as UserModel) instead of the Pydantic/schema User
        user = db.query(ProfileModel).join(UserModel).filter(UserModel.username == username).first()

    # 2. Собрать все активные items (фильтры)
    query = db.query(ItemModel).filter(ItemModel.active == True)
    if category:
        query = query.filter(ItemModel.category == category)
    if location:
        # location фильтр по профилю пользователя
        user_ids = [p.user_id for p in db.query(ProfileModel).filter(ProfileModel.location == location).all()]
        query = query.filter(ItemModel.user_id.in_(user_ids))
    items = query.all()

    # 3. Для каждого item ищем потенциальные совпадения по offers/wants
    results = []
    for item in items:
        # Пропускать неактуальные (например, с истёкшим сроком)
        # if item.expires_at and item.expires_at < datetime.utcnow():
        #     continue
        # Для каждого item ищем совпадения с другими пользователями
        candidates = db.query(ItemModel).filter(
            ItemModel.id != item.id,
            ItemModel.active == True,
            ItemModel.category == item.category,
            ItemModel.user_id != item.user_id
        ).all()
        for candidate in candidates:
            # Совпадение по offers/wants (пересечение)
            # Safely extract and normalize offers/wants to plain Python iterables
            offers_raw = getattr(item, "offers", None)
            wants_raw = getattr(item, "wants", None)
            c_offers_raw = getattr(candidate, "offers", None)
            c_wants_raw = getattr(candidate, "wants", None)

            offers = set(offers_raw) if isinstance(offers_raw, (list, tuple, set)) else set()
            wants = set(wants_raw) if isinstance(wants_raw, (list, tuple, set)) else set()
            c_offers = set(c_offers_raw) if isinstance(c_offers_raw, (list, tuple, set)) else set()
            c_wants = set(c_wants_raw) if isinstance(c_wants_raw, (list, tuple, set)) else set()

            # A.offers <-> B.wants и B.offers <-> A.wants
            score = 0
            if offers & c_wants:
                score += 0.6
            if c_offers & wants:
                score += 0.6
            # Категория совпадает — бонус (use plain Python values to avoid SQLAlchemy ColumnElement truthiness)
            category_a = getattr(item, "category", None)
            category_b = getattr(candidate, "category", None)
            if category_a is not None and category_b is not None and str(category_a) == str(category_b):
                score += 0.2
            # TODO: добавить веса за location, статус, актуальность
            # Собрать результат
            if score > 0:
                results.append({
                    "item_a": item.id,
                    "item_b": candidate.id,
                    "score": round(score, 3),
                    "category": item.category,
                    "offers_a": list(offers),
                    "wants_a": list(wants),
                    "offers_b": list(c_offers),
                    "wants_b": list(c_wants),
                })
    # 4. Отсортировать по score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

class BarterResponse(BaseModel):
    message: str
    match_id: int

@app.post("/barter/propose/", response_model=BarterResponse)
def propose_barter(from_username: str, to_username: str, offer_item: int, request_item: int, db: Session = Depends(get_db)):
    """Propose a barter exchange."""
    # Check if users exist
    from_user_obj = get_user_by_telegram(db, username=from_username)
    to_user_obj = get_user_by_telegram(db, username=to_username)
    if not from_user_obj or not to_user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if items exist and belong to users
    offer_item_obj = db.query(ItemModel).filter(ItemModel.id == offer_item, ItemModel.user_id == from_user_obj.id).first()
    request_item_obj = db.query(ItemModel).filter(ItemModel.id == request_item, ItemModel.user_id == to_user_obj.id).first()
    if not offer_item_obj or not request_item_obj:
        raise HTTPException(status_code=404, detail="Item not found or not owned by user")

    # Create barter proposal (perhaps use Match or a new model)
    # For simplicity, create a match
    match = MatchModel(
        item_a=offer_item,
        item_b=request_item,
        score=1.0,  # Direct proposal
        computed_by="direct_proposal",
        status="proposed"
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    # Create notification
    create_notification(db, NotificationCreate(
        user_id=cast(int, to_user_obj.id),
        payload={
            "type": "barter_proposal",
            "from_user": from_username,
            "offer_item": offer_item,
            "request_item": request_item,
            "match_id": match.id
        }
    ))

    return {"message": "Barter proposed", "match_id": match.id}

# Reuse the earlier SimpleMessageResponse definition; duplicate removed

@app.post("/barter/{barter_id}/accept", response_model=SimpleMessageResponse)
def accept_barter(barter_id: int, db: Session = Depends(get_db)):
    """Accept a barter proposal."""
    match = db.query(MatchModel).filter(MatchModel.id == barter_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Barter not found")

    # Ensure we compare a plain Python value (string) to avoid constructing a SQL expression
    status_val = getattr(match, "status")
    if str(status_val) != "proposed":
        raise HTTPException(status_code=400, detail="Barter not in proposed state")

    # Use setattr to avoid assigning a literal directly to an instrumented SQLAlchemy attribute
    setattr(match, "status", "accepted")
    db.commit()

    # Create notification for proposer
    proposer_item = db.query(ItemModel).filter(ItemModel.id == match.item_a).first()
    if proposer_item:
        create_notification(db, NotificationCreate(
            user_id=cast(int, proposer_item.user_id),
            payload={
                "type": "barter_accepted",
                "barter_id": barter_id
            }
        ))

    return {"message": "Barter accepted"}

@app.post("/barter/{barter_id}/decline", response_model=SimpleMessageResponse)
def decline_barter(barter_id: int, db: Session = Depends(get_db)):
    """Decline a barter proposal."""
    match = db.query(MatchModel).filter(MatchModel.id == barter_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Barter not found")
    status_val = getattr(match, "status")
    if str(status_val) != "proposed":
        raise HTTPException(status_code=400, detail="Barter not in proposed state")
    setattr(match, "status", "declined")
    db.commit()
    # Create notification for proposer
    proposer_item = db.query(ItemModel).filter(ItemModel.id == match.item_a).first()
    if proposer_item:
        create_notification(db, NotificationCreate(
            user_id=cast(int, proposer_item.user_id),
            payload={
                "type": "barter_declined",
                "barter_id": barter_id
            }
        ))
    return {"message": "Barter declined"}

@app.get("/notifications/{username}")
def get_notifications(username: str, db: Session = Depends(get_db)):
    """Get notifications for a user."""
    user = get_user_by_telegram(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    notifications = db.query(Notification).filter(Notification.user_id == user.id).all()
    return notifications

@app.put("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark a notification as read."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}

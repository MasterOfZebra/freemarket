"""Market listings endpoints (wants and offers)"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import SessionLocal
from backend.models import MarketListing, Item
from backend.schemas import MarketListingResponse, MarketListingCreate as MarketListingCreateSchema, Item as ItemResponse, ItemCreate
from backend.crud import get_market_listings, create_market_listing, get_items

router = APIRouter(prefix="/api/market-listings", tags=["market-listings"])

# Additional router for direct item access (frontend compatibility)
items_router = APIRouter(tags=["items"])


def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/wants/all", response_model=dict)
def list_wants(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get all wants/requests from users"""
    items, total = get_market_listings(
        db,
        skip=skip,
        limit=limit,
        listing_type="wants"
    )
    return {
        "items": [MarketListingResponse.from_orm(item).model_dump() if hasattr(item, '__table__') else item for item in items],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/offers/all", response_model=dict)
def list_offers(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get all offers from users"""
    items, total = get_market_listings(
        db,
        skip=skip,
        limit=limit,
        listing_type="offers"
    )
    return {
        "items": [MarketListingResponse.from_orm(item).model_dump() if hasattr(item, '__table__') else item for item in items],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/", response_model=MarketListingResponse)
def create_listing(listing: MarketListingCreateSchema, db: Session = Depends(get_db)):
    """Create a new market listing (want or offer)"""
    return create_market_listing(db, listing)




# Items endpoints for frontend compatibility
@items_router.get("/items/", response_model=List[ItemResponse])
def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all items (for frontend compatibility)"""
    items = get_items(db, skip=skip, limit=limit)
    return [ItemResponse.from_orm(item).model_dump() for item in items]


@items_router.post("/items/", response_model=ItemResponse)
def create_item_endpoint(item: ItemCreate, db: Session = Depends(get_db)):
    """Create a new item (for frontend compatibility)"""
    from backend.crud import create_item as crud_create_item
    return crud_create_item(db, item)


# Wants and offers endpoints for frontend compatibility
@items_router.get("/wants/", response_model=dict)
def get_wants_frontend(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get all wants (for frontend compatibility)"""
    items, total = get_market_listings(
        db,
        skip=skip,
        limit=limit,
        listing_type="wants"
    )
    return {
        "items": [MarketListingResponse.from_orm(item).model_dump() if hasattr(item, '__table__') else item for item in items],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@items_router.get("/offers/", response_model=dict)
def get_offers_frontend(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get all offers (for frontend compatibility)"""
    items, total = get_market_listings(
        db,
        skip=skip,
        limit=limit,
        listing_type="offers"
    )
    return {
        "items": [MarketListingResponse.from_orm(item).model_dump() if hasattr(item, '__table__') else item for item in items],
        "total": total,
        "skip": skip,
        "limit": limit
    }


# Export both routers
__all__ = ["router", "items_router"]

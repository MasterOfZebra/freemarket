"""Market listings endpoints (wants and offers)"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import SessionLocal
from backend.models import MarketListing
from backend.schemas import MarketListingResponse, MarketListingCreate as MarketListingCreateSchema
from backend.crud import get_market_listings, create_market_listing

router = APIRouter(prefix="/api/market-listings", tags=["market-listings"])


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

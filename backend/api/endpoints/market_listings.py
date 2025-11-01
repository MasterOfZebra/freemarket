"""Market listings endpoints (wants and offers)"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import SessionLocal
from backend.models import MarketListing, Item
from backend.schemas import MarketListingResponse, MarketListingCreate as MarketListingCreateSchema
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
@items_router.get("/items/")
def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all items (for frontend compatibility)"""
    try:
        items = get_items(db, skip=skip, limit=limit)
        # Convert to simple dict format
        result = []
        for item in items:
            result.append({
                "id": item.id,
                "user_id": item.user_id,
                "kind": item.kind,
                "category": item.category,
                "title": item.title,
                "description": item.description,
                "active": item.active,
                "created_at": item.created_at.isoformat() if item.created_at else None
            })
        return result
    except Exception as e:
        # Return empty list if database error
        return []


@items_router.post("/items/")
def create_item_endpoint(item_data: dict, db: Session = Depends(get_db)):
    """Create a new item (for frontend compatibility)"""
    try:
        from backend.crud import create_item
        from backend.schemas import ItemCreate

        # Convert dict to ItemCreate schema
        item = ItemCreate(**item_data)
        created_item = create_item(db, item)

        return {
            "id": created_item.id,
            "user_id": created_item.user_id,
            "kind": created_item.kind,
            "category": created_item.category,
            "title": created_item.title,
            "description": created_item.description,
            "active": created_item.active,
            "created_at": created_item.created_at.isoformat() if created_item.created_at else None
        }
    except Exception as e:
        return {"error": str(e)}


# Debug endpoint to test routing
@items_router.get("/test/")
def test_endpoint():
    """Test endpoint to verify routing works"""
    return {"message": "API routing works!", "status": "ok"}

# Wants and offers endpoints for frontend compatibility
@items_router.get("/wants/")
def get_wants_frontend(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get all wants (for frontend compatibility)"""
    try:
        items, total = get_market_listings(
            db,
            skip=skip,
            limit=limit,
            listing_type="wants"
        )
        # Convert to simple dict format
        items_list = []
        for item in items:
            items_list.append({
                "id": item.id if hasattr(item, 'id') else None,
                "title": getattr(item, 'title', ''),
                "description": getattr(item, 'description', ''),
                "category": getattr(item, 'category', ''),
                "price": getattr(item, 'price', 0),
                "user_id": getattr(item, 'user_id', None),
                "created_at": item.created_at.isoformat() if hasattr(item, 'created_at') and item.created_at else None
            })

        return {
            "items": items_list,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        # Return empty result if database error
        return {
            "items": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
            "error": str(e)
        }


@items_router.get("/offers/")
def get_offers_frontend(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get all offers (for frontend compatibility)"""
    try:
        items, total = get_market_listings(
            db,
            skip=skip,
            limit=limit,
            listing_type="offers"
        )
        # Convert to simple dict format
        items_list = []
        for item in items:
            items_list.append({
                "id": item.id if hasattr(item, 'id') else None,
                "title": getattr(item, 'title', ''),
                "description": getattr(item, 'description', ''),
                "category": getattr(item, 'category', ''),
                "price": getattr(item, 'price', 0),
                "user_id": getattr(item, 'user_id', None),
                "created_at": item.created_at.isoformat() if hasattr(item, 'created_at') and item.created_at else None
            })

        return {
            "items": items_list,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        # Return empty result if database error
        return {
            "items": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
            "error": str(e)
        }


# Export both routers
__all__ = ["router", "items_router"]

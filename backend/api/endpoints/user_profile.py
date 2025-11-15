"""
User profile and personal cabinet API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional, Dict

from backend.database import get_db
from backend.models import User, Listing, ListingItem, ExchangeType
from backend.schemas import UserProfile
from backend.auth import get_current_user, get_current_user_optional


router = APIRouter()


# Additional schemas for user cabinet
from pydantic import BaseModel
from datetime import datetime


class ListingSummary(BaseModel):
    """Summary of user's listing"""
    id: int
    title: Optional[str]
    description: Optional[str]
    created_at: datetime
    total_wants: int
    total_offers: int
    exchange_types: List[str]  # ["permanent", "temporary"]

    class Config:
        from_attributes = True


class ExchangeSummary(BaseModel):
    """Summary of active exchange"""
    id: int
    partner_name: Optional[str]
    partner_telegram: Optional[str]
    status: str
    created_at: datetime
    exchange_type: str
    category: str
    value_tenge: int

    class Config:
        from_attributes = True


class UserCabinetResponse(BaseModel):
    """Complete user cabinet data"""
    profile: UserProfile
    my_listings: List[ListingSummary]
    active_exchanges: List[ExchangeSummary]  # Placeholder for future implementation


@router.get("/cabinet", response_model=UserCabinetResponse)
async def get_user_cabinet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete user cabinet data:
    - User profile
    - My listings with summary
    - Active exchanges (placeholder for now)
    """
    try:
        # Get user's listings with items (only non-archived items)
        listings = db.query(Listing).options(
            joinedload(Listing.items)
        ).filter(
            Listing.user_id == current_user.id
        ).order_by(Listing.created_at.desc()).all()

        # Build listing summaries
        listing_summaries = []
        for listing in listings:
            # Count items by type and exchange type (only non-archived items)
            wants_count = 0
            offers_count = 0
            exchange_types = set()

            for item in listing.items:
                # Skip archived items
                if item.is_archived:
                    continue
                    
                if item.item_type.value == "want":
                    wants_count += 1
                elif item.item_type.value == "offer":
                    offers_count += 1
                exchange_types.add(item.exchange_type.value)
            
            # Only include listings that have at least one non-archived item
            if wants_count > 0 or offers_count > 0:

            listing_summaries.append(ListingSummary(
                id=listing.id,
                title=listing.title,
                description=listing.description,
                created_at=listing.created_at,
                total_wants=wants_count,
                total_offers=offers_count,
                exchange_types=list(exchange_types)
            ))

        # For now, return empty active exchanges
        # TODO: Implement when exchanges/matches are fully implemented
        active_exchanges = []

        return UserCabinetResponse(
            profile=UserProfile.from_orm(current_user),
            my_listings=listing_summaries,
            active_exchanges=active_exchanges
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load cabinet: {str(e)}")


@router.get("/listings", response_model=List[ListingSummary])
async def get_my_listings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's listings with summary information
    """
    try:
        listings = db.query(Listing).options(
            joinedload(Listing.items)
        ).filter(
            Listing.user_id == current_user.id
        ).order_by(Listing.created_at.desc()).all()

        result = []
        for listing in listings:
            wants_count = 0
            offers_count = 0
            exchange_types = set()

            for item in listing.items:
                if item.item_type.value == "want":
                    wants_count += 1
                elif item.item_type.value == "offer":
                    offers_count += 1
                exchange_types.add(item.exchange_type.value)

            result.append(ListingSummary(
                id=listing.id,
                title=listing.title,
                description=listing.description,
                created_at=listing.created_at,
                total_wants=wants_count,
                total_offers=offers_count,
                exchange_types=list(exchange_types)
            ))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load listings: {str(e)}")


@router.get("/exchanges", response_model=List[ExchangeSummary])
async def get_active_exchanges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's active exchanges (placeholder for future implementation)
    TODO: Implement when exchange/matching system is complete
    """
    # For now, return empty list
    # This will be implemented when the matching/exchange system is built
    return []


@router.get("/profile")
def get_profile(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get current user profile information
    """
    if not current_user:
        return {"error": "Authentication required"}
    return UserProfile.from_orm(current_user)


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    profile_data: dict,  # Will be replaced with proper schema
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information
    """
    try:
        # Allow updating safe profile fields
        allowed_fields = {
            'full_name', 'telegram_contact', 'city', 'bio'
        }

        for field, value in profile_data.items():
            if field in allowed_fields:
                setattr(current_user, field, value)

        current_user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(current_user)

        return UserProfile.from_orm(current_user)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete user account (soft delete - mark as inactive)
    """
    try:
        # Soft delete - just mark as inactive
        current_user.is_active = False
        current_user.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {"message": "Account deactivated successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")


# Import datetime for update_profile
from datetime import datetime, timezone

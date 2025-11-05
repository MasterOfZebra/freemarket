"""
Categories API endpoints
Provides versioned category system for dynamic forms and validation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from pydantic import BaseModel

from backend.database import get_db
from backend.models import CategoryV6, CategoryVersion, ExchangeType


router = APIRouter()


# Pydantic schemas
class CategoryResponse(BaseModel):
    slug: str
    name: str
    group: str
    emoji: str
    sort_order: int
    form_schema: Optional[dict] = None

    class Config:
        from_attributes = True


class CategoriesByExchangeType(BaseModel):
    permanent: List[CategoryResponse]
    temporary: List[CategoryResponse]


class CategoriesVersionResponse(BaseModel):
    version: str
    description: Optional[str]
    categories: CategoriesByExchangeType


@router.get("/categories", response_model=CategoriesVersionResponse)
async def get_categories(
    version: str = Query("v6.0", description="Category system version"),
    db: Session = Depends(get_db)
):
    """
    Get categories for the specified version.
    Returns categories organized by exchange type for dynamic form generation.
    """
    # Get the requested version
    category_version = db.query(CategoryVersion).filter(
        and_(
            CategoryVersion.version == version,
            CategoryVersion.is_active == True
        )
    ).first()

    if not category_version:
        raise HTTPException(
            status_code=404,
            detail=f"Category version '{version}' not found or not active"
        )

    # Get all active categories for this version
    categories = db.query(CategoryV6).filter(
        and_(
            CategoryV6.version_id == category_version.id,
            CategoryV6.is_active == True
        )
    ).order_by(CategoryV6.sort_order).all()

    # Organize by exchange type
    permanent_categories = []
    temporary_categories = []

    for cat in categories:
        cat_response = CategoryResponse.from_orm(cat)
        if cat.exchange_type == ExchangeType.PERMANENT:
            permanent_categories.append(cat_response)
        elif cat.exchange_type == ExchangeType.TEMPORARY:
            temporary_categories.append(cat_response)

    return CategoriesVersionResponse(
        version=category_version.version,
        description=category_version.description,
        categories=CategoriesByExchangeType(
            permanent=permanent_categories,
            temporary=temporary_categories
        )
    )


@router.get("/categories/{exchange_type}", response_model=List[CategoryResponse])
async def get_categories_by_type(
    exchange_type: str,
    version: str = Query("v6.0", description="Category system version"),
    db: Session = Depends(get_db)
):
    """
    Get categories for a specific exchange type.
    Used for populating form dropdowns and validation.
    """
    try:
        exchange_enum = ExchangeType(exchange_type.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid exchange type. Must be 'permanent' or 'temporary'"
        )

    # Get the requested version
    category_version = db.query(CategoryVersion).filter(
        and_(
            CategoryVersion.version == version,
            CategoryVersion.is_active == True
        )
    ).first()

    if not category_version:
        raise HTTPException(
            status_code=404,
            detail=f"Category version '{version}' not found or not active"
        )

    # Get categories for the specific exchange type
    categories = db.query(CategoryV6).filter(
        and_(
            CategoryV6.version_id == category_version.id,
            CategoryV6.exchange_type == exchange_enum,
            CategoryV6.is_active == True
        )
    ).order_by(CategoryV6.sort_order).all()

    return [CategoryResponse.from_orm(cat) for cat in categories]


@router.get("/categories/groups/{exchange_type}")
async def get_category_groups(
    exchange_type: str,
    version: str = Query("v6.0", description="Category system version"),
    db: Session = Depends(get_db)
):
    """
    Get unique category groups for a specific exchange type.
    Useful for organizing UI sections.
    """
    try:
        exchange_enum = ExchangeType(exchange_type.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid exchange type. Must be 'permanent' or 'temporary'"
        )

    # Get the requested version
    category_version = db.query(CategoryVersion).filter(
        and_(
            CategoryVersion.version == version,
            CategoryVersion.is_active == True
        )
    ).first()

    if not category_version:
        raise HTTPException(
            status_code=404,
            detail=f"Category version '{version}' not found or not active"
        )

    # Get unique groups
    groups = db.query(CategoryV6.group).filter(
        and_(
            CategoryV6.version_id == category_version.id,
            CategoryV6.exchange_type == exchange_enum,
            CategoryV6.is_active == True
        )
    ).distinct().all()

    return {"groups": [group[0] for group in groups]}

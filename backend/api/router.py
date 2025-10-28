"""Main API router - combines all endpoint routers"""
from fastapi import APIRouter

from .endpoints import health, market_listings, notifications

router = APIRouter()

# Include all endpoint routers
router.include_router(health.router)
router.include_router(market_listings.router)
router.include_router(notifications.router)

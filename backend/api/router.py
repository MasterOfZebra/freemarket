"""Main API router - combines all endpoint routers"""
from fastapi import APIRouter

from .endpoints import health, market_listings, notifications, exchange_chains, users

router = APIRouter()

# Include all endpoint routers
router.include_router(health.router)
router.include_router(market_listings.router)
router.include_router(notifications.router)
router.include_router(exchange_chains.router)
router.include_router(users.router)

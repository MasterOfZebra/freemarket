"""Main API router - combines all endpoint routers"""
from fastapi import APIRouter

from .endpoints import health, market_listings, notifications, exchange_chains, users, matching, listings_exchange
from .endpoints.market_listings import items_router

router = APIRouter()

# Include all endpoint routers
router.include_router(health.router)
router.include_router(users.router)
router.include_router(market_listings.router)
router.include_router(items_router)  # Items endpoints for frontend compatibility
router.include_router(listings_exchange.router)
router.include_router(notifications.router)
router.include_router(exchange_chains.router)
router.include_router(matching.router)

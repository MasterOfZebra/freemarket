"""Main API router - combines all endpoint routers"""
from fastapi import APIRouter

from .endpoints import health, notifications, exchange_chains, users, matching, listings_exchange

router = APIRouter()

# Include all endpoint routers
router.include_router(health.router)
router.include_router(users.router)

# Listings exchange endpoints (permanent/temporary with categories) - PRIMARY endpoint for listings
router.include_router(listings_exchange.router, prefix="/api")
router.include_router(notifications.router)
router.include_router(exchange_chains.router)
router.include_router(matching.router)

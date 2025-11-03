"""Main API router - combines all endpoint routers"""
from fastapi import APIRouter

from .endpoints import health, notifications, exchange_chains, users, matching, listings_exchange, categories, auth, user_profile

router = APIRouter()

# Include all endpoint routers
router.include_router(health.router)
router.include_router(users.router)

# Authentication API
router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# User profile and cabinet API
router.include_router(user_profile.router, prefix="/user", tags=["user"])

# Categories API for dynamic forms
router.include_router(categories.router)

# Listings exchange endpoints (permanent/temporary with categories) - PRIMARY endpoint for listings
router.include_router(listings_exchange.router, prefix="/api")
router.include_router(notifications.router)
router.include_router(exchange_chains.router)
router.include_router(matching.router)

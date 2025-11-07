"""Main API router - combines all endpoint routers"""
from fastapi import APIRouter

from .endpoints import health, notifications, exchange_chains, users, matching, listings_exchange, categories, auth, user_profile, chat, reviews, exchange_history, sse, moderation

router = APIRouter()

# Include all endpoint routers
router.include_router(health.router)
router.include_router(users.router)

# Authentication API
router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# User profile and cabinet API
router.include_router(user_profile.router, prefix="/user", tags=["user"])

# Categories API for dynamic forms
router.include_router(categories.router, prefix="/v1", tags=["categories"])

# Listings exchange endpoints (permanent/temporary with categories) - PRIMARY endpoint for listings
router.include_router(listings_exchange.router, prefix="/api")
router.include_router(notifications.router)
router.include_router(exchange_chains.router)
router.include_router(matching.router)

# Real-time functionality
router.include_router(chat.router, prefix="/ws", tags=["chat"])
router.include_router(sse.router, prefix="/api", tags=["sse"])
router.include_router(notifications.router, prefix="/api", tags=["notifications"])
router.include_router(reviews.router, prefix="/api", tags=["reviews"])
router.include_router(exchange_history.router, prefix="/api", tags=["exchange_history"])
router.include_router(moderation.router, prefix="/api", tags=["moderation"])

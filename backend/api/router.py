"""Main API router - combines all endpoint routers"""
from fastapi import APIRouter

from .endpoints import health, market_listings, notifications, exchange_chains, users, matching, listings_exchange

router = APIRouter()

# Include all endpoint routers
router.include_router(health.router)
router.include_router(users.router)
router.include_router(market_listings.router)

# Items endpoints for frontend compatibility
try:
    from .endpoints.market_listings import items_router
    router.include_router(items_router, prefix="/api")
    print("✅ items_router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load items_router: {e}")

router.include_router(listings_exchange.router)
router.include_router(notifications.router)
router.include_router(exchange_chains.router)
router.include_router(matching.router)

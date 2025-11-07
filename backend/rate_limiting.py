"""
Rate limiting middleware for API endpoints.

Uses Redis for distributed rate limiting.
"""
import time
import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .config import REDIS_URL

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RateLimiter:
    """Redis-based rate limiter"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        if not self.redis_client and REDIS_AVAILABLE and REDIS_URL:
            try:
                self.redis_client = redis.from_url(REDIS_URL)
            except Exception as e:
                logger.warning(f"Failed to connect Redis for rate limiting: {e}")

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Unique identifier for the rate limit (e.g., "user:123:messages")
            limit: Maximum requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            True if allowed, False if rate limited
        """
        if not self.redis_client:
            return True  # Allow if Redis not available

        try:
            current_time = int(time.time())
            window_start = current_time - window_seconds

            # Use Redis sorted set to track requests
            zset_key = f"ratelimit:{key}"

            # Remove old entries
            self.redis_client.zremrangebyscore(zset_key, 0, window_start)

            # Count current requests in window
            request_count = self.redis_client.zcard(zset_key)

            if request_count >= limit:
                return False

            # Add current request
            self.redis_client.zadd(zset_key, {str(current_time): current_time})

            # Set expiration on the key
            self.redis_client.expire(zset_key, window_seconds * 2)

            return True

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return True  # Allow on error

    def get_remaining_time(self, key: str, window_seconds: int) -> int:
        """
        Get seconds until rate limit resets.

        Args:
            key: Rate limit key
            window_seconds: Window size

        Returns:
            Seconds until reset
        """
        if not self.redis_client:
            return 0

        try:
            zset_key = f"ratelimit:{key}"
            # Get oldest timestamp in current window
            oldest = self.redis_client.zrange(zset_key, 0, 0, withscores=True)

            if oldest:
                oldest_time = int(oldest[0][1])
                current_time = int(time.time())
                reset_time = oldest_time + window_seconds
                return max(0, reset_time - current_time)

        except Exception as e:
            logger.error(f"Error getting reset time: {e}")

        return 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""

    def __init__(self, app, limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.limiter = limiter or RateLimiter()

        # Define rate limits for different endpoints
        self.rate_limits = {
            # Messages: 30 per minute per user
            "/api/chat/exchanges/": (30, 60),

            # Reviews: 5 per hour per user
            "/api/reviews/exchanges/": (5, 3600),

            # Listings creation: 10 per hour per user
            "/api/listings": (10, 3600),

            # General API: 100 per minute per IP
            "default": (100, 60),
        }

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if request.url.path.startswith(("/health", "/docs", "/redoc", "/openapi.json")):
            return await call_next(request)

        # Get client identifier (user ID if authenticated, otherwise IP)
        client_id = await self._get_client_id(request)

        # Find matching rate limit rule
        limit, window = self._get_rate_limit(request.url.path)

        # Check rate limit
        rate_key = f"{client_id}:{request.url.path.split('/')[1]}"  # e.g., "user123:chat"

        if not self.limiter.is_allowed(rate_key, limit, window):
            reset_time = self.limiter.get_remaining_time(rate_key, window)

            logger.warning(f"Rate limit exceeded for {client_id} on {request.url.path}")

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Try again in {reset_time} seconds.",
                    "retry_after": reset_time
                },
                headers={"Retry-After": str(reset_time)}
            )

        # Proceed with request
        response = await call_next(request)
        return response

    async def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from JWT token (simplified)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # In a real implementation, you'd decode the JWT to get user ID
            # For now, use a hash of the token as identifier
            import hashlib
            token_hash = hashlib.md5(auth_header[7:].encode()).hexdigest()[:8]
            return f"user_{token_hash}"

        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip_{client_ip}"

    def _get_rate_limit(self, path: str) -> tuple:
        """Get rate limit for path"""
        for prefix, (limit, window) in self.rate_limits.items():
            if prefix != "default" and path.startswith(prefix):
                return limit, window

        return self.rate_limits["default"]


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

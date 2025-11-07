"""
Error tracking integration with Sentry.

Provides middleware for automatic error reporting and context capture.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastAPIIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None
    FastAPIIntegration = None
    RedisIntegration = None
    SqlalchemyIntegration = None


def init_sentry(dsn: Optional[str] = None, environment: str = "development"):
    """
    Initialize Sentry error tracking.

    Args:
        dsn: Sentry DSN (Data Source Name)
        environment: Environment name (development, staging, production)
    """
    if not SENTRY_AVAILABLE:
        logger.info("Sentry not available - install sentry-sdk to enable error tracking")
        return

    if not dsn:
        # Try to get from environment
        import os
        dsn = os.getenv("SENTRY_DSN")

    if not dsn:
        logger.info("SENTRY_DSN not configured - error tracking disabled")
        return

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            integrations=[
                FastAPIIntegration(),
                RedisIntegration(),
                SqlalchemyIntegration(),
            ],
            # Capture performance traces
            traces_sample_rate=0.1,  # 10% of transactions
            # Capture request bodies for debugging
            request_bodies="small",
            # Don't send personal data
            send_default_pii=False,
            # Custom before_send to filter sensitive data
            before_send=before_send_filter,
        )

        logger.info(f"Sentry initialized for environment: {environment}")

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_filter(event, hint):
    """
    Filter sensitive data before sending to Sentry.

    Args:
        event: Sentry event
        hint: Event hint

    Returns:
        Filtered event or None to drop
    """
    try:
        # Remove sensitive fields from request data
        if "request" in event:
            request = event["request"]

            # Remove auth headers
            if "headers" in request:
                headers = request["headers"]
                sensitive_headers = ["authorization", "x-api-key", "cookie"]
                for header in sensitive_headers:
                    if header in headers:
                        headers[header] = "[FILTERED]"

            # Filter request body for sensitive endpoints
            if "data" in request:
                url = request.get("url", "")
                if any(endpoint in url for endpoint in ["/auth/login", "/auth/register"]):
                    request["data"] = "[FILTERED - AUTH DATA]"

        # Add custom tags
        if "tags" not in event:
            event["tags"] = {}

        event["tags"]["component"] = "freemarket-backend"

        return event

    except Exception as e:
        logger.warning(f"Error in Sentry before_send filter: {e}")
        return event


def capture_exception(exc: Exception, **kwargs):
    """
    Capture exception with additional context.

    Args:
        exc: Exception to capture
        **kwargs: Additional context
    """
    if SENTRY_AVAILABLE and sentry_sdk:
        with sentry_sdk.configure_scope() as scope:
            for key, value in kwargs.items():
                scope.set_context(key, {"value": value})
            sentry_sdk.capture_exception(exc)


def capture_message(message: str, level: str = "info", **kwargs):
    """
    Capture custom message.

    Args:
        message: Message to capture
        level: Log level
        **kwargs: Additional context
    """
    if SENTRY_AVAILABLE and sentry_sdk:
        with sentry_sdk.configure_scope() as scope:
            for key, value in kwargs.items():
                scope.set_context(key, {"value": value})
            sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id: int, email: Optional[str] = None, **kwargs):
    """
    Set user context for error tracking.

    Args:
        user_id: User ID
        email: User email (optional)
        **kwargs: Additional user data
    """
    if SENTRY_AVAILABLE and sentry_sdk:
        sentry_sdk.set_user({
            "id": str(user_id),
            "email": email,
            **kwargs
        })


def set_tag(key: str, value: str):
    """
    Set custom tag for error tracking.

    Args:
        key: Tag key
        value: Tag value
    """
    if SENTRY_AVAILABLE and sentry_sdk:
        sentry_sdk.set_tag(key, value)


# FastAPI middleware for additional error context
class ErrorTrackingMiddleware:
    """
    Middleware to add error tracking context to requests.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Add request context
        if SENTRY_AVAILABLE and sentry_sdk:
            sentry_sdk.set_context("request", {
                "method": scope.get("method"),
                "path": scope.get("path"),
                "query_string": scope.get("query_string", b"").decode(),
            })

        await self.app(scope, receive, send)

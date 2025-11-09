"""
FreeMarket Backend - Main FastAPI Application
"""
print("[DEBUG] FreeMarket main.py starting...")

import sys
import os
import json
from typing import Any

# Add parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from backend.config import API_TITLE, API_VERSION, API_DESCRIPTION, CORS_ORIGINS, ENV
from backend.database import engine
from backend.models import Base as ModelBase
from backend.api import router as api_router
from backend.chat_worker import chat_lifespan
from backend.report_processor import report_processor_lifespan
from backend.exchange_sync import exchange_sync_lifespan
from backend.rate_limiting import RateLimitMiddleware
from backend.error_tracking import init_sentry

# Initialize error tracking
init_sentry(environment=ENV)


class UTF8JSONResponse(JSONResponse):
    """Custom JSON Response that preserves UTF-8 characters"""
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


# Combined lifespan for all background services
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup
    async with chat_lifespan():
        async with report_processor_lifespan():
            async with exchange_sync_lifespan():
                yield

    # Shutdown - handled by individual lifespans


# Initialize FastAPI app
print(f"[DEBUG] Creating FastAPI app with title: {API_TITLE}, version: {API_VERSION}")
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    default_response_class=UTF8JSONResponse,
    lifespan=lifespan,
)
print("[DEBUG] FastAPI app created successfully")

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API Version header middleware
@app.middleware("http")
async def add_api_version_header(request, call_next):
    """Add X-API-Version header to all responses"""
    response = await call_next(request)
    response.headers["X-API-Version"] = API_VERSION
    return response

# Include all API routers
print("[DEBUG] Including API router...")
app.include_router(api_router)
print("[DEBUG] API router included successfully")


# Create database tables on startup (not on import)
@app.on_event("startup")
def startup_event():
    """Create database tables on app startup"""
    try:
        ModelBase.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"⚠️  Warning: Could not create DB tables on startup: {e}")
        print("   This is OK for development. Tables should exist in production.")

    # Clear OpenAPI cache to ensure requestBody schemas are generated correctly
    # This is needed for gunicorn workers that fork after app creation
    print("[DEBUG] Clearing OpenAPI cache for proper schema generation")
    app.openapi_schema = None


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=(ENV == "development"),
    )

"""
FreeMarket Backend - Main FastAPI Application
"""
import sys
import os
import json
from typing import Any

# Add parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import uvicorn

from backend.config import API_TITLE, API_VERSION, API_DESCRIPTION, CORS_ORIGINS, ENV
from backend.database import engine
from backend.models import Base as ModelBase
from backend.api import router as api_router


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


# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    default_response_class=UTF8JSONResponse,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routers
app.include_router(api_router)

# Create database tables
ModelBase.metadata.create_all(bind=engine)


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=(ENV == "development"),
    )

"""Health check endpoints"""
from fastapi import APIRouter

router = APIRouter(prefix="", tags=["health"])


@router.get("/health")
def health_check():
    """Health check endpoint to verify API is running"""
    return {"status": "ok", "message": "FreeMarket API is running"}


@router.get("/")
def read_root():
    """Root API endpoint"""
    return {"message": "FreeMarket API", "version": "1.0.0"}

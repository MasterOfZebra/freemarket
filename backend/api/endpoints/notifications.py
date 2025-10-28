"""Notifications endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.schemas import NotificationCreate

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    """Get pending notifications for a user"""
    # TODO: Implement notification retrieval
    return {"notifications": [], "count": 0}

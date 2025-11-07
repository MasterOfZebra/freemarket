"""
Database configuration and session management
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis.asyncio as redis

from backend.config import DATABASE_URL, REDIS_URL

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()

# Redis for caching and queues
redis_client = redis.from_url(REDIS_URL)


# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    from backend import models  # Import all models to register them with Base
    print("Creating tables...")
    models.Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

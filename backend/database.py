from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import redis.asyncio as redis

# Database URL - set via environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./exchange.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Redis for caching and queues
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL)

if __name__ == "__main__":
    from backend import models  # Import all models to register them with Base
    print("Creating tables...")
    models.Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

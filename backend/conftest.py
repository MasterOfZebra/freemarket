import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend import models  # ensure models are registered on Base

@pytest.fixture(scope="function")
def session():
    # Use an isolated SQLite DB for matching tests
    engine = create_engine("sqlite:///./test_matching.db", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # Create schema
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop schema to keep tests isolated
        Base.metadata.drop_all(bind=engine)

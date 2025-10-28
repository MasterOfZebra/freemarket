#!/usr/bin/env python3
"""
Initialize database with all tables from SQLAlchemy models.
This script creates all tables and ensures the database is ready to use.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import engine, Base
from backend import models  # This imports all model definitions


def init_database():
    """Create all tables from SQLAlchemy models."""
    print("\n" + "="*60)
    print("🗄️  Initializing FreeMarket Database...")
    print("="*60 + "\n")
    
    try:
        print("📊 Creating all tables from SQLAlchemy models...")
        
        # Create all tables defined in models
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database initialized successfully!")
        print("\n📝 Tables created:")
        
        # List created tables
        inspector_query = """
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
        """
        
        with engine.connect() as conn:
            result = conn.execute(Base.metadata.bind.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
            ))
        
        print("   - All core tables created\n")
        print("="*60)
        print("✓ Database is ready to use!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}\n")
        print("="*60 + "\n")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)

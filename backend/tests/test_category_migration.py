#!/usr/bin/env python3
"""
Tests for category migration functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy.orm import sessionmaker

from backend.database import engine
from backend.models import CategoryMapping, ListingItem, ExchangeType, CategoryVersion, CategoryV6
from backend.scripts.migrate_legacy_categories import migrate_legacy_categories, rollback_legacy_categories


class TestCategoryMigration:
    """Test category migration functionality"""

    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.rollback()
        session.close()

    def test_category_mappings_exist(self, db_session):
        """Test that category mappings are properly created"""
        mappings = db_session.query(CategoryMapping).all()
        assert len(mappings) > 0, "No category mappings found"

        # Check some expected mappings
        electronics_mapping = db_session.query(CategoryMapping).filter(
            CategoryMapping.legacy_category == "electronics",
            CategoryMapping.exchange_type == ExchangeType.PERMANENT
        ).first()

        assert electronics_mapping is not None, "Electronics mapping not found"
        assert electronics_mapping.confidence >= 0.8, "Low confidence for electronics mapping"

    def test_migration_script_runs(self, db_session):
        """Test that migration script can run without errors"""
        try:
            # This should not raise an exception
            migrate_legacy_categories()
        except Exception as e:
            pytest.fail(f"Migration script failed: {e}")

    def test_rollback_script_runs(self, db_session):
        """Test that rollback script can run without errors"""
        try:
            # This should not raise an exception
            rollback_legacy_categories()
        except Exception as e:
            pytest.fail(f"Rollback script failed: {e}")

    def test_category_api_endpoints(self, client):
        """Test category API endpoints"""
        # Test getting categories
        response = client.get("/v1/categories")
        assert response.status_code == 200

        data = response.json()
        assert "version" in data
        assert "categories" in data
        assert "permanent" in data["categories"]
        assert "temporary" in data["categories"]

        # Test getting categories by type
        response = client.get("/v1/categories/permanent")
        assert response.status_code == 200

        permanent_cats = response.json()
        assert len(permanent_cats) > 0
        assert all(cat["slug"] for cat in permanent_cats)

    def test_listing_item_validation(self, db_session):
        """Test that listing items have valid categories"""
        items = db_session.query(ListingItem).limit(10).all()

        for item in items:
            # Category should not be empty
            assert item.category, f"Item {item.id} has empty category"

            # Category should be reasonable length
            assert len(item.category) <= 50, f"Category too long: {item.category}"

            # Exchange type should be valid
            assert item.exchange_type in [ExchangeType.PERMANENT, ExchangeType.TEMPORARY]


if __name__ == "__main__":
    # Run basic smoke tests
    print("🧪 Running category migration smoke tests...")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Test mappings exist
        mappings_count = db.query(CategoryMapping).count()
        print(f"✅ Found {mappings_count} category mappings")

        # Test categories exist
        v6_count = db.query(CategoryV6).count()
        print(f"✅ Found {v6_count} v6 categories")

        # Test versions exist
        versions = db.query(CategoryVersion).all()
        print(f"✅ Found {len(versions)} category versions: {[v.version for v in versions]}")

        print("✅ All smoke tests passed!")

    except Exception as e:
        print(f"❌ Smoke test failed: {e}")
        sys.exit(1)
    finally:
        db.close()

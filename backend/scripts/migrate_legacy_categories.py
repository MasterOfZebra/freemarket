#!/usr/bin/env python3
"""
Migrate legacy categories to v6 system using category mappings
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from backend.database import engine
from backend.models import CategoryMapping, ListingItem, ExchangeType


def migrate_legacy_categories():
    """Migrate existing listing items to new v6 categories"""

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Get all listings with legacy categories
        legacy_items = db.query(ListingItem).filter(
            ListingItem.category.in_([
                'electronics', 'money', 'furniture', 'transport', 'services'
            ])
        ).all()

        migrated_count = 0
        skipped_count = 0

        for item in legacy_items:
            # Find best mapping for this category and exchange type
            mapping = db.query(CategoryMapping).filter(
                CategoryMapping.legacy_category == item.category,
                CategoryMapping.exchange_type == item.exchange_type
            ).order_by(CategoryMapping.confidence.desc()).first()

            if mapping:
                print(f"Migrating: {item.category} -> {mapping.new_category_slug} "
                      f"(confidence: {mapping.confidence})")
                item.category = mapping.new_category_slug
                migrated_count += 1
            else:
                print(f"⚠️  No mapping found for: {item.category} ({item.exchange_type})")
                skipped_count += 1

        db.commit()
        print(f"\n✅ Migration completed!")
        print(f"Migrated: {migrated_count} items")
        print(f"Skipped: {skipped_count} items")

    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()


def rollback_legacy_categories():
    """Rollback category migration (for testing)"""

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Get all v6 categories to rollback to legacy
        v6_categories = [
            'photo_equipment', 'lighting_equipment', 'money_crypto', 'furniture_appliances',
            'decor_textiles', 'personal_transport', 'electric_vehicles', 'services_work',
            'completed_projects', 'bicycles', 'electric_transport', 'tutoring',
            'task_execution', 'video_audio', 'trusted_equivalent'
        ]

        rollback_mappings = {
            # v6 -> legacy mappings for rollback
            'photo_equipment': 'electronics',
            'lighting_equipment': 'electronics',
            'money_crypto': 'money',
            'furniture_appliances': 'furniture',
            'decor_textiles': 'furniture',
            'personal_transport': 'transport',
            'electric_vehicles': 'transport',
            'services_work': 'services',
            'completed_projects': 'services',
            'bicycles': 'transport',
            'electric_transport': 'transport',
            'tutoring': 'services',
            'task_execution': 'services',
            'video_audio': 'electronics',
            'trusted_equivalent': 'money'
        }

        items_to_rollback = db.query(ListingItem).filter(
            ListingItem.category.in_(v6_categories)
        ).all()

        rolled_back_count = 0
        for item in items_to_rollback:
            if item.category in rollback_mappings:
                old_category = item.category
                item.category = rollback_mappings[item.category]
                print(f"Rolled back: {old_category} -> {item.category}")
                rolled_back_count += 1

        db.commit()
        print(f"\n✅ Rollback completed! Rolled back {rolled_back_count} items")

    except Exception as e:
        db.rollback()
        print(f"❌ Rollback failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        print("🔄 Starting rollback...")
        rollback_legacy_categories()
    else:
        print("🔄 Starting migration...")
        migrate_legacy_categories()

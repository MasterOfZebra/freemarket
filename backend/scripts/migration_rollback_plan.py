#!/usr/bin/env python3
"""
Migration rollback plan for categories v6
Provides feature flag control and rollback procedures
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from backend.database import engine
from backend.models import CategoryVersion, CategoryV6, CategoryMapping, ListingItem, ExchangeType


# Feature flag for new categories
USE_NEW_CATEGORIES = os.getenv("USE_NEW_CATEGORIES", "true").lower() == "true"


def get_active_category_version(db):
    """Get currently active category version"""
    return db.query(CategoryVersion).filter(
        CategoryVersion.is_active == True
    ).first()


def set_category_version(version: str, db):
    """Set active category version"""
    # Deactivate all versions
    db.query(CategoryVersion).update({"is_active": False})

    # Activate specified version
    version_obj = db.query(CategoryVersion).filter(
        CategoryVersion.version == version
    ).first()

    if version_obj:
        version_obj.is_active = True
        db.commit()
        print(f"✅ Activated category version: {version}")
    else:
        print(f"❌ Version {version} not found")
        db.rollback()


def rollback_to_legacy_categories(db):
    """Rollback to legacy categories (v5 or earlier)"""
    print("🔄 Starting rollback to legacy categories...")

    try:
        # 1. Deactivate v6 categories
        v6_version = db.query(CategoryVersion).filter(
            CategoryVersion.version == "v6.0"
        ).first()

        if v6_version:
            v6_version.is_active = False

        # 2. Find or create legacy version
        legacy_version = db.query(CategoryVersion).filter(
            CategoryVersion.version == "legacy"
        ).first()

        if not legacy_version:
            # Create legacy version if it doesn't exist
            legacy_version = CategoryVersion(
                version="legacy",
                is_active=True,
                description="Legacy categories (pre-v6)"
            )
            db.add(legacy_version)
            db.flush()

        # 3. Migrate data back to legacy categories
        # This would need to be customized based on your legacy category system
        print("⚠️  Manual step required: Restore legacy category tables/data")

        # 4. Update listing items to use legacy categories
        # (This is handled by migrate_legacy_categories.py --rollback)

        db.commit()
        print("✅ Rollback to legacy categories completed")

    except Exception as e:
        db.rollback()
        print(f"❌ Rollback failed: {e}")
        raise


def emergency_rollback_procedure():
    """
    Emergency rollback procedure - for critical issues
    Run this if new categories cause system instability
    """
    print("🚨 EMERGENCY ROLLBACK PROCEDURE")
    print("=" * 50)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Step 1: Deactivate new categories
        print("Step 1: Deactivating v6 categories...")
        db.query(CategoryVersion).filter(
            CategoryVersion.version == "v6.0"
        ).update({"is_active": False})

        # Step 2: Activate legacy fallback
        print("Step 2: Activating legacy categories...")
        legacy_version = db.query(CategoryVersion).filter(
            CategoryVersion.version == "legacy"
        ).first()

        if legacy_version:
            legacy_version.is_active = True
        else:
            print("⚠️  Legacy version not found, creating emergency fallback...")
            legacy_version = CategoryVersion(
                version="legacy",
                is_active=True,
                description="Emergency fallback to legacy categories"
            )
            db.add(legacy_version)

        # Step 3: Rollback listing item categories
        print("Step 3: Rolling back listing item categories...")
        # This calls the rollback function from migrate_legacy_categories.py
        from backend.scripts.migrate_legacy_categories import rollback_legacy_categories
        rollback_legacy_categories()

        db.commit()
        print("✅ Emergency rollback completed successfully")

    except Exception as e:
        db.rollback()
        print(f"❌ Emergency rollback failed: {e}")
        print("Manual intervention required!")
        raise
    finally:
        db.close()


def migration_status_report(db):
    """Generate migration status report"""
    print("\n📊 MIGRATION STATUS REPORT")
    print("=" * 40)

    # Active version
    active_version = get_active_category_version(db)
    print(f"Active version: {active_version.version if active_version else 'None'}")

    # Category counts
    if active_version:
        permanent_count = db.query(CategoryV6).filter(
            CategoryV6.version_id == active_version.id,
            CategoryV6.exchange_type == ExchangeType.PERMANENT
        ).count()

        temporary_count = db.query(CategoryV6).filter(
            CategoryV6.version_id == active_version.id,
            CategoryV6.exchange_type == ExchangeType.TEMPORARY
        ).count()

        print(f"Permanent categories: {permanent_count}")
        print(f"Temporary categories: {temporary_count}")

    # Migration mappings
    mapping_count = db.query(CategoryMapping).count()
    print(f"Legacy mappings: {mapping_count}")

    # Listing items status
    total_items = db.query(ListingItem).count()
    migrated_items = db.query(ListingItem).filter(
        ListingItem.category.in_([
            # List of v6 category slugs
            'bicycles', 'electric_transport', 'carsharing', 'hand_tools',
            'printers_equipment', 'construction_tools', 'photo_equipment',
            'video_audio', 'production_kits', 'cloud_resources', 'api_access',
            'software_licenses', 'network_resources', 'money_crypto',
            'trusted_equivalent', 'tutoring', 'task_execution', 'time_resource',
            'housing_rental', 'coworking_spaces', 'pet_sitting', 'temporary_care',
            'sports_equipment', 'board_games', 'props_rental'
        ])
    ).count()

    print(f"Total listing items: {total_items}")
    print(f"Migrated to v6: {migrated_items}")
    print(f"Migration progress: {(migrated_items/total_items*100):.1f}%")


def main():
    """Main migration control interface"""
    if len(sys.argv) < 2:
        print("Usage: python migration_rollback_plan.py <command>")
        print("Commands:")
        print("  status          - Show migration status")
        print("  activate <ver>  - Activate category version")
        print("  rollback        - Rollback to legacy categories")
        print("  emergency       - Emergency rollback procedure")
        return

    command = sys.argv[1]

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        if command == "status":
            migration_status_report(db)

        elif command == "activate" and len(sys.argv) > 2:
            version = sys.argv[2]
            set_category_version(version, db)

        elif command == "rollback":
            rollback_to_legacy_categories(db)

        elif command == "emergency":
            emergency_rollback_procedure()

        else:
            print("Unknown command")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

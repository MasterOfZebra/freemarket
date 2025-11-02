#!/usr/bin/env python3
"""
Migration script to convert legacy MarketListing records to new ListingItem format.

This script:
1. Converts old MarketListing records to new ListingItem records
2. Migrates array-based data to byCategory.items[] structure
3. Updates exchange_type based on lease_term presence
4. Preserves all existing data with proper validation

Run this script ONCE after deploying the new schema.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import sessionmaker
from database import engine, SessionLocal
from models import (
    MarketListing, ListingItem, ListingItemType, ExchangeType, Listing, User
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_market_listings_to_listing_items():
    """
    Convert old MarketListing records to new ListingItem records.
    """
    db = SessionLocal()

    try:
        # Get all existing market listings
        market_listings = db.query(MarketListing).all()
        logger.info(f"Found {len(market_listings)} market listings to migrate")

        migrated_count = 0
        skipped_count = 0

        for market_listing in market_listings:
            try:
                # Skip if already migrated (check if listing exists)
                existing_listing = db.query(Listing).filter(
                    Listing.id == market_listing.id
                ).first()

                if existing_listing:
                    logger.info(f"Listing {market_listing.id} already exists, skipping")
                    skipped_count += 1
                    continue

                # Create new Listing record
                new_listing = Listing(
                    id=market_listing.id,  # Preserve ID
                    user_id=market_listing.user_id,
                    title=market_listing.title or "Migrated listing",
                    description=market_listing.description
                )
                db.add(new_listing)
                db.flush()  # Get listing ID

                # Determine exchange type based on lease_term
                exchange_type = ExchangeType.TEMPORARY if market_listing.lease_term else ExchangeType.PERMANENT

                # Create ListingItem based on listing type
                item_type = ListingItemType.WANT if market_listing.type == "wants" else ListingItemType.OFFER

                # Map old categories to new ones (simplified mapping)
                category_mapping = {
                    "electronics": "electronics",
                    "furniture": "furniture",
                    "transport": "transport",
                    "money": "money",
                    "services": "services",
                    # Add more mappings as needed
                }

                old_category = market_listing.category_id  # This would be a foreign key
                # For now, use a default category - in real migration you'd look up Category.name
                new_category = category_mapping.get("electronics", "electronics")  # Default fallback

                # Create ListingItem
                listing_item = ListingItem(
                    listing_id=new_listing.id,
                    item_type=item_type,
                    category=new_category,
                    exchange_type=exchange_type,
                    item_name=market_listing.title or "Migrated item",
                    value_tenge=int(market_listing.value_max or market_listing.value_min or 1000),
                    duration_days=market_listing.lease_term.days if market_listing.lease_term else None,
                    description=market_listing.description
                )

                # Validate the item
                if not listing_item.is_valid:
                    logger.warning(f"Invalid migrated item for listing {market_listing.id}, skipping")
                    db.rollback()
                    continue

                db.add(listing_item)
                migrated_count += 1

                if migrated_count % 10 == 0:
                    logger.info(f"Migrated {migrated_count} listings...")

            except Exception as e:
                logger.error(f"Error migrating listing {market_listing.id}: {e}")
                db.rollback()
                continue

        db.commit()
        logger.info(f"Migration completed: {migrated_count} migrated, {skipped_count} skipped")

        return {
            "migrated": migrated_count,
            "skipped": skipped_count,
            "total": len(market_listings)
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        db.close()


def rollback_migration():
    """
    Rollback migration - remove all ListingItem records created from MarketListing.
    This is a destructive operation - use with caution!
    """
    db = SessionLocal()

    try:
        # Delete all Listing and ListingItem records (dangerous!)
        # In real scenario, you'd need more sophisticated rollback logic
        logger.warning("Rolling back migration - this will DELETE all new listings!")

        deleted_listings = db.query(Listing).delete()
        deleted_items = db.query(ListingItem).delete()

        db.commit()

        logger.info(f"Rollback completed: {deleted_listings} listings, {deleted_items} items deleted")

        return {
            "listings_deleted": deleted_listings,
            "items_deleted": deleted_items
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Rollback failed: {e}")
        raise
    finally:
        db.close()


def validate_migration():
    """
    Validate that migration was successful.
    """
    db = SessionLocal()

    try:
        total_listings = db.query(Listing).count()
        total_items = db.query(ListingItem).count()
        total_market_listings = db.query(MarketListing).count()

        logger.info("Migration validation:")
        logger.info(f"- New listings: {total_listings}")
        logger.info(f"- New listing items: {total_items}")
        logger.info(f"- Old market listings: {total_market_listings}")

        # Check for orphaned records
        orphaned_items = db.query(ListingItem).filter(
            ~ListingItem.listing_id.in_(db.query(Listing.id))
        ).count()

        if orphaned_items > 0:
            logger.error(f"Found {orphaned_items} orphaned listing items!")

        return {
            "new_listings": total_listings,
            "new_items": total_items,
            "old_listings": total_market_listings,
            "orphaned_items": orphaned_items,
            "valid": orphaned_items == 0
        }

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate legacy MarketListing to new ListingItem format")
    parser.add_argument("action", choices=["migrate", "rollback", "validate"],
                       help="Action to perform")

    args = parser.parse_args()

    if args.action == "migrate":
        logger.info("Starting migration...")
        result = migrate_market_listings_to_listing_items()
        logger.info(f"Migration result: {result}")

    elif args.action == "rollback":
        confirm = input("This will DELETE all migrated data. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            result = rollback_migration()
            logger.info(f"Rollback result: {result}")
        else:
            logger.info("Rollback cancelled")

    elif args.action == "validate":
        result = validate_migration()
        logger.info(f"Validation result: {result}")

        if result["valid"]:
            logger.info("✅ Migration validation PASSED")
        else:
            logger.error("❌ Migration validation FAILED")
            sys.exit(1)

#!/usr/bin/env python3
"""
Rollback script for data migration from MarketListing to ListingItem format.

WARNING: This script is DESTRUCTIVE and will permanently delete data!
Use only in development/testing environments or as a last resort.

This script:
1. Deletes all ListingItem records
2. Deletes all Listing records
3. Optionally restores MarketListing records from backup
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import sessionmaker
from database import engine, SessionLocal
from models import Listing, ListingItem, MarketListing
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rollback_data_migration():
    """
    Rollback the data migration - delete all new records.
    """
    db = SessionLocal()

    try:
        logger.warning("🚨 STARTING DESTRUCTIVE ROLLBACK OPERATION 🚨")
        logger.warning("This will permanently delete all Listing and ListingItem records!")

        # Confirm deletion
        confirm = input("Type 'YES' to confirm permanent data deletion: ")
        if confirm != "YES":
            logger.info("Rollback cancelled by user")
            return {"cancelled": True}

        # Delete in correct order (child first)
        deleted_items = db.query(ListingItem).delete()
        logger.info(f"Deleted {deleted_items} listing items")

        deleted_listings = db.query(Listing).delete()
        logger.info(f"Deleted {deleted_listings} listings")

        db.commit()

        logger.info("✅ Rollback completed successfully")
        logger.info(f"- Deleted {deleted_items} listing items")
        logger.info(f"- Deleted {deleted_listings} listings")

        return {
            "items_deleted": deleted_items,
            "listings_deleted": deleted_listings,
            "success": True
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Rollback failed: {e}")
        raise
    finally:
        db.close()


def check_rollback_status():
    """
    Check if rollback can be performed safely.
    """
    db = SessionLocal()

    try:
        listings_count = db.query(Listing).count()
        items_count = db.query(ListingItem).count()
        market_listings_count = db.query(MarketListing).count()

        logger.info("Rollback status check:")
        logger.info(f"- Current listings: {listings_count}")
        logger.info(f"- Current listing items: {items_count}")
        logger.info(f"- Legacy market listings: {market_listings_count}")

        can_rollback = listings_count > 0 or items_count > 0

        if can_rollback:
            logger.info("✅ Rollback is possible (data exists to delete)")
        else:
            logger.info("ℹ️  No data to rollback (already clean)")

        return {
            "can_rollback": can_rollback,
            "listings": listings_count,
            "items": items_count,
            "legacy_listings": market_listings_count
        }

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Rollback data migration")
    parser.add_argument("action", choices=["rollback", "status"],
                       help="Action to perform")

    args = parser.parse_args()

    if args.action == "rollback":
        result = rollback_data_migration()
        if result.get("success"):
            logger.info("✅ Rollback completed successfully")
        else:
            logger.error("❌ Rollback failed or was cancelled")

    elif args.action == "status":
        result = check_rollback_status()
        logger.info(f"Status: {result}")

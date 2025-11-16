#!/usr/bin/env python3
"""
Safe backfill script for migrating users.role VARCHAR to users.role_id INTEGER

This script migrates existing role data without blocking the users table.
Run this AFTER applying the RBAC migration.

Usage:
    python scripts/backfill_user_roles.py
"""

import os
import sys
import time
from typing import Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError


def get_database_url() -> str:
    """Get database URL from environment"""
    return os.getenv('DATABASE_URL', 'postgresql://assistadmin_pg:assistMurzAdmin@postgres:5432/assistance_kz')


def create_db_engine():
    """Create SQLAlchemy engine"""
    db_url = get_database_url()
    return create_engine(db_url, echo=False)


def backfill_user_roles(batch_size: int = 1000, dry_run: bool = False) -> None:
    """
    Safely migrate users.role to users.role_id

    Args:
        batch_size: Number of users to process per batch
        dry_run: If True, only show what would be changed
    """
    engine = create_db_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with SessionLocal() as session:
        try:
            print("🔍 Analyzing existing user roles...")

            # Check if old 'role' column exists (for backward compatibility)
            from sqlalchemy import inspect as sql_inspect
            inspector = sql_inspect(session.bind)
            columns = [col['name'] for col in inspector.get_columns('users')]
            has_old_role_column = 'role' in columns

            # Check role mapping in roles table
            roles_mapping_query = text("""
                SELECT name, id FROM roles ORDER BY id
            """)

            result = session.execute(roles_mapping_query)
            role_mappings = {row[0]: row[1] for row in result.fetchall()}

            print(f"🎯 Available roles in system: {role_mappings}")

            # Find users that need migration
            if has_old_role_column:
                # Check what roles exist in old users.role column
                existing_roles_query = text("""
                    SELECT role, COUNT(*) as count
                    FROM users
                    WHERE role IS NOT NULL AND role != ''
                    GROUP BY role
                    ORDER BY count DESC
                """)

                try:
                    result = session.execute(existing_roles_query)
                    existing_roles = result.fetchall()
                    print(f"📊 Found {len(existing_roles)} different role values in old 'role' column:")
                    for role_name, count in existing_roles:
                        print(f"  - '{role_name}': {count} users")
                except Exception as e:
                    print(f"⚠️  Could not read old 'role' column: {e}")
                    has_old_role_column = False

                # Find users with old VARCHAR role but no role_id
                users_to_migrate_query = text("""
                    SELECT COUNT(*) FROM users
                    WHERE role_id IS NULL
                      AND role IS NOT NULL
                      AND role != ''
                """)

                result = session.execute(users_to_migrate_query)
                users_count = result.scalar()
                print(f"📝 Users with old VARCHAR roles needing migration: {users_count}")
            else:
                users_count = 0
                print("ℹ️  Old 'role' column does not exist - skipping old role migration")

            # Find users with no role_id at all (should get default 'user' role)
            users_no_role_query = text("""
                SELECT COUNT(*) FROM users
                WHERE role_id IS NULL
            """)

            result = session.execute(users_no_role_query)
            users_no_role_count = result.scalar()

            print(f"👤 Users with no role_id (will get default 'user'): {users_no_role_count}")

            total_to_process = users_count + users_no_role_count
            print(f"📊 Total users to process: {total_to_process}")

            if dry_run:
                print("🔍 DRY RUN - showing what would be migrated:")

                # Show sample of users that will be processed
                if has_old_role_column:
                    sample_query = text("""
                        SELECT id, username, role,
                               CASE WHEN role IS NULL OR role = '' THEN true ELSE false END as needs_default
                        FROM users
                        WHERE role_id IS NULL
                        ORDER BY id
                        LIMIT 20
                    """)
                else:
                    sample_query = text("""
                        SELECT id, username, NULL as role, true as needs_default
                        FROM users
                        WHERE role_id IS NULL
                        ORDER BY id
                        LIMIT 20
                    """)

                result = session.execute(sample_query)
                sample_users = result.fetchall()

                for row in sample_users:
                    user_id, username = row[0], row[1]
                    if has_old_role_column and len(row) > 3:
                        role, needs_default = row[2], row[3]
                        if needs_default:
                            print(f"  User {username} (ID: {user_id}): no role -> default user role_id {role_mappings.get('user', 'N/A')}")
                        else:
                            target_role_id = role_mappings.get(role)
                            if target_role_id:
                                print(f"  User {username} (ID: {user_id}): '{role}' -> role_id {target_role_id}")
                            else:
                                print(f"  User {username} (ID: {user_id}): '{role}' -> NO MAPPING, will get default user")
                    else:
                        print(f"  User {username} (ID: {user_id}): no role_id -> default user role_id {role_mappings.get('user', 'N/A')}")

                return

            if total_to_process == 0:
                print("✅ No users need migration!")
                return

            # Get default user role ID
            default_user_role_id = role_mappings.get('user')
            if not default_user_role_id:
                print("❌ Default 'user' role not found in roles table!")
                return

            print(f"🎯 Default user role ID: {default_user_role_id}")

            # Perform migration in batches
            print(f"🚀 Starting migration of {total_to_process} users in batches of {batch_size}...")

            total_processed = 0
            batch_num = 0

            while True:
                batch_num += 1

                # Get next batch of users to migrate
                if has_old_role_column:
                    batch_query = text("""
                        SELECT id, username, role, CASE WHEN role IS NULL OR role = '' THEN true ELSE false END as needs_default
                        FROM users
                        WHERE role_id IS NULL
                        ORDER BY id
                        LIMIT :batch_size
                        FOR UPDATE SKIP LOCKED
                    """)
                else:
                    batch_query = text("""
                        SELECT id, username, NULL as role, true as needs_default
                        FROM users
                        WHERE role_id IS NULL
                        ORDER BY id
                        LIMIT :batch_size
                        FOR UPDATE SKIP LOCKED
                    """)

                result = session.execute(batch_query, {"batch_size": batch_size})
                batch_users = result.fetchall()

                if not batch_users:
                    break

                print(f"📦 Batch {batch_num}: processing {len(batch_users)} users...")

                for row in batch_users:
                    user_id, username = row[0], row[1]
                    if has_old_role_column and len(row) > 3:
                        role, needs_default = row[2], row[3]
                        if needs_default:
                            # User has no role, assign default 'user'
                            target_role_id = default_user_role_id
                            print(f"  🆕 {username}: no role -> default user role_id {target_role_id}")
                        else:
                            # User has old VARCHAR role, try to map it
                            target_role_id = role_mappings.get(role)
                            if target_role_id:
                                print(f"  ✅ {username}: '{role}' -> role_id {target_role_id}")
                            else:
                                # Role not found, assign default
                                target_role_id = default_user_role_id
                                print(f"  ⚠️  {username}: '{role}' not found -> default user role_id {target_role_id}")
                    else:
                        # No old role column - just assign default
                        target_role_id = default_user_role_id
                        print(f"  🆕 {username}: no role_id -> default user role_id {target_role_id}")

                    # Update user with role_id
                    update_query = text("""
                        UPDATE users
                        SET role_id = :role_id
                        WHERE id = :user_id
                    """)

                    session.execute(update_query, {
                        "role_id": target_role_id,
                        "user_id": user_id
                    })

                # Commit batch
                session.commit()
                total_processed += len(batch_users)

                print(f"  📊 Progress: {total_processed}/{total_to_process} users processed")

                # Small delay between batches to reduce load
                time.sleep(0.1)

            print("🎉 Migration completed successfully!")
            print(f"📈 Total users processed: {total_processed}")

            # Final verification
            if has_old_role_column:
                final_check_query = text("""
                    SELECT COUNT(*) FROM users
                    WHERE role_id IS NULL
                      AND role IS NOT NULL
                      AND role != ''
                """)
            else:
                final_check_query = text("""
                    SELECT COUNT(*) FROM users
                    WHERE role_id IS NULL
                """)

            result = session.execute(final_check_query)
            remaining = result.scalar()

            if remaining == 0:
                print("✅ All users successfully migrated!")
            else:
                print(f"⚠️  {remaining} users still need migration (check logs above)")

        except SQLAlchemyError as e:
            print(f"❌ Database error: {e}")
            session.rollback()
            raise
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            session.rollback()
            raise


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Backfill user roles to RBAC system')
    parser.add_argument('--batch-size', type=int, default=1000,
                       help='Number of users to process per batch')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without making changes')

    args = parser.parse_args()

    print("🔄 User Roles Backfill Script")
    print("=" * 40)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    else:
        print("⚠️  PRODUCTION MODE - Changes will be applied to database")

    # Skip confirmation prompt in non-interactive mode (e.g., when called from migrate_to_rbac.py)
    # Check if stdin is a TTY (interactive terminal)
    import sys
    if sys.stdin.isatty():
        confirm = input("Continue? (y/N): ").lower().strip()
        if confirm not in ['y', 'yes']:
            print("Aborted.")
            return
    else:
        # Non-interactive mode - proceed automatically
        print("Non-interactive mode detected - proceeding automatically...")

    backfill_user_roles(batch_size=args.batch_size, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

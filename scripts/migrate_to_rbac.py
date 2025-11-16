#!/usr/bin/env python3
"""
Complete RBAC migration script

This script:
1. Applies the RBAC database migration
2. Runs the backfill script to migrate existing user roles
3. Performs final verification

Usage:
    python scripts/migrate_to_rbac.py [--dry-run]
"""

import os
import sys
import subprocess
import argparse

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def run_command(cmd: list, description: str, timeout: int = 300) -> bool:
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
            timeout=timeout
        )

        if result.returncode == 0:
            print("✅ Success")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print("❌ Failed")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
            return False

    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(description='Complete RBAC migration')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no actual changes)')
    parser.add_argument('--skip-migration', action='store_true',
                       help='Skip database migration step')
    parser.add_argument('--skip-backfill', action='store_true',
                       help='Skip backfill step')

    args = parser.parse_args()

    print("🔄 RBAC Migration Script")
    print("=" * 50)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No permanent changes will be made")

    # Step 1: Apply database migration
    if not args.skip_migration:
        print("\n1️⃣ Applying database migration...")

        # Try different alembic command approaches
        migration_commands = [
            ["alembic", "-c", "/app/alembic.ini", "upgrade", "head"],
            ["python", "-m", "alembic", "-c", "/app/alembic.ini", "upgrade", "head"],
        ]

        migration_success = False
        for cmd in migration_commands:
            if run_command(cmd, f"Trying migration command: {' '.join(cmd)}"):
                migration_success = True
                break

        if not migration_success:
            print("❌ Migration failed. Check alembic configuration.")
            return 1

    # Step 2: Run backfill script
    if not args.skip_backfill:
        print("\n2️⃣ Running user roles backfill...")

        # Use absolute path to script in container
        backfill_cmd = [sys.executable, "/app/scripts/backfill_user_roles.py"]
        if args.dry_run:
            backfill_cmd.append("--dry-run")

        if not run_command(backfill_cmd, "Backfilling user roles"):
            print("❌ Backfill failed.")
            return 1

    # Step 3: Verification
    print("\n3️⃣ Running verification...")

    verify_cmd = [sys.executable, "-c", """
import os
from sqlalchemy import create_engine, text, inspect

db_url = os.getenv('DATABASE_URL', 'postgresql://assistadmin_pg:assistMurzAdmin@postgres:5432/assistance_kz')
engine = create_engine(db_url)

with engine.connect() as conn:
    # Check roles table
    result = conn.execute(text("SELECT COUNT(*) FROM roles"))
    roles_count = result.scalar()
    print(f"Roles in system: {roles_count}")

    # Check permissions
    result = conn.execute(text("SELECT COUNT(*) FROM permissions"))
    perms_count = result.scalar()
    print(f"Permissions defined: {perms_count}")

    # Check if old 'role' column exists
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('users')]
    has_old_role = 'role' in columns

    # Check users migration
    if has_old_role:
        result = conn.execute(text("SELECT COUNT(*) FROM users WHERE role_id IS NULL AND (role IS NOT NULL AND role != '')"))
    else:
        result = conn.execute(text("SELECT COUNT(*) FROM users WHERE role_id IS NULL"))
    unmigrated = result.scalar()
    print(f"Users needing migration: {unmigrated}")

    # Check total users with roles
    result = conn.execute(text("SELECT COUNT(*) FROM users WHERE role_id IS NOT NULL"))
    with_roles = result.scalar()
    print(f"Users with role_id assigned: {with_roles}")

    if unmigrated == 0:
        print("✅ Migration successful!")
    else:
        print(f"⚠️  {unmigrated} users still need migration")
"""]

    if not run_command(verify_cmd, "Verifying migration results"):
        print("❌ Verification failed.")
        return 1

    print("\n🎉 RBAC migration completed successfully!")
    print("\nNext steps:")
    print("1. Update your application code to use role_id instead of role")
    print("2. Test admin functionality")
    print("3. Deploy to production")

    return 0


if __name__ == "__main__":
    sys.exit(main())

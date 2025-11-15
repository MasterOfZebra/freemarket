#!/bin/bash
# Script to manually fix merge migration issue
# This script marks the merge migration as applied in the database

echo "=========================================="
echo "Fixing Merge Migration"
echo "=========================================="

# Check if merge migration file exists in container
echo "[1/3] Checking if merge migration file exists..."
docker compose -f docker-compose.prod.yml exec backend ls -la /app/backend/alembic/versions/p4q5r6s7t8u9_merge_telegram_and_auth_heads.py || {
    echo "File not found in container. Need to rebuild container or copy file."
    echo "Attempting to copy file..."
    docker compose -f docker-compose.prod.yml cp backend/alembic/versions/p4q5r6s7t8u9_merge_telegram_and_auth_heads.py backend:/app/backend/alembic/versions/
}

# Option 1: Try to apply merge migration directly
echo ""
echo "[2/3] Attempting to apply merge migration..."
docker compose -f docker-compose.prod.yml exec backend alembic upgrade p4q5r6s7t8u9 || {
    echo "Migration not found. Trying alternative approach..."
    
    # Option 2: Manually insert merge migration record into alembic_version table
    echo "[3/3] Manually marking merge migration as applied..."
    docker compose -f docker-compose.prod.yml exec -T postgres psql -U freemarket_user -d freemarket_db <<EOF
-- Check current version
SELECT * FROM alembic_version;

-- Insert merge migration record if both parent migrations are applied
INSERT INTO alembic_version (version_num)
SELECT 'p4q5r6s7t8u9'
WHERE EXISTS (
    SELECT 1 FROM alembic_version WHERE version_num = 'n2o3p4q5r6s7'
) AND EXISTS (
    SELECT 1 FROM alembic_version WHERE version_num = 'o3p4q5r6s7t8'
) AND NOT EXISTS (
    SELECT 1 FROM alembic_version WHERE version_num = 'p4q5r6s7t8u9'
);

-- Show updated version
SELECT * FROM alembic_version;
EOF
}

echo ""
echo "=========================================="
echo "Merge migration fix completed!"
echo "=========================================="
echo ""
echo "Note: The main issue is already fixed - telegram_id is now BigInteger."
echo "The merge migration is just for Alembic bookkeeping and doesn't change the database."


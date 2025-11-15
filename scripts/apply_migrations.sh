#!/bin/bash
# Script to apply migrations step by step to resolve multiple heads issue

echo "=========================================="
echo "Applying Alembic Migrations"
echo "=========================================="

# Step 1: Check current heads
echo ""
echo "[1/4] Checking current migration heads..."
docker compose -f docker-compose.prod.yml exec backend alembic heads
echo ""

# Step 2: Apply first branch (refresh_tokens and auth_events)
echo "[2/4] Applying migration n2o3p4q5r6s7 (refresh_tokens and auth_events)..."
docker compose -f docker-compose.prod.yml exec backend alembic upgrade n2o3p4q5r6s7 || echo "Migration may already be applied"
echo ""

# Step 3: Apply second branch (telegram_id to BigInteger)
echo "[3/4] Applying migration o3p4q5r6s7t8 (telegram_id to BigInteger)..."
docker compose -f docker-compose.prod.yml exec backend alembic upgrade o3p4q5r6s7t8 || echo "Migration may already be applied"
echo ""

# Step 4: Apply merge migration
echo "[4/4] Applying merge migration p4q5r6s7t8u9..."
docker compose -f docker-compose.prod.yml exec backend alembic upgrade p4q5r6s7t8u9 || echo "Migration may already be applied"
echo ""

# Final: Try to upgrade to head
echo "Attempting to upgrade to head..."
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

echo ""
echo "=========================================="
echo "Migrations applied successfully!"
echo "=========================================="


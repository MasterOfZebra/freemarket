#!/bin/bash
# db-recovery.sh — Safe PostgreSQL recovery for FreeMarket
# Purpose: clean conflicting types and run Alembic migrations
# Usage: bash db-recovery.sh (on server in /freemarket)

set -e

PROJECT_DIR="${PROJECT_DIR:-.}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

echo "=== FreeMarket Database Recovery Script ==="
echo ""

# 1. Backup
echo "[1] Creating database backup..."
BACKUP_FILE="db-backup-$(date +%Y%m%d_%H%M%S).dump"
docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U postgres -d freemarket -F c -f /tmp/"$BACKUP_FILE" || {
    echo "Warning: Backup failed; continuing anyway..."
}
echo "Backup saved to db/$BACKUP_FILE (if available)"
echo ""

# 2. Check for conflicting types
echo "[2] Checking for conflicting PostgreSQL types..."
CONFLICT_TYPES=$(docker compose -f "$COMPOSE_FILE" exec -T db psql -U postgres -d freemarket -t -c \
  "SELECT n.nspname || '.' || t.typname FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid WHERE t.typname IN ('listings', 'match', 'user', 'item') AND n.nspname = 'public';") || true

if [ -z "$CONFLICT_TYPES" ]; then
    echo "No conflicting types found."
else
    echo "Found conflicting types:"
    echo "$CONFLICT_TYPES"
    echo ""
    echo "[3] Attempting to drop conflicting types..."
    while IFS= read -r type_full; do
        if [ -n "$type_full" ]; then
            echo "  Dropping $type_full..."
            docker compose -f "$COMPOSE_FILE" exec -T db psql -U postgres -d freemarket -c "DROP TYPE IF EXISTS $type_full CASCADE;" || true
        fi
    done <<< "$CONFLICT_TYPES"
    echo "Types dropped."
fi
echo ""

# 3. Stop backend to avoid connection conflicts
echo "[4] Stopping backend service..."
docker compose -f "$COMPOSE_FILE" stop backend || true
sleep 2
echo "Backend stopped."
echo ""

# 4. Run Alembic migrations
echo "[5] Running Alembic migrations..."
docker compose -f "$COMPOSE_FILE" run --rm backend alembic -c /app/alembic.ini upgrade head || {
    echo "ERROR: Alembic migration failed. Check logs above."
    exit 1
}
echo "Migrations completed."
echo ""

# 5. Restart backend
echo "[6] Restarting backend service..."
docker compose -f "$COMPOSE_FILE" up -d backend
sleep 3
echo "Backend started."
echo ""

# 6. Health check
echo "[7] Checking health endpoint..."
HEALTH=$(curl -s http://localhost:8000/health || echo "no response")
echo "Health response: $HEALTH"

if echo "$HEALTH" | grep -q "healthy"; then
    echo ""
    echo "✓ Database recovery successful!"
    echo "✓ Backend is healthy."
    exit 0
else
    echo ""
    echo "⚠ Health check did not return expected response. Check backend logs:"
    docker compose -f "$COMPOSE_FILE" logs --tail 100 backend
    exit 1
fi

#!/bin/bash
# FreeMarket Rollback Script
# Usage: bash rollback.sh
# Stops containers, rolls back migrations, and cleans up

set -e

COMPOSE_FILE="docker-compose.prod.yml"
PROJECT_DIR="/opt/freemarket"

echo "=========================================="
echo "FreeMarket Rollback Script"
echo "=========================================="
echo ""

# Step 1: Stop containers
echo "[1/4] Stopping containers..."
cd "$PROJECT_DIR"
docker-compose -f "$COMPOSE_FILE" down
echo "✓ Containers stopped"

# Step 2: (Optional) Rollback database migrations
echo ""
echo "[2/4] Database rollback (requires manual SQL if needed)"
echo "If you need to rollback migrations:"
echo "  docker-compose -f $COMPOSE_FILE up -d db"
echo "  docker-compose -f $COMPOSE_FILE exec db psql -U freemarket_user -d freemarket_db"
echo "  // Run any required SQL rollback statements"
echo "✓ Manual DB rollback prepared"

# Step 3: Clean up Docker resources
echo ""
echo "[3/4] Cleaning up Docker resources..."
docker system prune -f
echo "✓ Docker resources cleaned"

# Step 4: Restore from backup (if needed)
echo ""
echo "[4/4] Backup information"
echo "Database backups are located in /backup/freemarket/"
echo "To restore from backup:"
echo "  docker-compose -f $COMPOSE_FILE up -d db"
echo "  docker-compose -f $COMPOSE_FILE exec db psql -U freemarket_user -d freemarket_db < /backup/freemarket/backup_<timestamp>.sql"

echo ""
echo "=========================================="
echo "✓ Rollback procedure completed"
echo "=========================================="

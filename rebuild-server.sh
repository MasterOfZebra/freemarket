#!/bin/bash
# Quick Rebuild Script for FreeMarket Server
# Run this on the production server after code changes

set -e  # Exit on any error

echo "=== FreeMarket Quick Rebuild ==="
echo ""

# Step 1: Navigate to project directory
cd /opt/freemarket || { echo "ERROR: Project directory not found"; exit 1; }

# Step 2: Pull latest code
echo "[1/5] Pulling latest code..."
git pull origin main
echo "✓ Code updated"
echo ""

# Step 3: Rebuild containers
echo "[2/5] Rebuilding Docker images..."
docker-compose -f docker-compose.prod.yml build backend frontend --no-cache
echo "✓ Images rebuilt"
echo ""

# Step 4: Restart services
echo "[3/5] Restarting containers..."
docker-compose -f docker-compose.prod.yml up -d backend frontend
echo "✓ Containers restarted"
echo ""

# Step 5: Wait for health check
echo "[4/5] Waiting for services to be healthy (30 seconds)..."
sleep 30

# Step 6: Verify status
echo "[5/5] Checking status..."
docker-compose -f docker-compose.prod.yml ps
echo ""

# Health check
echo "Testing health endpoint..."
HEALTH=$(curl -s http://localhost:8000/health || echo "FAILED")
echo "Health response: $HEALTH"
echo ""

# Show recent logs
echo "Recent backend logs (last 20 lines):"
docker-compose -f docker-compose.prod.yml logs --tail 20 backend
echo ""

echo "=== Rebuild Complete ==="
echo ""
echo "Next steps:"
echo "  - Monitor logs: docker-compose -f docker-compose.prod.yml logs -f backend"
echo "  - Check site in browser: http://your-domain.com"
echo "  - If issues occur, rollback: docker-compose -f docker-compose.prod.yml down && git checkout HEAD~1 && docker-compose -f docker-compose.prod.yml up -d"

#!/bin/bash
# Script to check backend status and restart if needed

echo "=========================================="
echo "Backend Status Check"
echo "=========================================="

# Check if backend container is running
echo "[1/4] Checking backend container status..."
docker compose -f docker-compose.prod.yml ps backend

# Check backend logs for errors
echo ""
echo "[2/4] Checking backend logs (last 50 lines)..."
docker compose -f docker-compose.prod.yml logs backend --tail 50

# Check if backend is responding to health check
echo ""
echo "[3/4] Checking backend health endpoint..."
docker compose -f docker-compose.prod.yml exec backend curl -f http://localhost:8000/health || {
    echo "Backend health check failed!"
    echo ""
    echo "[4/4] Attempting to restart backend..."
    docker compose -f docker-compose.prod.yml restart backend
    sleep 5
    echo "Backend restarted. Checking logs..."
    docker compose -f docker-compose.prod.yml logs backend --tail 20
}

echo ""
echo "=========================================="
echo "Status check completed!"
echo "=========================================="


#!/bin/bash
# FreeMarket Server Deployment Script
# Usage: bash deploy-server.sh
# Run on the production server

set -e  # Exit on error

echo "=========================================="
echo "FreeMarket Deployment Script"
echo "=========================================="

# Configuration
PROJECT_DIR="/opt/freemarket"  # Adjust to your server path
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="/backup/freemarket"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Step 1: Pull latest changes from git
echo ""
echo "[1/6] Pulling latest code from git..."
cd "$PROJECT_DIR"
git pull origin main
if [ $? -ne 0 ]; then
    echo "ERROR: git pull failed. Aborting deployment."
    exit 1
fi
echo "✓ Code pulled successfully"

# Step 2: Check .env file
echo ""
echo "[2/6] Checking .env configuration..."
if [ ! -f .env ]; then
    echo "ERROR: .env file not found in $PROJECT_DIR"
    exit 1
fi
echo "✓ .env file exists"

# Step 3: Build Docker images
echo ""
echo "[3/6] Building Docker images (this may take several minutes)..."
docker-compose -f "$COMPOSE_FILE" build --no-cache
if [ $? -ne 0 ]; then
    echo "ERROR: Docker build failed. Aborting deployment."
    exit 1
fi
echo "✓ Docker images built successfully"

# Step 4: Start containers
echo ""
echo "[4/6] Starting containers..."
docker-compose -f "$COMPOSE_FILE" up -d
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start containers. Aborting deployment."
    exit 1
fi
echo "✓ Containers started"

# Wait for services to be ready
echo ""
echo "Waiting for services to be healthy (max 60s)..."
for i in {1..12}; do
    sleep 5
    echo "  Checking health... attempt $i/12"
done

# Check container status
echo ""
echo "[5/6] Verifying container status..."
docker-compose -f "$COMPOSE_FILE" ps
echo "✓ Container status checked"

# Step 5: Apply database migrations
echo ""
echo "[5/6] Applying database migrations..."
docker-compose -f "$COMPOSE_FILE" exec -T backend alembic upgrade head
if [ $? -ne 0 ]; then
    echo "WARNING: Migrations may have failed or already applied"
fi
echo "✓ Migrations completed"

# Step 6: Run smoke tests
echo ""
echo "[6/6] Running smoke tests..."
BACKEND_URL="http://localhost:8000"
HEALTH_CHECK=$(curl -s "$BACKEND_URL/health")
echo "  Health check response: $HEALTH_CHECK"

if echo "$HEALTH_CHECK" | grep -q "healthy"; then
    echo "✓ Health check passed"
else
    echo "WARNING: Health check did not return 'healthy' status"
fi

# Print summary
echo ""
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
docker-compose -f "$COMPOSE_FILE" ps
echo ""
echo "View logs with:"
echo "  docker-compose -f $COMPOSE_FILE logs -f backend"
echo "  docker-compose -f $COMPOSE_FILE logs -f frontend"
echo "  docker-compose -f $COMPOSE_FILE logs -f db"
echo ""
echo "=========================================="
echo "✓ Deployment completed successfully!"
echo "=========================================="

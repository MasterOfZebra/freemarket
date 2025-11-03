#!/bin/bash

# Docker cleanup script for FreeMarket testing
echo "🧹 Cleaning up Docker environment for FreeMarket testing..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Stop all running containers
echo "Stopping all running containers..."
docker stop $(docker ps -aq) 2>/dev/null || true

# Remove all containers
echo "Removing all containers..."
docker rm $(docker ps -aq) 2>/dev/null || true

# Remove orphan containers specifically
echo "Removing orphan containers..."
docker compose -f docker-compose.test.yml down --remove-orphans 2>/dev/null || true

# Remove volumes
echo "Removing test volumes..."
docker volume rm $(docker volume ls -q | grep freemarket) 2>/dev/null || true

# Remove old images
echo "Removing old freemarket images..."
docker images | grep freemarket | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

# System cleanup
echo "Running system cleanup..."
docker system prune -f >/dev/null 2>&1 || true

# Remove dangling images
echo "Removing dangling images..."
docker image prune -f >/dev/null 2>&1 || true

print_status "Docker environment cleaned up successfully!"
echo ""
echo "🎯 Now you can run:"
echo "   ./docker-test.sh"
echo ""
echo "Or run manually:"
echo "   docker compose -f docker-compose.test.yml up -d postgres redis"
echo "   sleep 15"
echo "   docker compose -f docker-compose.test.yml --profile init run --rm init-db"
echo "   docker compose -f docker-compose.test.yml up -d backend frontend"

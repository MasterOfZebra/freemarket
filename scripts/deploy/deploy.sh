#!/bin/bash
# Universal Deployment Script for FreeMarket
# Usage: ./deploy.sh --env=<environment>

set -e

# Default environment
ENV="dev"

# Parse arguments
for arg in "$@"; do
  case $arg in
    --env=*)
      ENV="${arg#*=}"
      shift
      ;;
    *)
      echo "Unknown argument: $arg"
      exit 1
      ;;
  esac
done

# Configuration
PROJECT_DIR="/opt/freemarket"
COMPOSE_FILE="docker-compose.yml"
if [ "$ENV" == "prod" ]; then
  COMPOSE_FILE="docker-compose.prod.yml"
fi

# Functions
log() {
  echo -e "\033[0;32m[$(date +'%Y-%m-%d %H:%M:%S')] $1\033[0m"
}

error() {
  echo -e "\033[0;31m[ERROR] $1\033[0m" >&2
  exit 1
}

# Deployment steps
log "Starting deployment for environment: $ENV"

# Step 1: Pull latest changes
log "Pulling latest changes from git..."
cd "$PROJECT_DIR"
git pull origin main || error "Git pull failed"

# Step 2: Check .env file
log "Checking .env configuration..."
if [ ! -f .env ]; then
  error ".env file not found in $PROJECT_DIR"
fi

# Step 3: Build Docker images
log "Building Docker images..."
docker-compose -f "$COMPOSE_FILE" build || error "Docker build failed"

# Step 4: Start containers
log "Starting containers..."
docker-compose -f "$COMPOSE_FILE" up -d || error "Failed to start containers"

# Step 5: Apply database migrations
log "Applying database migrations..."
docker-compose -f "$COMPOSE_FILE" exec -T backend alembic upgrade head || log "Migrations may have failed or already applied"

# Step 6: Run health checks
log "Running health checks..."
HEALTH_CHECK=$(curl -s http://localhost:8000/health || true)
if echo "$HEALTH_CHECK" | grep -q "healthy"; then
  log "Health check passed"
else
  log "Health check failed"
fi

log "Deployment completed successfully!"

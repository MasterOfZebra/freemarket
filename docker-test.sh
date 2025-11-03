#!/bin/bash

# Docker testing script for FreeMarket user cabinet system
set -e

echo "🐳 FreeMarket Docker Testing Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_status "Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    print_error "docker-compose is not installed"
    exit 1
fi

print_status "Docker Compose is available"

# Function to use docker compose (v2) or docker-compose (v1)
docker_compose_cmd() {
    if docker compose version >/dev/null 2>&1; then
        docker compose "$@"
    else
        docker-compose "$@"
    fi
}

echo ""
echo "🏗️  Building and starting services..."

# Stop any existing containers
print_info "Stopping existing containers..."
docker_compose_cmd -f docker-compose.test.yml down --volumes --remove-orphans 2>/dev/null || true

# Build and start services
print_info "Building services..."
docker_compose_cmd -f docker-compose.test.yml build --no-cache

print_info "Starting database and Redis..."
docker_compose_cmd -f docker-compose.test.yml up -d postgres redis

# Wait for database to be ready
print_info "Waiting for database to be ready..."
sleep 15

# Initialize database
print_info "Initializing database..."
docker_compose_cmd -f docker-compose.test.yml --profile init run --rm init-db

# Start backend
print_info "Starting backend..."
docker_compose_cmd -f docker-compose.test.yml up -d backend

# Wait for backend to be ready
print_info "Waiting for backend to be ready..."
sleep 10

# Start frontend
print_info "Starting frontend..."
docker_compose_cmd -f docker-compose.test.yml up -d frontend

echo ""
print_status "All services started successfully!"
echo ""
echo "🌐 Access URLs:"
echo "  Frontend:     http://localhost:3001"
echo "  Backend API:  http://localhost:8001"
echo "  API Docs:     http://localhost:8001/docs"
echo "  Categories:   http://localhost:8001/v1/categories"
echo ""
echo "🧪 Test commands:"
echo ""

# Test database connection
echo "# Test database connectivity:"
echo "docker_compose_cmd -f docker-compose.test.yml exec backend python -c \""
echo "from backend.database import engine; "
echo "from sqlalchemy import text; "
echo "with engine.connect() as conn: "
echo "    result = conn.execute(text('SELECT 1')); "
echo "    print('Database connection: OK')\""
echo ""

# Test API endpoints
echo "# Test API endpoints:"
echo "curl -f http://localhost:8001/health"
echo "curl -f http://localhost:8001/v1/categories | jq ."
echo ""

# Test user registration
echo "# Test user registration:"
echo "curl -X POST http://localhost:8001/auth/register \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"email\": \"test@example.com\","
echo "    \"password\": \"testpass123\","
echo "    \"full_name\": \"Test User\","
echo "    \"city\": \"Алматы\""
echo "  }'"
echo ""

echo "# Test user login:"
echo "curl -X POST http://localhost:8001/auth/login \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -c cookies.txt -b cookies.txt \\"
echo "  -d '{"
echo "    \"identifier\": \"test@example.com\","
echo "    \"password\": \"testpass123\""
echo "  }'"
echo ""

echo "# Test user cabinet (needs auth):"
echo "curl -X GET http://localhost:8001/user/cabinet \\"
echo "  -b cookies.txt"
echo ""

echo "🛑 To stop testing:"
echo "docker_compose_cmd -f docker-compose.test.yml down --volumes"
echo ""

print_info "Services are running. Open http://localhost:3001 in your browser to test the UI."
print_warning "Don't forget to stop the services when done: docker_compose_cmd -f docker-compose.test.yml down --volumes"

#!/bin/bash
set -e

echo "🚀 Starting deployment to /freemarket..."

cd /freemarket

# Ensure .env exists with required variables
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
DATABASE_URL=postgresql://assistadmin_pg:assistMurzAdmin@192.168.1.9:5432/assistance_kz
TELEGRAM_BOT_TOKEN=8400094200:AAEbfXLH-aGIUhgJlJmg7-TNqsHKYCtWPGg
REDIS_URL=redis://redis:6379/0
DB_PASSWORD=assistMurzAdmin
EOF
else
    echo "✓ .env already exists"
fi

# Git pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main || echo "⚠ Git pull skipped"

# Build backend
echo "🔨 Building backend container..."
docker compose -f docker-compose.prod.yml build backend

# Start backend
echo "🚀 Starting backend..."
docker compose -f docker-compose.prod.yml up -d backend

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 10

# Apply migrations
echo "📊 Applying Alembic migrations..."
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

# Seed categories
echo "🌱 Seeding categories..."
docker compose -f docker-compose.prod.yml exec -T backend python scripts/seed_categories.py

# Health check
echo "✅ Running health check..."
curl -f http://localhost:8000/health || echo "⚠ Health check endpoint not responding yet"

echo "✨ Deployment completed!"
echo ""
echo "📋 API Endpoints:"
echo "  - GET  /categories?section=wants"
echo "  - GET  /categories?section=offers"
echo "  - GET  /market-listings?type=wants&page=1"
echo "  - POST /market-listings (create new listing)"

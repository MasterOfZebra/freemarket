# 🚀 FreeMarket Deployment Guide

**Version:** 2.0 | **Last Updated:** January 2025

---

## 📋 Deployment Overview

This guide covers production deployment using **Docker Compose**.

**Stack:**
- 🐳 Docker & Docker Compose
- 🖥️ Ubuntu/Linux Server
- 🌐 Nginx (reverse proxy)
- 🐘 PostgreSQL (database)
- 🔴 Redis (caching)
- 🤖 Telegram Bot (notifications)

---

## 🛠️ Prerequisites

**Server Requirements:**
- Ubuntu 20.04+ or similar Linux
- Docker installed (`docker --version`)
- Docker Compose installed (`docker-compose --version`)
- Minimum: 2GB RAM, 10GB disk
- Open ports: 80 (HTTP), 443 (HTTPS optional)

**Database:**
- PostgreSQL 12+ (can be external or containerized)
- Database name: `assistance_kz`
- User: `assistadmin_pg`
- Password: `assistMurzAdmin` (or use env var)

**Third-party Services:**
- Telegram Bot Token (from @BotFather)

---

## 📦 Docker Setup

### Step 1: Clone Repository

```bash
# SSH into your server
ssh user@your-server-ip

# Clone the repository
git clone https://github.com/YourOrg/freemarket.git
cd freemarket
```

### Step 2: Create Environment File

```bash
# Create .env for production
cat > .env << EOF
# Database
DATABASE_URL=postgresql://assistadmin_pg:assistMurzAdmin@postgres:5432/assistance_kz

# Redis
REDIS_URL=redis://redis:6379/0

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Environment
ENV=production
DEBUG=false

# API Settings
API_TITLE=FreeMarket API
API_VERSION=1.0.0
LOG_LEVEL=INFO
EOF

chmod 600 .env  # Restrict permissions
```

### Step 3: Verify docker-compose.prod.yml

```bash
# Check production config
cat docker/docker-compose.prod.yml
```

**Expected services:**
- `frontend` - React app (port 80)
- `backend` - FastAPI (port 8000)
- `bot` - Telegram bot
- `postgres` - Database
- `redis` - Cache

### Step 4: Build Images

```bash
# Build all Docker images
docker-compose -f docker/docker-compose.prod.yml build

# Or build specific service
docker-compose -f docker/docker-compose.prod.yml build backend
```

**Expected output:**
```
Building backend
Building frontend
Building bot
...
Successfully built <hash>
```

### Step 5: Start Services

```bash
# Start all services in background
docker-compose -f docker/docker-compose.prod.yml up -d

# Verify services are running
docker-compose -f docker/docker-compose.prod.yml ps
```

**Expected output:**
```
NAME                  STATUS           PORTS
freemarket-frontend   Up 2 minutes     0.0.0.0:80->80/tcp
freemarket-backend    Up 2 minutes     0.0.0.0:8000->8000/tcp
freemarket-bot        Up 2 minutes
freemarket-postgres   Up 2 minutes     0.0.0.0:5432->5432/tcp
freemarket-redis      Up 2 minutes     0.0.0.0:6379->6379/tcp
```

### Step 6: Initialize Database

```bash
# Create tables
docker-compose -f docker/docker-compose.prod.yml exec backend python backend/init_db.py

# Expected output:
# Created table: users
# Created table: items
# Created table: matches
# Created table: exchange_chains
# Created table: notifications
```

---

## ✅ Verify Deployment

### Test Backend API

```bash
# Health check
curl http://your-server-ip:8000/health
# Expected: {"status": "ok", "message": "FreeMarket API is running"}

# Get API info
curl http://your-server-ip:8000/
# Expected: {"message": "FreeMarket API", "version": "1.0.0"}
```

### Test Frontend

```bash
# Open in browser
http://your-server-ip

# Should show FreeMarket homepage
```

### Check Database

```bash
# Connect to database
docker-compose -f docker/docker-compose.prod.yml exec postgres \
  psql -U assistadmin_pg -d assistance_kz

# List tables
\dt

# Exit
\q
```

### Check Logs

```bash
# Backend logs
docker-compose -f docker/docker-compose.prod.yml logs backend -f

# Bot logs
docker-compose -f docker/docker-compose.prod.yml logs bot -f

# All logs
docker-compose -f docker/docker-compose.prod.yml logs -f
```

---

## 🔒 Security Configuration

### SSL/HTTPS Setup (Optional)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Update Nginx config to use SSL
# Edit: config/freemarket.nginx
# Add:
#   listen 443 ssl;
#   ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
#   ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
```

### Firewall Rules

```bash
# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS (if using SSL)
sudo ufw allow 443/tcp

# Allow SSH
sudo ufw allow 22/tcp

# Deny everything else
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable
```

### Database Security

```bash
# Change default password
docker-compose -f docker/docker-compose.prod.yml exec postgres \
  psql -U assistadmin_pg -d assistance_kz \
  -c "ALTER USER assistadmin_pg WITH PASSWORD 'new_secure_password';"

# Update .env file
sed -i 's/assistMurzAdmin/new_secure_password/g' .env
```

---

## 📊 Monitoring & Maintenance

### View Resource Usage

```bash
# CPU, Memory, Network stats
docker stats

# Specific service
docker stats freemarket-backend
```

### Database Backup

```bash
# Backup database
docker-compose -f docker/docker-compose.prod.yml exec postgres \
  pg_dump -U assistadmin_pg assistance_kz > backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose -f docker/docker-compose.prod.yml exec -T postgres \
  psql -U assistadmin_pg assistance_kz < backup_20250115.sql
```

### Clean Up Old Data

```bash
# Remove old Docker images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove stopped containers
docker container prune
```

### Update Code

```bash
# Pull latest changes
git pull origin main

# Rebuild images
docker-compose -f docker/docker-compose.prod.yml build

# Restart services
docker-compose -f docker/docker-compose.prod.yml up -d

# Check status
docker-compose -f docker/docker-compose.prod.yml ps
```

---

## 🐛 Troubleshooting

### Problem: Services won't start

```bash
# Check logs
docker-compose -f docker/docker-compose.prod.yml logs

# Verify images built
docker images

# Try rebuilding
docker-compose -f docker/docker-compose.prod.yml build --no-cache
docker-compose -f docker/docker-compose.prod.yml up -d
```

### Problem: Database connection error

```bash
# Verify PostgreSQL is running
docker-compose -f docker/docker-compose.prod.yml ps postgres

# Check connection
docker-compose -f docker/docker-compose.prod.yml exec backend \
  python -c "from backend.database import engine; print('Connected!' if engine.connect() else 'Failed')"

# View connection string
cat .env | grep DATABASE_URL
```

### Problem: Backend returns 500 errors

```bash
# Check backend logs
docker-compose -f docker/docker-compose.prod.yml logs backend --tail=50

# Restart backend
docker-compose -f docker/docker-compose.prod.yml restart backend

# Check health
curl http://localhost:8000/health
```

### Problem: Telegram bot not sending notifications

```bash
# Verify bot token
cat .env | grep TELEGRAM_BOT_TOKEN

# Check bot logs
docker-compose -f docker/docker-compose.prod.yml logs bot --tail=50

# Restart bot
docker-compose -f docker/docker-compose.prod.yml restart bot
```

---

## 📈 Performance Optimization

### Database Indexes

```bash
# Connect to database
docker-compose -f docker/docker-compose.prod.yml exec postgres \
  psql -U assistadmin_pg -d assistance_kz

# Create indexes (in PostgreSQL console)
CREATE INDEX idx_users_locations ON users USING gin(locations);
CREATE INDEX idx_items_user_id ON items(user_id);
CREATE INDEX idx_items_category ON items(category);
CREATE INDEX idx_matches_users ON matches(user_a_id, user_b_id);
CREATE INDEX idx_chains_status ON exchange_chains(status);

# Verify indexes
\d items
```

### Cache Configuration

```bash
# Check Redis connection
docker-compose -f docker/docker-compose.prod.yml exec redis redis-cli ping
# Expected: PONG

# Monitor Redis
docker-compose -f docker/docker-compose.prod.yml exec redis redis-cli monitor
```

### Nginx Optimization

```bash
# Edit config/freemarket.nginx
# Increase worker processes:
worker_processes auto;

# Increase connections
events {
    worker_connections 2048;
}

# Add caching headers
add_header Cache-Control "public, max-age=86400" for static files;
```

---

## 🔄 Scaling

### Horizontal Scaling

```bash
# Run multiple backend instances (Docker Swarm or Kubernetes)
# Update docker-compose.prod.yml:

services:
  backend:
    deploy:
      replicas: 3  # Run 3 instances
      
  nginx:
    ports:
      - "80:80"
    # Nginx will load-balance across 3 backend instances
```

### Vertical Scaling

```bash
# Increase resource limits in docker-compose.prod.yml

services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## 📋 Deployment Checklist

```
Pre-Deployment
  ☐ Code pushed to repository
  ☐ .env file created with all secrets
  ☐ Backups of existing database taken
  ☐ DNS records updated (if domain change)

Docker Setup
  ☐ Docker & Docker Compose installed
  ☐ docker-compose.prod.yml verified
  ☐ All images built successfully
  ☐ Services start without errors

Database
  ☐ PostgreSQL running
  ☐ Database tables created
  ☐ Initial data loaded (if needed)
  ☐ Backup configured

API Verification
  ☐ Health endpoint responds (200)
  ☐ Create user works
  ☐ Create listing works
  ☐ Matching pipeline runs

Bot Setup
  ☐ Telegram bot token set
  ☐ Bot receives messages
  ☐ Notifications send correctly

Monitoring
  ☐ Logs accessible
  ☐ Health checks configured
  ☐ Backup script scheduled (cron)
  ☐ Disk space monitor set up

Security
  ☐ Firewall rules configured
  ☐ SSL certificate installed (optional)
  ☐ Database password changed
  ☐ SSH key-only access enabled
  ☐ No secrets in code/logs
```

---

## 🚀 Quick Deploy Script

```bash
#!/bin/bash
# deploy.sh - Quick deployment script

set -e  # Exit on error

echo "🚀 Starting FreeMarket deployment..."

# 1. Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# 2. Build images
echo "🔨 Building Docker images..."
docker-compose -f docker/docker-compose.prod.yml build

# 3. Stop old services
echo "🛑 Stopping old services..."
docker-compose -f docker/docker-compose.prod.yml down

# 4. Start new services
echo "🚀 Starting new services..."
docker-compose -f docker/docker-compose.prod.yml up -d

# 5. Initialize database
echo "💾 Initializing database..."
docker-compose -f docker/docker-compose.prod.yml exec backend \
  python backend/init_db.py

# 6. Verify
echo "✅ Verifying deployment..."
curl -s http://localhost:8000/health | grep -q "ok" && echo "✅ API OK" || echo "❌ API FAILED"

echo "✅ Deployment complete!"
```

**Usage:**
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📞 Support

**Common Issues:**
- See [docs/TESTING.md](./TESTING.md) for debugging
- Check logs: `docker-compose logs -f`
- Reset database: `docker-compose down -v`

**Documentation:**
- [docs/ARCHITECTURE.md](./ARCHITECTURE.md) - System design
- [docs/API_REFERENCE.md](./API_REFERENCE.md) - API endpoints
- [docs/CONFIGURATION.md](./CONFIGURATION.md) - Environment variables

---

**Ready to deploy? Start with Step 1: Clone Repository ⬆️**

# FreeMarket Quick Reference Commands

## On Production Server

### Initial Deployment
```bash
cd /opt/freemarket
bash deploy-server.sh
```

### After Deployment - Smoke Tests
```bash
bash smoke-tests.sh http://your-server-ip:8000
```

### View Container Status
```bash
docker-compose -f docker-compose.prod.yml ps
```

### View Live Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f db
docker-compose -f docker-compose.prod.yml logs -f redis
```

### Restart Services
```bash
# All services
docker-compose -f docker-compose.prod.yml restart

# Specific service
docker-compose -f docker-compose.prod.yml restart backend
```

### Stop Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### Start Services
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Apply Database Migrations
```bash
docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
```

### Run Backend Tests
```bash
docker-compose -f docker-compose.prod.yml exec backend python -m pytest backend/ -v
```

### Enter Backend Container Shell
```bash
docker-compose -f docker-compose.prod.yml exec backend /bin/bash
```

### Access PostgreSQL Database
```bash
docker-compose -f docker-compose.prod.yml exec db psql -U freemarket_user -d freemarket_db
```

### Redis CLI
```bash
docker-compose -f docker-compose.prod.yml exec redis redis-cli
```

## Manual Smoke Tests (curl)

### Health Check
```bash
curl -X GET http://your-server-ip:8000/health
```

### Create User
```bash
curl -X POST http://your-server-ip:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","contact":"test@example.com"}'
```

### List Users
```bash
curl -X GET http://your-server-ip:8000/users/testuser
```

### Create Profile
```bash
curl -X POST http://your-server-ip:8000/profiles/ \
  -H "Content-Type: application/json" \
  -d '{
    "username":"testuser",
    "name":"Test User",
    "category":"Electronics",
    "description":"Test profile",
    "location":"Almaty"
  }'
```

### List Market Listings
```bash
curl -X GET "http://your-server-ip:8000/market-listings/" \
  -H "Content-Type: application/json"
```

### List Categories
```bash
curl -X GET http://your-server-ip:8000/categories
```

## Backup & Rollback

### Backup Database
```bash
docker-compose -f docker-compose.prod.yml exec db pg_dump \
  -U freemarket_user -d freemarket_db > /backup/freemarket/backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database
```bash
docker-compose -f docker-compose.prod.yml exec db psql \
  -U freemarket_user -d freemarket_db < /backup/freemarket/backup_<timestamp>.sql
```

### Stop All Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### Clean Up Docker
```bash
docker system prune -f
docker system prune -a --volumes
```

## Monitoring

### Check Disk Usage
```bash
df -h
docker system df
```

### Check Container Resource Usage
```bash
docker stats
```

### Check System Logs
```bash
# Last 50 lines
docker-compose -f docker-compose.prod.yml logs --tail 50

# Follow logs
docker-compose -f docker-compose.prod.yml logs -f

# Logs from last 1 hour
docker-compose -f docker-compose.prod.yml logs --since 1h
```

## Environment & Configuration

### View Current Environment
```bash
cat .env
```

### Update Environment Variable
```bash
# Edit the .env file
nano .env

# Restart services to apply changes
docker-compose -f docker-compose.prod.yml restart backend
```

### Check Git Status
```bash
git status
git log --oneline -10
```

### Update Code
```bash
git pull origin main
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

## Emergency Commands

### Force Restart All
```bash
docker-compose -f docker-compose.prod.yml kill
docker-compose -f docker-compose.prod.yml up -d
```

### Reset Database (DANGEROUS - Will delete all data!)
```bash
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d db
# Wait for db to be healthy
docker-compose -f docker-compose.prod.yml exec db psql -U freemarket_user -d freemarket_db < backend/schema.sql
```

### View Backend Python Version
```bash
docker-compose -f docker-compose.prod.yml exec backend python --version
```

### Check All Installed Dependencies
```bash
docker-compose -f docker-compose.prod.yml exec backend pip list
```

---

For more details, see `DEPLOYMENT.md`

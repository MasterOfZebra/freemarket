# FreeMarket Server Deployment Guide

## Pre-Deployment Checklist

Before running the deployment, ensure:

- [ ] SSH access to production server
- [ ] Docker and docker-compose installed on server
- [ ] `.env` file exists on server with all required variables:
  - `DB_PASSWORD` (PostgreSQL password)
  - `TELEGRAM_BOT_TOKEN` (Telegram bot token)
  - `REDIS_URL` (Redis connection string)
- [ ] Sufficient disk space for Docker images and database
- [ ] Database backup created (optional but recommended)
- [ ] Git repository cloned at `/opt/freemarket` (or your custom path)

## Deployment Steps

### 1. SSH into Production Server

```bash
ssh user@your-server-ip
cd /opt/freemarket
```

### 2. Verify .env Configuration

```bash
cat .env | grep DB_PASSWORD
cat .env | grep TELEGRAM_BOT_TOKEN
cat .env | grep REDIS_URL
```

Ensure all critical variables are set.

### 3. Run Deployment Script

```bash
bash deploy-server.sh
```

This script will:
1. Pull latest code from git
2. Validate `.env` file
3. Build Docker images with `--no-cache`
4. Start containers using `docker-compose.prod.yml`
5. Wait for services to be healthy
6. Apply database migrations (alembic)
7. Run smoke tests

Expected output:
```
✓ Code pulled successfully
✓ Docker images built successfully
✓ Containers started
✓ Migrations completed
✓ Health check passed
✓ Deployment completed successfully!
```

### 4. Verify Deployment

Check container status:
```bash
docker-compose -f docker-compose.prod.yml ps
```

Expected output (all containers should be "Up"):
```
NAME                           STATUS
freemarket_backend_1           Up (healthy)
freemarket_frontend_1          Up
freemarket_db_1                Up (healthy)
freemarket_redis_1             Up
freemarket_nginx_1             Up
freemarket_bot_1               Up
```

### 5. Run Smoke Tests

```bash
bash smoke-tests.sh http://your-server-ip:8000
```

Or if using Nginx on port 80:
```bash
bash smoke-tests.sh http://your-server-ip
```

Expected tests:
- ✓ Health Check (HTTP 200)
- ✓ Create User (HTTP 200)
- ✓ Get User by Username (HTTP 200)
- ✓ Create Profile (HTTP 200)
- ✓ Get Profile (HTTP 200)
- ✓ Get Categories (HTTP 200)
- ✓ List Market Listings (HTTP 200)
- ✓ List Wants (HTTP 200)
- ✓ List Offers (HTTP 200)

### 6. Monitor Logs

Watch real-time logs:
```bash
# Backend logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Frontend logs
docker-compose -f docker-compose.prod.yml logs -f frontend

# Database logs
docker-compose -f docker-compose.prod.yml logs -f db

# All services
docker-compose -f docker-compose.prod.yml logs -f
```

## Rollback Procedure

If deployment fails or issues arise:

### 1. Stop Services

```bash
docker-compose -f docker-compose.prod.yml down
```

### 2. Run Rollback Script

```bash
bash rollback.sh
```

### 3. Manual Rollback (if needed)

```bash
# Restore database from backup
docker-compose -f docker-compose.prod.yml up -d db
docker-compose -f docker-compose.prod.yml exec db \
  psql -U freemarket_user -d freemarket_db < /backup/freemarket/backup_<timestamp>.sql
```

### 4. Restart Services

```bash
git checkout HEAD~1  # Go back to previous version
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Health Check Fails

```bash
# Check backend logs
docker-compose -f docker-compose.prod.yml logs backend

# Check database connection
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "from backend.database import SessionLocal; db = SessionLocal(); print('DB OK')"
```

### Container Crashes

```bash
# View detailed logs
docker-compose -f docker-compose.prod.yml logs --tail 100

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend
```

### Database Connection Issues

```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec db \
  pg_isready -U freemarket_user -d freemarket_db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db
```

### Out of Disk Space

```bash
# Clean up Docker resources
docker system prune -a

# Remove old images
docker image prune -a

# Check disk usage
df -h
docker system df
```

## Health Check Endpoint

The `/health` endpoint returns:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-22T12:34:56.789123"
}
```

If database or Redis is down, it returns HTTP 503.

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@db/freemarket_db` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot API token | `123456789:ABCD...` |
| `ENV` | Environment name | `production` |
| `LOG_LEVEL` | Logging level | `info` |

## Post-Deployment Checklist

- [ ] All containers are healthy (`docker-compose ps`)
- [ ] Smoke tests pass (`bash smoke-tests.sh`)
- [ ] Health endpoint returns 200 OK
- [ ] Frontend loads in browser
- [ ] Can create user and profile
- [ ] Can view market listings
- [ ] Monitor logs for 5-10 minutes for any errors
- [ ] Database has applied migrations successfully
- [ ] Redis is functioning (used for caching)

## Support

For issues or questions:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Review this guide's troubleshooting section
3. Check GitHub issues: https://github.com/MasterOfZebra/freemarket
4. Contact the development team

---

Last updated: 2025-10-22

# FreeMarket Quick Reference Commands

## Deployment

### Initial Deployment
```bash
cd /opt/freemarket
bash scripts/deploy/deploy.sh --env=prod
```

### After Deployment - Smoke Tests
```bash
bash smoke-tests.sh http://your-server-ip:8000
```

### View Container Status
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Restart Services
```bash
# All services
docker-compose -f docker-compose.prod.yml restart

# Specific service
docker-compose -f docker-compose.prod.yml restart backend
```

### Apply Database Migrations
```bash
docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
```

## Monitoring

### View Live Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Check Disk Usage
```bash
df -h
docker system df
```

### Check Container Resource Usage
```bash
docker stats
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

---

For more details, see `DEPLOYMENT.md`

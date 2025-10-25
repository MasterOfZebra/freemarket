# FreeMarket Deployment Guide

## Overview

This guide explains how to deploy the FreeMarket application using Docker and Docker Compose in a production environment.

---

## Prerequisites

1. **Server Requirements**:
   - Docker and Docker Compose installed.
   - At least 4GB of RAM and sufficient disk space.
2. **Environment Variables**:
   - Create a `.env` file in the project root with the following variables:
     ```env
     DB_PASSWORD=your_postgres_password
     TELEGRAM_BOT_TOKEN=your_telegram_bot_token
     REDIS_URL=redis://redis:6379/0
     DATABASE_URL=postgresql://user:password@db/freemarket_db
     ```
3. **Clone the Repository**:
   ```bash
   git clone https://github.com/MasterOfZebra/freemarket.git
   cd freemarket
   ```

---

## Building and Running Containers

### Step 1: Build Docker Images

Use the following command to build all services:
```bash
docker-compose -f docker-compose.prod.yml build
```

### Step 2: Start Services

Start all services in detached mode:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Step 3: Verify Services

Check the status of all containers:
```bash
docker-compose -f docker-compose.prod.yml ps
```

Expected output:
```
NAME                           STATUS
freemarket_backend_1           Up (healthy)
freemarket_frontend_1          Up
freemarket_db_1                Up (healthy)
freemarket_redis_1             Up
freemarket_nginx_1             Up
freemarket_bot_1               Up
```

---

## Health Checks

### Backend Health Check

The backend exposes a health check endpoint:
```bash
curl -X GET http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-25T12:34:56.789123"
}
```

### Nginx Health Check

Verify Nginx is serving the frontend:
```bash
curl -X GET http://localhost/
```

---

## Applying Database Migrations

Run Alembic migrations to ensure the database schema is up-to-date:
```bash
docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
```

---

## Logs and Monitoring

### View Logs

View logs for all services:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

View logs for a specific service (e.g., backend):
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Monitor Resource Usage

Check container resource usage:
```bash
docker stats
```

---

## Backup and Restore

### Backup Database

Create a database backup:
```bash
docker-compose -f docker-compose.prod.yml exec db pg_dump \
  -U freemarket_user -d freemarket_db > /backup/freemarket/backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

Restore the database from a backup:
```bash
docker-compose -f docker-compose.prod.yml exec db psql \
  -U freemarket_user -d freemarket_db < /backup/freemarket/backup_<timestamp>.sql
```

---

## Stopping and Restarting Services

### Stop All Services

Stop all running containers:
```bash
docker-compose -f docker-compose.prod.yml down
```

### Restart Services

Restart all services:
```bash
docker-compose -f docker-compose.prod.yml restart
```

---

## Troubleshooting

### Check Container Status

If a container is not running, check its logs:
```bash
docker-compose -f docker-compose.prod.yml logs <service_name>
```

### Rebuild and Restart

If changes were made to the code or configuration:
```bash
docker-compose -f docker-compose.prod.yml build

docker-compose -f docker-compose.prod.yml up -d
```

---

## Additional Notes

- Ensure the `.env` file is properly configured before starting the services.
- Regularly monitor logs and resource usage to ensure the application is running smoothly.
- Use health checks to verify the availability of services.

---

# Updated Deployment Guide

## Updated File Structure

The Dockerfiles have been moved to the `docker/` directory for better organization. Ensure the following paths are used in your `docker-compose.prod.yml`:

- Backend: `docker/Dockerfile.backend`
- Frontend: `docker/Dockerfile.frontend`
- Bot: `docker/Dockerfile.bot`

Additionally, the Nginx configuration file is now located in the `config/` directory:

- Nginx Config: `config/freemarket.nginx`

## Updated Commands

### Build Docker Images

```bash
docker-compose -f docker-compose.prod.yml build
```

### Start Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Verify Services

```bash
docker-compose -f docker-compose.prod.yml ps
```

Ensure all services are running and healthy.

---

Last updated: 2025-10-25

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

- Frontend: `src/` (Vite, React)
- Dockerfile for frontend: `docker/Dockerfile.frontend`
- No more `frontend/` or root `Dockerfile.frontend`


## Nginx Proxy Configuration (Production)

Nginx должен проксировать все запросы к API через путь `/api/` на backend без дополнительного префикса `/api`:

```
location /api/ {
   proxy_pass http://backend:8000/;
   proxy_set_header Host $host;
   proxy_set_header X-Real-IP $remote_addr;
   proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   proxy_set_header X-Forwarded-Proto $scheme;
}
```
Файл конфига: `config/freemarket.nginx`. После изменений перезапустите nginx:
```bash
docker compose -f docker-compose.prod.yml restart nginx
```

## Использование внешнего PostgreSQL

В продакшене может использоваться внешний сервер PostgreSQL (например, 192.168.1.9). В этом случае:

- В `.env` или переменных окружения укажите:
  ```env
  DATABASE_URL=postgresql://assistadmin_pg:assistMurzAdmin@192.168.1.9:5432/assistance_kz
  ```
- Проверьте доступность порта 5432:
  ```bash
  nc -vz 192.168.1.9 5432
  # или telnet 192.168.1.9 5432
  ```
- Проверьте подключение к базе:
  ```bash
  psql -h 192.168.1.9 -U assistadmin_pg assistance_kz
  # пароль: assistMurzAdmin
  ```

## Диагностика ошибок Input/output error и нехватки места

Если в логах backend или БД появляется ошибка `Input/output error`:

1. Проверьте свободное место:
  ```bash
  df -h
  ```
2. Очистите место:
  ```bash
  sudo du -h --max-depth=2 / | sort -hr | head -30
  sudo journalctl --vacuum-time=3d
  sudo rm -rf /var/log/*.gz /var/log/*.[0-9]
  docker system prune -af
  ```
3. После очистки перезапустите сервисы:
  ```bash
  docker compose -f docker-compose.prod.yml restart
  ```
4. Проверьте работу API и логи backend/postgres.

## Восстановление и диагностика PostgreSQL (внешний сервер)

1. Проверить процессы и конфиг на сервере БД:
  ```bash
  ps aux | grep postgres
  sudo find / -name postgresql.conf 2>/dev/null
  sudo ss -tlnp | grep 5432
  ```
2. Проверить логи PostgreSQL (на сервере БД):
  ```bash
  sudo tail -n 50 /var/log/postgresql/postgresql-*.log
  ```
3. Проверить состояние таблиц:
  ```sql
  \dt
  SELECT count(*) FROM market_listings;
  ```

## Мониторинг и резервное копирование

- Регулярно проверяйте место на диске и состояние БД.
- Настройте автоматические бэкапы (скрипты, cron, pg_dump).
- Используйте Prometheus/Alertmanager для мониторинга сервисов.

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

## Fixes for Build Errors

### Bot Service
- Ensure the `Dockerfile.bot` references the correct paths:
  - `COPY backend/requirements.bot.txt ./requirements.txt`
  - `COPY backend/bot.py .`

### Frontend Service
- Ensure the `Dockerfile.frontend` references the correct Nginx configuration:
  - `COPY backend/freemarket.nginx /etc/nginx/conf.d/default.conf`

### Commands to Rebuild and Restart
1. Rebuild the images:
   ```bash
   docker compose -f docker-compose.prod.yml build
   ```
2. Restart the services:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

### Verify Services
- Check the status of all containers:
  ```bash
  docker compose -f docker-compose.prod.yml ps
  ```
- Ensure all services are running and healthy.

---

## Frontend Build Issues
- Фронтенд теперь в `src/`, точка входа — `src/index.html`, основной скрипт — `src/main.jsx`.
- Dockerfile для фронта: `docker/Dockerfile.frontend`.

### Commands to Rebuild and Restart
1. Rebuild the images:
   ```bash
   docker compose -f docker-compose.prod.yml build
   ```
2. Restart the services:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

### Verify Services
- Check the status of all containers:
  ```bash
  docker compose -f docker-compose.prod.yml ps
  ```
- Ensure all services are running and healthy.

---

## Frontend Build Fixes

If you encounter the following error during the frontend build:

```
The `npm ci` command can only install with an existing package-lock.json or npm-shrinkwrap.json...
```

Follow these steps to resolve it:

1. **Generate `package-lock.json` Locally**:
   - Navigate to the `src` directory:
     ```bash
     cd src
     ```
   - Run `npm install` to generate the `package-lock.json` file:
     ```bash
     npm install
     ```

2. **Update the Dockerfile**:
   - Ensure the `Dockerfile.frontend` includes the following line to copy the `package-lock.json` file:
     ```dockerfile
     COPY src/package*.json src/package-lock.json ./
     ```

3. **Rebuild the Docker Image**:
   - Run the following command to rebuild the frontend image:
     ```bash
     docker compose build frontend
     ```

4. **Restart Services**:
   - Restart all services to apply the changes:
     ```bash
     docker compose up -d
     ```

5. **Verify Services**:
   - Check the status of all containers:
     ```bash
     docker compose ps
     ```
   - Ensure all services are running and healthy.

---

Last updated: 2025-10-25

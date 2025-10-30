# 📋 План развёртывания FreeMarket на сервере

## Цель

Развернуть полнофункциональное приложение FreeMarket на Linux-сервере с использованием Docker Compose, включая backend (FastAPI), frontend (React/Vite), PostgreSQL, Redis, Nginx и Telegram bot.

## Предварительные требования

- Ubuntu 20.04+ или другой Linux-дистрибутив
- SSH доступ к серверу с правами sudo
- Открытые порты: 80 (HTTP), 443 (HTTPS, опционально)
- Минимум 2GB RAM, 10GB свободного места на диске
- Telegram Bot Token (от @BotFather)

## Быстрый старт

```bash
sudo mkdir -p /opt/freemarket && sudo chown $USER:$USER /opt/freemarket
cd /opt/freemarket && git clone <your-repo-url> .
cp .env.example .env && nano .env   # заполните переменные
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
curl http://localhost/api/health
```

## Пошаговое развёртывание (ручное)

### Этап 1: Подготовка сервера

#### 1.1 Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

#### 1.2 Установка Docker (кратко)

```bash
sudo apt update && sudo apt install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
docker --version && docker compose version
```

#### 1.3 Настройка Docker (опц.)

```bash
# Добавление текущего пользователя в группу docker (для работы без sudo)
sudo usermod -aG docker $USER
newgrp docker

# Настройка автозапуска Docker
sudo systemctl enable docker
sudo systemctl start docker
```

#### 1.4 Утилиты (опц.)

```bash
sudo apt-get install -y git curl wget vim ufw
```

#### 1.5 Файрвол (опц.)

```bash
# Разрешение SSH
sudo ufw allow 22/tcp

# Разрешение HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включение файрвола
sudo ufw --force enable
sudo ufw status
```

### Этап 2: Клонирование проекта

#### 2.1 Создание директории проекта

```bash
# Рекомендуемая директория
sudo mkdir -p /opt/freemarket
sudo chown $USER:$USER /opt/freemarket
cd /opt/freemarket
```

#### 2.2 Клонирование репозитория

```bash
# Если проект в Git репозитории
git clone <your-repo-url> .

# Или копирование файлов проекта через SCP/rsync с локальной машины
# scp -r /path/to/FreeMarket/* user@server:/opt/freemarket/
```

#### 2.3 Проверка структуры проекта

```bash
ls -la
# Должны быть видны: backend/, src/, docker-compose.prod.yml, docker/, config/
```

### Этап 3: Настройка окружения

#### 3.1 .env

```bash
# ВАЖНО: Замените значения на реальные
nano .env
# или
vim .env
```

Обязательные: `DB_PASSWORD`, `TELEGRAM_BOT_TOKEN`. После правки: `chmod 600 .env`.

### Этап 4: Проверка конфигурации Docker

#### 4.1 Проверка docker-compose.prod.yml

```bash
cat docker-compose.prod.yml
# Убедитесь что все сервисы присутствуют: postgres, redis, backend, frontend, nginx, bot
```

#### 4.2 Dockerfile'ы (опц.)
`ls -la docker/` — должны быть `Dockerfile.backend`, `Dockerfile.frontend`, `Dockerfile.bot`.

#### 4.3 Проверка конфигурации Nginx

```bash
cat config/freemarket.nginx
# Проверьте корректность настроек проксирования
```

#### 4.4 Валидация конфигурации

```bash
docker compose -f docker-compose.prod.yml config
# Должен вывести валидную конфигурацию без ошибок
```

### Этап 5: Сборка Docker образов

#### 5.1 Сборка всех образов

```bash
cd /opt/freemarket
docker compose -f docker-compose.prod.yml build --no-cache
```

**Примечание:** Первая сборка может занять 10-20 минут в зависимости от скорости интернета.

#### 5.2 Проверка созданных образов

```bash
docker images | grep freemarket
# Должны быть: freemarket_backend, freemarket_frontend, freemarket_bot
```

### Этап 6: Запуск сервисов

#### 6.1 Запуск контейнеров в фоновом режиме

```bash
cd /opt/freemarket
docker compose -f docker-compose.prod.yml up -d
```

#### 6.2 Проверка статуса контейнеров

```bash
docker compose -f docker-compose.prod.yml ps
# Все контейнеры должны быть в статусе "Up"
```

#### 6.3 Логи
`docker compose -f docker-compose.prod.yml logs -f [service]`

### Этап 7: Применение миграций базы данных

#### 7.1 Проверка PostgreSQL (опц.)
`docker compose -f docker-compose.prod.yml exec postgres pg_isready -U assistadmin_pg`

#### 7.2 Применение миграций Alembic

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

#### 7.3 Проверка БД (опц.)
Мини-тест подключения к БД доступен в логах backend при старте.

### Этап 8: Проверка работоспособности

#### 8.1 Health check backend

```bash
curl http://localhost:8000/health
# Ожидается: {"status":"ok","message":"FreeMarket API is running"}
```

#### 8.2 Frontend
`curl http://localhost` — должен вернуть HTML.

#### 8.3 Проверка API через Nginx

```bash
curl http://localhost/api/health
# Должен проксировать запрос к backend
```

#### 8.4 Проверка статуса всех контейнеров

```bash
docker compose -f docker-compose.prod.yml ps
```

### Этап 9: Настройка автозапуска и мониторинга

#### 9.1 Настройка автозапуска контейнеров при перезагрузке

```bash
# Docker Compose уже настроен с restart: unless-stopped в docker-compose.prod.yml
# Проверка:
docker compose -f docker-compose.prod.yml config | grep restart
```

#### 9.2 Создание systemd service (опционально)

```bash
sudo tee /etc/systemd/system/freemarket.service > /dev/null << 'EOF'
[Unit]
Description=FreeMarket Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/freemarket
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable freemarket.service
```

### Этап 10: Резервное копирование и обслуживание

#### 10.1 Резервное копирование базы данных

```bash
# Создание бэкапа PostgreSQL
docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U assistadmin_pg assistance_kz > backup_$(date +%Y%m%d_%H%M%S).sql

# Или использование скрипта
bash scripts/backup_db.sh
```

#### 10.2 Восстановление из бэкапа

```bash
# Использование скрипта восстановления
bash scripts/restore_db.sh /backup/freemarket/backup_YYYYMMDD_HHMMSS.sql.gz
```

#### 10.3 Просмотр использования ресурсов

```bash
docker stats
```

#### 10.4 Очистка неиспользуемых образов и контейнеров

```bash
docker system prune -a --volumes
# ВНИМАНИЕ: Это удалит все неиспользуемые ресурсы
```

## Устранение неполадок

### Проблема: Контейнеры не запускаются

```bash
# Проверка логов
docker compose -f docker-compose.prod.yml logs

# Проверка конфигурации
docker compose -f docker-compose.prod.yml config

# Пересборка без кэша
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

### Проблема: База данных не подключается

```bash
# Проверка статуса PostgreSQL
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U assistadmin_pg

# Проверка переменных окружения
docker compose -f docker-compose.prod.yml exec backend env | grep DATABASE

# Перезапуск PostgreSQL
docker compose -f docker-compose.prod.yml restart postgres
```

### Проблема: Frontend не отображается

```bash
# Проверка сборки frontend
docker compose -f docker-compose.prod.yml exec frontend ls -la /usr/share/nginx/html

# Проверка Nginx конфигурации
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# Перезапуск Nginx
docker compose -f docker-compose.prod.yml restart nginx
```

## Быстрые команды
```bash
# Перезапуск / остановка
docker compose -f docker-compose.prod.yml restart
docker compose -f docker-compose.prod.yml down

# Обновление и миграции
git pull && docker compose -f docker-compose.prod.yml build --no-cache && docker compose -f docker-compose.prod.yml up -d && docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Логи и здоровье
docker compose -f docker-compose.prod.yml logs -f backend
curl http://localhost/api/health && docker compose -f docker-compose.prod.yml ps
```

## Дополнительные шаги (опционально)

### Настройка SSL/TLS (Let's Encrypt)

```bash
# Установка Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo certbot renew --dry-run
```

### Настройка мониторинга (Prometheus/Grafana)

```bash
# Использование существующего docker-compose.monitoring.yml
cd /opt/freemarket/monitoring
docker compose -f docker-compose.monitoring.yml up -d
```

## Финальная проверка

После завершения всех этапов выполните:

```bash
# 1. Проверка статуса всех контейнеров
docker compose -f docker-compose.prod.yml ps

# 2. Проверка health endpoints
curl http://localhost/api/health
curl http://localhost/health

# 3. Проверка доступности frontend
curl -I http://localhost

# 4. Проверка логов на ошибки
docker compose -f docker-compose.prod.yml logs | grep -i error
```

## Файлы проекта, которые используются

- `docker-compose.prod.yml` - основная конфигурация Docker Compose
- `docker/Dockerfile.backend` - образ для FastAPI backend
- `docker/Dockerfile.frontend` - образ для React frontend
- `docker/Dockerfile.bot` - образ для Telegram bot
- `config/freemarket.nginx` - конфигурация Nginx reverse proxy
- `backend/requirements.txt` - зависимости Python backend
- `backend/alembic/` - миграции базы данных
- `.env` - переменные окружения (создаётся на сервере)
- `.env.example` - шаблон переменных окружения

## Скрипты автоматизации

- `scripts/deploy/full_deployment.sh` - полное автоматическое развёртывание (все 10 этапов)
- `scripts/backup_db.sh` - резервное копирование базы данных
- `scripts/restore_db.sh` - восстановление базы данных из бэкапа
- `scripts/quick_commands.sh` - быстрые команды для управления

## Поддержка
1) Логи: `docker compose -f docker-compose.prod.yml logs`  2) Статус: `ps`  3) Конфиг: `config`


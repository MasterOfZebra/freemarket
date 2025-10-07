# FreeMarket — Архитектура и Развертывание

## Архитектура проекта

FreeMarket — это полнофункциональное веб-приложение для обмена товарами/услугами с системой матчинга, Telegram-ботом и мониторингом. Проект построен на микросервисной архитектуре с использованием Docker для контейнеризации.

### Компоненты системы

#### Backend (FastAPI)
- **Файлы**: `backend/main.py`, `backend/models.py`, `backend/crud.py`, `backend/schemas.py`, `backend/matching.py`
- **Функциональность**:
  - REST API для управления пользователями, профилями, товарами, матчами и рейтингами
  - Алгоритм матчинга на основе TF-IDF и косинусного сходства
  - Интеграция с Telegram-ботом для уведомлений
- **Технологии**: FastAPI, SQLAlchemy, PostgreSQL, Redis (для кэша), scikit-learn
- **Эндпоинты**:
  - `GET /health` — health check
  - `POST /users/` — создание пользователя
  - `GET /users/{id}` — получение пользователя
  - `POST /profiles/` — создание профиля
  - `GET /profiles/{user_id}` — получение профилей пользователя
  - `GET /matches/{user_id}` — получение матчей
  - `POST /ratings/` — создание рейтинга

#### Database (PostgreSQL)
- **Версия**: PostgreSQL 15
- **Схема**: `backend/schema.sql`
- **Таблицы**:
  - `users` — пользователи (id, telegram_id, username, contact, trust_score)
  - `profiles` — профили (id, user_id, data, location, visibility)
  - `items` — товары (id, user_id, kind, category, title, description, metadata, active)
  - `matches` — матчи (id, item_a, item_b, score, computed_by)
  - `ratings` — рейтинги (id, from_user, to_user, score, comment, tx_id)
  - `notifications` — уведомления (id, user_id, channel, payload, status, sent_at)

#### Bot (Aiogram)
- **Файл**: `backend/bot.py`
- **Функциональность**: Отправка уведомлений о матчах через Telegram
- **Технологии**: Aiogram 3.x

#### Frontend (React)
- **Файлы**: `src/` (исходники), `package.json`
- **Функциональность**: Веб-интерфейс для пользователей
- **Технологии**: React 18, React Router, Axios
- **Сборка**: Create React App

#### Monitoring (Prometheus + Alertmanager)
- **Файлы**: `monitoring/prometheus.yml`, `monitoring/alert_rules.yml`, `monitoring/alertmanager.yml`
- **Метрики**: CPU, память, диск, статус сервисов, время отклика
- **Алерты**: Email и Telegram webhook

#### Infrastructure
- **Docker Compose**: `docker-compose.prod.yml` для продакшена, `backend/docker-compose.yml` для разработки
- **Nginx**: Reverse proxy и статические файлы
- **Redis**: Кэш и очереди задач
- **Volumes**: `postgres_data`, `redis_data`

### Архитектурная диаграмма

```
[Пользователь] <-> [Nginx (80/443)]
                    |
                    +-> [Frontend (React)] <-> [Backend (FastAPI)] <-> [PostgreSQL]
                    |                                           |
                    |                                           +-> [Redis]
                    |
                    +-> [Bot (Aiogram)] <-> [Telegram API]
                    |
                    +-> [Monitoring (Prometheus/Alertmanager)]
```

### Поток данных
1. Пользователь регистрируется через API или бота
2. Создает профиль/товар
3. Backend запускает алгоритм матчинга
4. Находит подходящие матчи, создает уведомления
5. Бот отправляет уведомления в Telegram
6. Пользователи оценивают сделки, обновляется trust_score

## План развертывания на сервере

### Предпосылки
- Linux сервер (Ubuntu/Debian) с Docker и Docker Compose
- Домен (например, freemarket.com) с DNS на сервер
- TLS сертификаты (Let's Encrypt или Cloudflare)
- Переменные окружения: `DB_PASSWORD`, `TELEGRAM_BOT_TOKEN`

### Шаг 1: Подготовка сервера
```bash
# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Клонирование репозитория
git clone https://github.com/MasterOfZebra/user.git freemarket
cd freemarket

# Создание .env файла
cat > .env << EOF
DB_PASSWORD=your_strong_password_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
EOF
```

### Шаг 2: Сборка и запуск
```bash
# Сборка образов
docker compose -f docker-compose.prod.yml build

# Запуск всех сервисов
docker compose -f docker-compose.prod.yml up -d

# Проверка статуса
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
```

### Шаг 3: Настройка Nginx и TLS
```bash
# Получение сертификатов Let's Encrypt (опционально)
sudo apt install certbot
sudo certbot certonly --standalone -d freemarket.com

# Копирование сертификатов в папку ssl/
sudo cp /etc/letsencrypt/live/freemarket.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/freemarket.com/privkey.pem ssl/

# Перезапуск nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### Шаг 4: Инициализация базы данных
```bash
# Проверка схемы
docker compose -f docker-compose.prod.yml exec db psql -U freemarket_user -d freemarket_db -c "\dt"

# Создание тестового пользователя (опционально)
docker compose -f docker-compose.prod.yml exec backend python -c "
from backend.database import SessionLocal
from backend.models import User
db = SessionLocal()
user = User(telegram_id=123456789, username='test')
db.add(user)
db.commit()
print('Test user created')
"
```

### Шаг 5: Настройка мониторинга (опционально)
```bash
# Запуск Prometheus и Alertmanager
docker compose -f monitoring/docker-compose.monitoring.yml up -d

# Проверка доступа
curl http://localhost:9090  # Prometheus
curl http://localhost:9093  # Alertmanager
```

### Шаг 6: CI/CD (опционально)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Deploy to server
      run: |
        echo "${{ secrets.SSH_PRIVATE_KEY }}" > key
        chmod 600 key
        scp -i key -o StrictHostKeyChecking=no docker-compose.prod.yml user@server:/path/to/freemarket/
        ssh -i key user@server "cd /path/to/freemarket && docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend bot"
```

## Операционные задачи

### Бэкапы
```bash
# Настройка cron для ежедневных бэкапов
0 2 * * * /path/to/freemarket/pg_backup.sh
```

### Масштабирование
```bash
# Масштабирование backend
docker compose -f docker-compose.prod.yml up -d --scale backend=3

# Обновление образов
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend bot
```

### Мониторинг и логи
```bash
# Просмотр логов
docker compose -f docker-compose.prod.yml logs -f backend

# Метрики
curl http://freemarket.com/metrics  # Через nginx
```

### Безопасность
- Регулярные обновления образов
- Ограничение доступа к портам 5432, 6379
- Использование secrets для переменных окружения
- Настройка firewall (ufw)

## Чек-лист перед развертыванием
- [ ] .env файл создан с корректными секретами
- [ ] DNS настроен на сервер
- [ ] Сертификаты TLS готовы
- [ ] Docker и Docker Compose установлены
- [ ] Репозиторий склонирован
- [ ] docker compose up -d проходит без ошибок
- [ ] /health возвращает 200
- [ ] База данных инициализирована
- [ ] Фронтенд доступен по домену
- [ ] Бот получает токен и работает

## Troubleshooting
- **Backend не стартует**: Проверить DATABASE_URL и подключение к БД
- **Frontend не загружается**: Проверить сборку образа и nginx конфиг
- **Бот не отправляет сообщения**: Проверить TELEGRAM_BOT_TOKEN
- **Высокая нагрузка**: Проверить метрики в Prometheus, оптимизировать запросы

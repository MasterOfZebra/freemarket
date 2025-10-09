# 🛒 Freemarket

Open-source платформа обмена товарами и услугами с матчинговым алгоритмом и Telegram-ботом.

## 🚀 Стек технологий
- Backend: FastAPI (Python), SQLAlchemy
- Database: PostgreSQL (локально может использоваться SQLite)
- Frontend: React (CRA)
- Containerization: Docker, Docker Compose
- Monitoring: Prometheus, Alertmanager
- Bot: Aiogram (Telegram)

## 📂 Структура репозитория
```
FreeMarket/
├─ backend/
│  ├─ main.py            # FastAPI приложение
│  ├─ models.py          # SQLAlchemy модели
│  ├─ schemas.py         # Pydantic схемы
│  ├─ crud.py            # CRUD-логика
│  ├─ matching.py        # Матчинг (TF-IDF + cosine)
│  ├─ database.py        # Подключение к БД
│  ├─ requirements.txt   # Зависимости бэкенда
│  ├─ schema.sql         # Инициализация БД
│  └─ bot.py             # Telegram-бот (Aiogram)
├─ src/                  # React frontend (dev из корня через package.json)
├─ monitoring/           # Prometheus/Alertmanager конфиги
├─ Dockerfile.backend    # Backend образ
├─ Dockerfile.frontend   # Frontend образ
├─ docker-compose.prod.yml
├─ docs/
│  ├─ ARCHITECTURE.md    # Архитектура
│  └─ DEPLOYMENT.md      # План развертывания
└─ .github/workflows/ci-cd.yml
```

## ⚙️ Быстрый старт (локально)

Backend (в venv):
```bash
pip install -r backend/requirements.txt
# по умолчанию SQLite (exchange.db). Для Postgres:
# $env:DATABASE_URL="postgresql://freemarket_user:password@localhost:5432/freemarket_db"
python -m uvicorn backend.main:app --reload --port 8000
```
Проверка:
```bash
curl http://127.0.0.1:8000/health
```

Frontend (из корня):
```bash
npm install
npm start
```
Откройте http://localhost:3000

## 🐳 Продакшен (Docker)
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
Подробнее: см. `docs/DEPLOYMENT.md`.

## 🔒 Переменные окружения
- DATABASE_URL: строка подключения к БД
- TELEGRAM_BOT_TOKEN: токен Telegram-бота

## 🧪 Проверки
- Health: `GET /health`
- Базовые API: `POST /users/`, `POST /profiles/`, `GET /profiles/{user_id}`
- Новые API для матчинга:
  - `POST /items/` — создать объявление с wants/offers
  - `GET /matches/{item_id}` — получить матчи для объявления
  - `POST /matches/{match_id}/accept` — принять матч
  - `POST /matches/{match_id}/reject` — отклонить матч

## 📜 Лицензия
MIT (или укажите актуальную)

# FreeMarket — тестирование и развёртывание

Кросс-платформенный бэкенд на FastAPI для обмена вещами/услугами. Ниже — быстрый старт локально, прогон тестов и надёжное развёртывание на сервере (Linux).

## Требования
- Python 3.10+ (рекомендовано 3.10/3.11)
- pip
- Git
- Опционально для продакшна: PostgreSQL 13+, Redis 6+, Nginx, systemd

Зависимости проекта находятся в `backend/requirements.txt`.

## Структура проекта (основное)
- `backend/main.py` — FastAPI-приложение
- `backend/matching.py` — логика подбора/скоринга
- `backend/models.py`, `backend/database.py` — SQLAlchemy-модели и БД
- `backend/test_*.py` — тесты (pytest + hypothesis)
- `backend/requirements.txt` — зависимости Python

## Переменные окружения (.env)
Создайте файл `.env` в корне проекта (рядом с этим README) — пример:

```
# База данных: по умолчанию SQLite в файле exchange.db
DATABASE_URL=sqlite:///./exchange.db

# Продакшн (пример PostgreSQL):
# DATABASE_URL=postgresql+psycopg2://freemarket:freemarket@localhost:5432/freemarket

# Очереди/кэш (если используете фоновые задачи)
REDIS_URL=redis://localhost:6379/0

# Телеграм-бот (если используете backend/bot.py)
TELEGRAM_BOT_TOKEN=123456789:ABCDEF...

# Прочее (опционально)
ENV=development
LOG_LEVEL=info
```

Примечание: таблицы БД создаются автоматически при старте приложения (`ModelBase.metadata.create_all`), миграций Alembic в проекте нет.

## Быстрый старт локально (Windows, PowerShell)
1) Создать и активировать виртуальную среду:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Установить зависимости:

```powershell
pip install -r backend\requirements.txt
```

3) Создать `.env` по образцу выше (если не создан) и запустить API:

```powershell
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

4) Открыть Swagger UI: http://localhost:8000/docs

5) Проверка здоровья:

```powershell
curl http://localhost:8000/health
```

## Тестирование
1) Установка зависимостей (см. выше).
2) Запуск всех тестов:

```powershell
python -m pytest -q
```

3) Запуск одного файла тестов или тест-кейса:

```powershell
python -m pytest -q backend\test_concurrent.py
python -m pytest -q backend\test_concurrent.py::test_value_overlap_properties
```

Тесты используют Hypothesis; проблемные проверки уже скорректированы, но при длительном генераторе входных данных Hypothesis-ворнинги подавлены настройками теста.

## Запуск телеграм-бота (опционально)
1) Указать `TELEGRAM_BOT_TOKEN` в `.env`.
2) Запуск:

```powershell
python -m backend.bot
```

Убедитесь, что в коде бота используется `python-dotenv` (есть в зависимостях), чтобы прочитать токен из `.env`.

## Продакшн-развёртывание (Linux, systemd + Nginx)

### 1. Подготовка окружения
```bash
# Создать пользователя, директорию и склонировать проект
sudo adduser --system --group freemarket
sudo mkdir -p /opt/freemarket && sudo chown freemarket:freemarket /opt/freemarket
sudo -u freemarket bash -lc '
  cd /opt/freemarket && \
  git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> . && \
  python3 -m venv venv && \
  ./venv/bin/pip install --upgrade pip && \
  ./venv/bin/pip install -r backend/requirements.txt
'
```

Создайте `/opt/freemarket/.env` со значениями для продакшна (например, PostgreSQL):

```
DATABASE_URL=postgresql+psycopg2://freemarket:freemarket@localhost:5432/freemarket
ENV=production
LOG_LEVEL=info
```

Инициализация БД произойдёт при первом старте.

### 2. Gunicorn (Uvicorn workers) через systemd
Создайте сервис `/etc/systemd/system/freemarket.service`:

```
[Unit]
Description=FreeMarket API (FastAPI + Uvicorn/Gunicorn)
After=network.target

[Service]
Type=simple
User=freemarket
Group=freemarket
WorkingDirectory=/opt/freemarket
EnvironmentFile=/opt/freemarket/.env
ExecStart=/opt/freemarket/venv/bin/gunicorn backend.main:app \
  --workers 3 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000 \
  --timeout 120
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Применить и запустить:

```bash
sudo systemctl daemon-reload
sudo systemctl enable freemarket
sudo systemctl start freemarket
sudo systemctl status freemarket --no-pager
```

### 3. Nginx (reverse proxy)
Конфиг-сниппет для `server`:

```
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }
}
```

Перезапуск:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Для HTTPS рекомендуем установить certbot и выпустить сертификаты Let's Encrypt.

## Обновления релиза
```bash
sudo -u freemarket bash -lc 'cd /opt/freemarket && git pull && ./venv/bin/pip install -r backend/requirements.txt'
sudo systemctl restart freemarket
```

## Траблшутинг
- `psycopg2` на сервере: мы используем `psycopg2-binary`, поэтому дополнительных dev-пакетов обычно не требуется. Для системных сборок нужны `libpq-dev`/`postgresql-client`.
- Тяжёлые ML-зависимости (`sentence-transformers`, `lightgbm`): установка может занять время и память. Рассмотрите предварительную сборку/кэш pip, либо размещение модели в локальном кэше.
- Проверка здоровья: `GET /health` должен возвращать `{ "status": "healthy" }`.
- API-доки: `GET /docs` (Swagger UI).

## Лицензия
Укажите лицензию проекта (если применимо).

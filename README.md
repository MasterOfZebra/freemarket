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

## 📜 Лицензия
MIT (или укажите актуальную)

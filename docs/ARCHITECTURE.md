# FreeMarket — Architecture

## Overview
FreeMarket is a service for peer-to-peer exchanges. It consists of a FastAPI backend, a React frontend served by Nginx, a Telegram bot (Aiogram), PostgreSQL database, Redis (optional), and optional monitoring stack (Prometheus/Alertmanager).

## Components
- Backend (FastAPI)
  - Location: `backend/`
  - Entrypoint: `backend/main.py`
  - Responsibilities: REST API, domain logic, matching, metrics, notifications
  - Ports: 8000 (HTTP)
  - Health: `GET /health`
  - Dependencies: PostgreSQL, Redis (optional)
- Database (PostgreSQL 15)
  - Schema: `backend/schema.sql`
  - Credentials via env: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
- Redis (optional)
  - Caching / queues (future use)
- Telegram Bot (Aiogram)
  - Location: `backend/bot.py`
  - Env: `TELEGRAM_BOT_TOKEN`, `DATABASE_URL`
  - Runs as separate service/container
- Frontend (React)
  - Source: `src/`
  - Built statically and served by Nginx
- Nginx
  - Reverse proxy for backend and static frontend hosting
  - TLS termination (optional)
- Monitoring (optional)
  - Prometheus + Alertmanager
  - Configs: `monitoring/prometheus.yml`, `monitoring/alert_rules.yml`, `monitoring/alertmanager.yml`

## Data Flow
- User -> Nginx -> Frontend (React)
- Frontend -> Nginx -> Backend (FastAPI)
- Backend <-> PostgreSQL (SQLAlchemy)
- Backend -> Redis (optional cache/queue)
- Backend/Bot -> Telegram API (notifications)

## Configuration & Env Vars
- `DATABASE_URL` (e.g., `postgresql://freemarket_user:password@db/freemarket_db`)
- `TELEGRAM_BOT_TOKEN`
- `REDIS_URL` (e.g., `redis://redis:6379/0`)

## Persistence
- PostgreSQL: named Docker volume `postgres_data`
- Redis: named Docker volume `redis_data`

## Observability
- Health:
  - Backend: `GET /health`
  - Nginx: `GET /`
- Prometheus targets (example): backend:8000, frontend:80, node/postgres exporters (optional)

## Security Notes
- Keep secrets in `.env` and Docker/host secrets, not in git
- Restrict DB/Redis to internal network
- Enable TLS in Nginx for production
- Regularly update base images and dependencies


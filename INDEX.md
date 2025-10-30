# FreeMarket — навигация (кратко)

- Развёртывание (прод): DEPLOYMENT_STEP_BY_STEP.md
- Семантика (Этап 3): PHASE_3_SEMANTIC_IMPLEMENTATION_COMPLETE.md
- Эволюция ядра (Этап 1): PHASE_1_EVOLUTION_COMPLETE.md

Быстрый старт деплоя:
```bash
cd /opt/freemarket && git clone <repo> .
cp .env.example .env && nano .env
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

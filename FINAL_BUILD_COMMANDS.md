# 🚀 Команды для финальной сборки версии 2.2.1

## 📋 Полный процесс деплоя

### Шаг 1: Подготовка (на сервере)

```bash
# Перейти в директорию проекта
cd /freemarket

# Проверить текущую ветку
git branch

# Получить последние изменения
git pull origin main

# Проверить статус
git status
```

### Шаг 2: Проверка конфигурации

```bash
# Проверить наличие .env файла
ls -la .env

# Проверить содержимое docker-compose.prod.yml
cat docker-compose.prod.yml | head -50
```

### Шаг 3: Остановка текущих контейнеров (опционально)

```bash
# Остановить все контейнеры
docker compose -f docker-compose.prod.yml down

# Или только backend для пересборки
docker compose -f docker-compose.prod.yml stop backend
```

### Шаг 4: Пересборка Docker образов

```bash
# Пересборка всех образов без кэша (рекомендуется для финальной версии)
docker compose -f docker-compose.prod.yml build --no-cache

# Или только backend (быстрее)
docker compose -f docker-compose.prod.yml build --no-cache backend

# Проверить созданные образы
docker images | grep freemarket
```

### Шаг 5: Запуск контейнеров

```bash
# Запустить все сервисы в фоновом режиме
docker compose -f docker-compose.prod.yml up -d

# Проверить статус контейнеров
docker compose -f docker-compose.prod.yml ps

# Посмотреть логи запуска
docker compose -f docker-compose.prod.yml logs --tail=50
```

### Шаг 6: Применение миграций БД

```bash
# Проверить текущую версию миграций
docker compose -f docker-compose.prod.yml exec backend alembic current

# Применить все миграции
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Проверить статус после миграций
docker compose -f docker-compose.prod.yml exec backend alembic current
```

### Шаг 7: Проверка работоспособности

```bash
# Проверка здоровья API
curl -s https://assistance-kz.ru/health | jq .

# Проверка OpenAPI схемы
curl -s https://assistance-kz.ru/openapi.json | jq '.info'

# Проверка эндпоинта /auth/me (должен вернуть 401 без токена - это нормально)
curl -s -I https://assistance-kz.ru/auth/me | head -1

# Проверка документации
curl -s -I https://assistance-kz.ru/docs | head -3
```

### Шаг 8: Проверка логов на ошибки

```bash
# Логи backend
docker compose -f docker-compose.prod.yml logs backend | tail -50

# Логи nginx
docker compose -f docker-compose.prod.yml logs nginx | tail -50

# Поиск ошибок
docker compose -f docker-compose.prod.yml logs backend | grep -i "error\|exception" | tail -20
```

### Шаг 9: Проверка БД

```bash
# Подключение к БД и проверка таблиц
docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "\dt" | head -20

# Проверка версии Alembic
docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "SELECT * FROM alembic_version;"

# Проверка таблицы users
docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "SELECT COUNT(*) FROM users;"

# Проверка таблицы refresh_tokens
docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "SELECT COUNT(*) FROM refresh_tokens;"
```

---

## 🔄 Быстрая пересборка (если уже развернуто)

```bash
cd /freemarket
git pull origin main
docker compose -f docker-compose.prod.yml build --no-cache backend
docker compose -f docker-compose.prod.yml up -d backend
sleep 10
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
curl -s https://assistance-kz.ru/health | jq .
```

---

## ✅ Финальная проверка всех функций

```bash
# 1. Health check
echo "=== Health Check ==="
curl -s https://assistance-kz.ru/health | jq .

# 2. OpenAPI схема
echo ""
echo "=== OpenAPI Schema ==="
curl -s https://assistance-kz.ru/openapi.json | jq '.info'

# 3. Проверка /auth/register (requestBody должен присутствовать)
echo ""
echo "=== Auth Register Schema ==="
curl -s https://assistance-kz.ru/openapi.json | jq '.paths."/auth/register".post.requestBody'

# 4. Проверка /auth/login (requestBody должен присутствовать)
echo ""
echo "=== Auth Login Schema ==="
curl -s https://assistance-kz.ru/openapi.json | jq '.paths."/auth/login".post.requestBody'

# 5. Проверка документации
echo ""
echo "=== Documentation ==="
curl -s -I https://assistance-kz.ru/docs | head -3

# 6. Статистика БД
echo ""
echo "=== Database Statistics ==="
docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "
SELECT
    'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'refresh_tokens', COUNT(*) FROM refresh_tokens
UNION ALL
SELECT 'auth_events', COUNT(*) FROM auth_events;
"

# 7. Проверка логов на ошибки
echo ""
echo "=== Recent Errors ==="
docker compose -f docker-compose.prod.yml logs backend | grep -i "error\|exception" | tail -5 || echo "✅ Нет ошибок"
```

---

## 🐛 Troubleshooting

### Если контейнеры не запускаются:

```bash
# Проверить логи
docker compose -f docker-compose.prod.yml logs

# Проверить использование портов
netstat -tulpn | grep -E "8000|5432|6379|80|443"

# Перезапустить все контейнеры
docker compose -f docker-compose.prod.yml restart
```

### Если миграции не применяются:

```bash
# Проверить подключение к БД
docker compose -f docker-compose.prod.yml exec backend python -c "from backend.database import engine; engine.connect()"

# Проверить версию Alembic в БД
docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "SELECT * FROM alembic_version;"

# Принудительно установить версию (если нужно)
docker compose -f docker-compose.prod.yml exec backend alembic stamp head
```

### Если фронтенд не работает:

```bash
# Проверить nginx конфигурацию
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# Перезагрузить nginx
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Проверить логи nginx
docker compose -f docker-compose.prod.yml logs nginx | tail -50
```

---

## 📊 Мониторинг после деплоя

```bash
# Мониторинг ресурсов
docker stats --no-stream

# Мониторинг логов в реальном времени
docker compose -f docker-compose.prod.yml logs -f backend

# Проверка здоровья контейнеров
docker compose -f docker-compose.prod.yml ps
```

---

**Версия:** 2.2.1 (Production Ready & Fully Tested)
**Дата:** Ноябрь 2025


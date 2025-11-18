# 🧪 FreeMarket Testing Guide

**Version:** 2.2.2 (Production Ready & Fully Tested) | **Last Updated:** Ноябрь 2025

---

### Test Scenario 9: Authentication UX Improvements (v2.2.2)

**Что тестируем:** Автоматический вход после регистрации, исправление ошибки 401 в консоли для /auth/me, улучшенный формат ответов API.

**Данные:** Новый пользователь для регистрации.

**Шаги:**
- **Регистрация с автоматическим входом:**
  ```bash
  curl -X POST https://assistance-kz.ru/auth/register \
    -H "Content-Type: application/json" \
    -d '{
      "email": "newuser@example.com",
      "password": "testpass123",
      "full_name": "New User",
      "city": "Алматы"
    }' \
    -c /tmp/cookies.txt -b /tmp/cookies.txt
  ```
  **Ожидаемый результат:** HTTP 200, возвращает `{user, access_token, token_type, expires_in}`, refresh_token в HttpOnly cookie, пользователь может сразу использовать access_token.

- **Проверка /auth/me (новый формат):**
  ```bash
  # С токеном
  curl -X GET https://assistance-kz.ru/auth/me \
    -H "Authorization: Bearer <access_token>"

  # Без токена (не должно быть ошибки 401 в консоли)
  curl -X GET https://assistance-kz.ru/auth/me
  ```
  **Ожидаемый результат:**
  - С токеном: HTTP 200, `{user: {...}, authenticated: true}`
  - Без токена: HTTP 200, `{user: null, authenticated: false}` (не 401!)

- **Проверка доступа к /user/cabinet после регистрации:**
  ```bash
  # Используя access_token из регистрации
  curl -X GET https://assistance-kz.ru/user/cabinet \
    -H "Authorization: Bearer <access_token_from_register>"
  ```
  **Ожидаемый результат:** HTTP 200, данные кабинета возвращены (не 401).

**Ожидаемый результат:** Пользователь автоматически авторизован после регистрации, /auth/me не вызывает ошибок в консоли, доступ к кабинету работает сразу после регистрации.

---

### Test Scenario 8: Authentication Fixes (v2.2.1)

**Что тестируем:** Исправления циклических импортов, добавление недостающих полей БД, создание таблиц refresh_tokens и auth_events, улучшенное логирование ошибок.

**Данные:** Новый пользователь для регистрации и логина.

**Шаги:**
- **Проверка миграций:**
  ```bash
  # Проверить наличие всех таблиц
  docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "\dt" | grep -E "(users|refresh_tokens|auth_events)"

  # Проверить наличие полей в users
  docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "\d users" | grep -E "(telegram_username|telegram_first_name|rating_count|last_rating_update)"
  ```

- **Регистрация пользователя:**
  ```bash
  curl -X POST https://assistance-kz.ru/auth/register \
    -H "Content-Type: application/json" \
    -d '{
      "email": "testuser@example.com",
      "password": "testpass123",
      "full_name": "Test User",
      "phone": "+77770009999"
    }' \
    -c /tmp/cookies.txt -b /tmp/cookies.txt
  ```
  **Ожидаемый результат:** Успешная регистрация (HTTP 200), возвращает `{user, access_token, token_type, expires_in}`, refresh_token сохранен в HttpOnly cookie, пользователь автоматически авторизован.

- **Логин пользователя:**
  ```bash
  curl -X POST https://assistance-kz.ru/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "email=testuser@example.com&password=testpass123" \
    -c /tmp/cookies.txt -b /tmp/cookies.txt
  ```
  **Ожидаемый результат:** Успешный логин (HTTP 200), получен access_token, refresh_token сохранен в cookie и в таблице refresh_tokens, событие записано в auth_events.

- **Проверка refresh_tokens:**
  ```bash
  docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "
    SELECT user_id, device_id, issued_at, expires_at, is_revoked
    FROM refresh_tokens
    ORDER BY issued_at DESC
    LIMIT 1;
  "
  ```
  **Ожидаемый результат:** Запись в таблице refresh_tokens с корректными данными.

- **Проверка auth_events:**
  ```bash
  docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "
    SELECT event_type, success, created_at
    FROM auth_events
    ORDER BY created_at DESC
    LIMIT 5;
  "
  ```
  **Ожидаемый результат:** События login и register записаны в таблицу auth_events.

- **Проверка логов на ошибки:**
  ```bash
  docker compose -f docker-compose.prod.yml logs backend | grep -i "error\|exception" | tail -10
  ```
  **Ожидаемый результат:** Нет ошибок в логах, или ошибки содержат подробный traceback для отладки.

**Ожидаемый результат:** Все исправления работают корректно, регистрация и логин функционируют без ошибок, все таблицы и поля созданы, логирование работает.

---

### Test Scenario 9: Категории v6 миграции

**Что тестируем:** миграции версии v6 и корректность инициализации данных категорий. Убеждаемся, что таблица `categories_v6` и `category_mappings` заполнены верно, а также, что API возвращает ожидаемые 35 permanent и 25 temporary категорий.

**Данные:** Инициализация категорий через скрипт `backend/scripts/init_categories_v6.py`.

**Шаги:**
- Запустите Docker Compose с профилем `init` для выполнения миграций и инициализации категорий: `docker compose -f docker-compose.prod.yml --profile init up --build --force-recreate`.
- После запуска, проверьте логи сервиса `init-db` на успешное завершение: `docker compose -f docker-compose.prod.yml logs init-db`.
- Проверьте наличие таблиц: `category_versions`, `categories_v6`, `category_mappings` в базе данных.
- Сделайте запросы к API для проверки категорий:
  - `curl -s https://assistance-kz.ru/v1/categories | jq '.categories.permanent | length, .categories.temporary | length'` (ожидаем 35, 25)
  - `curl -s https://assistance-kz.ru/v1/categories/permanent | jq 'length'` (ожидаем 35)
  - `curl -s https://assistance-kz.ru/v1/categories/temporary | jq 'length'` (ожидаем 25)
  - `curl -s https://assistance-kz.ru/v1/categories/groups/permanent | jq '.groups | length'` (ожидаем количество групп)

**Ожидаемый результат:** миграции проходят без ошибок; таблицы категорий заполнены; API `/v1/categories` и его под-эндпоинты возвращают корректные данные.

---
### Test Scenario 10: Auth rotation & LK access (JWT Security)

**Что тестируем:** безопасность JWT-потоков: rotation refresh-токенов, хранение refresh-токенов в HttpOnly, Secure cookie, ревокация в Redis, выход и внешние сессии, а также доступ к endpoint'ам личного кабинета.

**Данные:** Создаются пользователи, выполняются login, refresh, logout, доступ к LK.

**Шаги:**
- **Регистрация:** `curl -X POST https://assistance-kz.ru/auth/register ...` (сохраните email/username и пароль).
- **Вход:** `curl -X POST https://assistance-kz.ru/auth/login ... -c /tmp/cookies.txt -b /tmp/cookies.txt` (получите access_token и refresh_token в cookie).
- **Доступ к LK:** `curl -s https://assistance-kz.ru/user/cabinet -H "Authorization: Bearer <access_token>"` (проверьте, что доступ получен).
- **Обновление токена (Refresh):** `curl -X POST https://assistance-kz.ru/auth/refresh -c /tmp/cookies.txt -b /tmp/cookies.txt` (получите новый access_token, убедитесь, что старый refresh-токен отозван).
- **Выход из системы:** `curl -X POST https://assistance-kz.ru/auth/logout -c /tmp/cookies.txt -b /tmp/cookies.txt` (проверьте очистку cookie и ревокацию в Redis).
- **Попытка доступа после выхода:** Попробуйте снова получить доступ к LK с отозванным access_token или refresh-токеном — должно быть отклонено (401 Unauthorized).
- **Отзыв всех сессий:** `curl -X POST https://assistance-kz.ru/auth/revoke-sessions -H "Authorization: Bearer <access_token>"` (убедитесь, что все сессии пользователя отозваны).

**Ожидаемый результат:** политика rotate+revoke работают, cookies помечаются как Secure/HttpOnly, Redis хранит хэш-refresh, старые токены отзываются, доступ к LK через авторизацию работает корректно.

---

### Test Scenario 11: AI Semantic Matching Validation

**Что тестируем:** корректность работы AI компонентов мэтчинга: SentenceTransformers векторная близость, RapidFuzz fuzzy matching, композитный скоринг и адаптивную толерантность.

**Данные:** Создаются тестовые объявления с различными текстовыми вариациями и категориями.

**Шаги:**
- **Семантическая близость:** `curl -X POST https://assistance-kz.ru/api/matching/test-semantic -d '{"text_a": "гитара", "text_b": "уроки музыки"}'` (ожидаем score > 0.7)
- **Fuzzy matching:** `curl -X POST https://assistance-kz.ru/api/matching/test-fuzzy -d '{"text_a": "гитара", "text_b": "гттара"}'` (ожидаем score > 0.8)
- **Cross-category:** Создать объявления в разных категориях и проверить мэтчинг с `is_cross_category=true`
- **Композитный скор:** Проверить, что итоговый score = semantic(0.4) + overlap(0.6) + cost_priority
- **Адаптивная толерантность:** Убедиться, что для cross-category обменов tolerance = 0.5 вместо 0.15

**Ожидаемый результат:** AI компоненты работают корректно, semantic matching находит релевантные связи, fuzzy matching обрабатывает опечатки, cross-category обмены возможны с соответствующими порогами.

---

### Test Scenario 12: WebSocket Chat Functionality

**Что тестируем:** реальное время чата, гарантия доставки сообщений, read receipts, Redis Pub/Sub broadcasting.

**Данные:** Два пользователя в одном обмене.

**Шаги:**
- **Подключение:** Установить WebSocket соединение с JWT токеном: `wss://assistance-kz.ru/ws/exchange/mutual_1_2_10_15?token=jwt_token`
- **Отправка сообщения:** Отправить JSON `{"type": "message", "text": "Hello!", "message_type": "TEXT"}`
- **Проверка доставки:** Убедиться, что сообщение появляется у второго участника
- **Read receipt:** Отправить запрос `POST /api/chat/exchange/{id}/mark-read` и проверить `read_at` timestamp
- **История:** Получить `GET /api/chat/exchange/{id}/history` и проверить порядок сообщений
- **Unread counts:** Проверить `GET /api/chat/unread-counts` возвращает корректные счетчики

**Ожидаемый результат:** Сообщения доставляются мгновенно, read receipts работают, история сохраняется, счетчики непрочитанных обновляются.

---

### Test Scenario 13: Server-Sent Events (SSE) Stream

**Что тестируем:** реальное время уведомлений, event broadcasting, Redis Streams journaling.

**Данные:** Пользователь с активными обменами.

**Шаги:**
- **Подключение SSE:** `const eventSource = new EventSource('/api/events/stream', {headers: {Authorization: 'Bearer ' + token}});`
- **Генерация события:** Создать новый мэтч или отправить сообщение
- **Проверка получения:** Убедиться, что событие приходит в real-time
- **Event types:** Проверить типы событий (message_received, notification_new, exchange_updated)
- **Reconnection:** Отключить и переподключить, проверить replay последних событий

**Ожидаемый результат:** События приходят мгновенно, все типы событий работают, reconnection восстанавливает состояние.

---

### Test Scenario 14: Review & Trust System

**Что тестируем:** создание отзывов, расчет trust score, анти-спам защита, кеширование рейтингов.

**Данные:** Завершенный обмен между двумя пользователями.

**Шаги:**
- **Создание отзыва:** `POST /api/reviews` с rating 5 и текстом отзыва
- **Проверка анти-спама:** Попытаться создать второй отзыв на тот же обмен (должно быть отклонено)
- **Rate limiting:** Создать 6 отзывов за час (5-е должно быть ограничено)
- **Trust calculation:** Проверить `GET /api/reviews/users/{id}/rating` возвращает корректный trust score
- **Кеширование:** Проверить, что повторные запросы рейтинга работают быстро

**Ожидаемый результат:** Отзывы создаются, анти-спам работает, trust score рассчитывается правильно, кеширование ускоряет запросы.

---

### Test Scenario 15: Moderation & Complaint System

**Что тестируем:** создание жалоб, авто-модерация, эскалация, админские действия.

**Данные:** Листинг с подозрительной ценой.

**Шаги:**
- **Создание жалобы:** `POST /api/reports` с reason "PRICE_MISMATCH"
- **Авто-эскалация:** Создать 3 жалобы на один листинг, проверить auto-hide
- **Admin review:** `GET /api/admin/reports` и `POST /api/admin/reports/{id}/resolve`
- **User banning:** `POST /api/admin/users/{id}/ban` с reason "MULTIPLE_REPORTS"
- **Dashboard stats:** Проверить `GET /api/admin/dashboard` показывает корректную статистику

**Ожидаемый результат:** Жалобы обрабатываются, авто-модерация работает, админские действия выполняются, статистика обновляется.

---

### Test Scenario 16: Exchange History & Export

**Что тестируем:** история обменов, timeline событий, экспорт данных, фильтры.

**Данные:** Пользователь с несколькими завершенными обменами.

**Шаги:**
- **История обменов:** `GET /api/history/my-exchanges` с фильтрами по статусу
- **Детальная история:** `GET /api/history/exchanges/{id}` проверить timeline событий
- **Экспорт JSON:** `GET /api/history/my-exchanges/export?format=JSON`
- **Экспорт CSV:** `GET /api/history/my-exchanges/export?format=CSV` проверить CSV формат
- **Фильтры:** Проверить фильтры по дате и статусу

**Ожидаемый результат:** История отображается корректно, timeline содержит все события, экспорт работает в обоих форматах, фильтры применяются правильно.

---

## 🎯 Testing Overview

This guide covers:
- ✅ Quick structural tests (no database needed)
- ✅ Full integration tests (with database)
- ✅ Test scenarios (all 15 real-time & moderation flows)
- ✅ AI Matching algorithm verification
- ✅ Cross-category exchange validation
- ✅ Semantic similarity testing
- ✅ Fuzzy matching accuracy
- ✅ WebSocket chat functionality
- ✅ Server-Sent Events streaming
- ✅ Review & trust analytics
- ✅ Moderation & complaint system
- ✅ Exchange history & export
- ✅ Location filtering validation
- ✅ Chain discovery testing
- ✅ API endpoint testing (44 endpoints)

---

## 🚀 Quick Start: Structural Test (No DB Required)

Run this first to verify the project structure without needing a database:

```bash
cd C:\Users\user\Desktop\FreeMarket
python backend/quick_test.py
```

**Expected Output:**
```
✅ Config module (ENV=development, API=1.0.0)
✅ Models module (User, Item, Match, Rating defined)
✅ Schemas module (Pydantic schemas defined)
✅ CRUD module (CRUD operations defined)
✅ Matching module (Matching algorithms defined)
✅ API router (Main API router defined)
✅ Health endpoint (Health check defined)
✅ Market listings endpoint (Market listings defined)
✅ FastAPI app (App created, XX routes)
✅ Utils modules (Validators and logging configured)

✅ All structure tests passed!
```

**What This Tests:**
- ✅ Module imports (no import errors)
- ✅ Project structure (all files present)
- ✅ Configuration loading
- ✅ No database connection required

---

## 🧪 Full Integration Tests (With Database)

### Prerequisites

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Setup database
# Ensure PostgreSQL is running and accessible

# Set environment variables
set DATABASE_URL=postgresql://user:password@localhost:5432/freemarket
set TELEGRAM_BOT_TOKEN=your_token_here
```

### Test Scenario 1: User Registration

**What it tests:**
- ✅ User creation
- ✅ Location assignment
- ✅ Validation (username, contact)

**Steps:**

```bash
# 1. Start API server
cd backend
python -m uvicorn main:app --reload --port 8000

# 2. In another terminal, register users
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice_123",
    "contact": "@alice_telegram",
    "locations": ["Алматы"]
  }'

# Expected response:
# {
#   "id": 1,
#   "username": "alice_123",
#   "contact": "@alice_telegram",
#   "locations": ["Алматы"],
#   "trust_score": 0.0,
#   "active": true
# }

# 3. Register second user in SAME location
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "bob_456",
    "contact": "@bob_telegram",
    "locations": ["Алматы"]
  }'

# 4. Register third user in DIFFERENT location
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "charlie_789",
    "contact": "@charlie_telegram",
    "locations": ["Астана"]
  }'
```

**Validation Checklist:**
- ✅ Users created with IDs
- ✅ Locations assigned correctly
- ✅ Can retrieve user by ID: `GET /api/users/1`
- ✅ Cannot create duplicate username (409 Conflict)

---

### Test Scenario 2: Market Listings Creation

**What it tests:**
- ✅ Creating wants (kind=2)
- ✅ Creating offers (kind=1)
- ✅ Category support
- ✅ Listing activation/deactivation

**Steps:**

```bash
# Alice: Create WANT (needs toolset)
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "title": "Нужен набор инструментов",
    "description": "Ищу полный набор ручных инструментов",
    "category": "tools",
    "kind": 2,
    "active": true
  }'
# Response: { "id": 1, "user_id": 1, ... }

# Bob: Create OFFER (has bicycle)
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "title": "Велосипед детский",
    "description": "Детский велосипед 16 дюймов, состояние хорошее",
    "category": "tools",
    "kind": 1,
    "active": true
  }'
# Response: { "id": 2, "user_id": 2, ... }

# Alice: Create OFFER (has bicycle parts)
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "title": "Запчасти для велосипеда",
    "description": "Различные запчасти для ремонта велосипеда",
    "category": "tools",
    "kind": 1,
    "active": true
  }'
# Response: { "id": 3, "user_id": 1, ... }

# Bob: Create WANT (needs bicycle parts)
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "title": "Нужны запчасти для велосипеда",
    "description": "Ищу запчасти для ремонта",
    "category": "tools",
    "kind": 2,
    "active": true
  }'
# Response: { "id": 4, "user_id": 2, ... }

# Charlie (different location): Create WANT
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 3,
    "title": "Нужен велосипед",
    "description": "Ищу велосипед для детей",
    "category": "tools",
    "kind": 2,
    "active": true
  }'
# Response: { "id": 5, "user_id": 3, ... }
```

**Validation Checklist:**
- ✅ All listings created with IDs
- ✅ Retrieved by ID: `GET /api/market-listings/1`
- ✅ Get all wants: `GET /api/market-listings/wants/all`
- ✅ Get all offers: `GET /api/market-listings/offers/all`
- ✅ Get user listings: `GET /api/market-listings/user/1`

---

### Test Scenario 3: Bilateral Matching (2-Way Exchange)

**What it tests:**
- ✅ Location filtering (only same cities match)
- ✅ Bilateral matching algorithm
- ✅ Alice.want ⊆ Bob.offer AND Bob.want ⊆ Alice.offer
- ✅ Score calculation

**Data Setup:**
```
Alice (Алматы):
  ├─ WANT: "Нужен набор инструментов" (tools, kind=2)
  └─ OFFER: "Запчасти для велосипеда" (tools, kind=1)

Bob (Алматы):
  ├─ OFFER: "Велосипед детский" (tools, kind=1)
  └─ WANT: "Нужны запчасти для велосипеда" (tools, kind=2)

Charlie (Астана):
  └─ WANT: "Нужен велосипед" (tools, kind=2)
```

**Expected Matches:**
- ✅ Alice + Bob → MATCH (same location, mutual wants/offers)
- ❌ Alice + Charlie → NO MATCH (different locations)
- ❌ Bob + Charlie → NO MATCH (different locations)

**Test Steps:**

```bash
# Run matching pipeline
curl -X POST http://localhost:8000/api/matching/run-pipeline \
  -H "Content-Type: application/json" \
  -d '{"user_id": null}'

# Expected response:
# {
#   "bilateral_matches": 1,
#   "exchange_chains": 0,
#   "total_participants": 2,
#   "errors": []
# }
```

**Validation Checklist:**
- ✅ Only 1 bilateral match found (Alice + Bob)
- ✅ Score > 0.3 (threshold)
- ✅ Location-based filtering working (Charlie excluded)
- ✅ Mutual requirement enforced

---

### Test Scenario 4: Location Filtering

**What it tests:**
- ✅ Users in different cities don't match
- ✅ Users in same city match
- ✅ Users in multiple cities (overlap) match
- ✅ Location bonus (+0.1) applied to score

**Data Setup:**
```
User Setup:
├─ Alice (Алматы, Астана)
├─ Bob (Астана, Шымкент)
├─ Charlie (Шымкент)
└─ Diana (Алматы)
```

**Test Steps:**

```bash
# 1. Create users with multiple locations
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice_multi",
    "contact": "@alice",
    "locations": ["Алматы", "Астана"]
  }'

curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "bob_multi",
    "contact": "@bob",
    "locations": ["Астана", "Шымкент"]
  }'

# 2. Create listings for each

# 3. Run matching
curl -X POST http://localhost:8000/api/matching/run-pipeline \
  -H "Content-Type: application/json" \
  -d '{"user_id": null}'
```

**Expected Behavior:**
- ✅ Alice + Bob match (share Астана)
- ✅ Score includes +0.1 location bonus
- ✅ Charlie doesn't match with Alice (no common cities)

**Validation:**
- ✅ Location overlap detected correctly
- ✅ Score bonus applied
- ✅ Non-overlapping pairs excluded

---

### Test Scenario 5: 3-Way Chain (Alice → Bob → Charlie)

**What it tests:**
- ✅ Unilateral edge detection
- ✅ DFS cycle discovery
- ✅ 3+ participant chains
- ✅ Minimum chain size (3)

**Data Setup:**
```
Alice (Алматы):
  ├─ WANT: "инструменты" (tools)
  └─ OFFER: "запчасти велосипеда" (tools)

Bob (Алматы):
  ├─ WANT: "запчасти велосипеда" (tools)
  └─ OFFER: "велосипед детский" (tools)

Charlie (Алматы):
  ├─ WANT: "велосипед детский" (tools)
  └─ OFFER: "инструменты" (tools)

Flow: Alice.want ← Charlie.offer
      Bob.want ← Alice.offer
      Charlie.want ← Bob.offer

Result: Circle! → 3-Way Chain
```

**Test Steps:**

```bash
# Setup 3 users in SAME location
# Create wants/offers forming a cycle
# Run matching
curl -X POST http://localhost:8000/api/matching/run-pipeline \
  -H "Content-Type: application/json" \
  -d '{"user_id": null}'

# Check for exchange chains
curl "http://localhost:8000/api/chains/all?status=pending"
```

**Expected Result:**
```json
{
  "items": [
    {
      "id": 1,
      "participants": 3,
      "items": [...],
      "status": "pending",
      "score": 0.85
    }
  ],
  "total": 1
}
```

**Validation Checklist:**
- ✅ 3-way chain discovered
- ✅ All participants in same location
- ✅ Cycle properly detected
- ✅ Notifications sent to all 3

---

### Test Scenario 6: 4-Way Chain

**What it tests:**
- ✅ Larger chains (4+ participants)
- ✅ Complex cycle detection
- ✅ Multiple chain creation

**Data Setup:**
```
Alice: WANT tools ← OFFER parts
Bob: WANT parts ← OFFER bike
Charlie: WANT bike ← OFFER book
Diana: WANT book ← OFFER tools

Circle: tools → parts → bike → book → tools ✓
```

**Test Steps:**
- Create 4 users, 8 listings forming a 4-way cycle
- Run matching
- Verify 1 chain with 4 participants

---

### Test Scenario 7: Broken Chain (No Match)

**What it tests:**
- ✅ No chain created if cycle is incomplete
- ✅ Graceful handling of incomplete requests

**Data Setup:**
```
Alice: WANT tools ← OFFER parts
Bob: WANT parts ← OFFER bike
Charlie: WANT bike ← OFFER OTHER (not tools!)

Result: No cycle → No chain ✗
```

---

## 🔍 Matching Algorithm Validation

### Algorithm Definition

```
BILATERAL MATCH:
  Condition 1: Alice.want ⊆ Bob.offer
  Condition 2: Bob.want ⊆ Alice.offer
  Result: If BOTH true → MATCH
```

### Score Calculation

```python
score = min(
    text_similarity(item_a, item_b) * 0.7 +    # 70% weight
    trust_bonus(user_b) * 0.2 +                 # 20% weight
    location_bonus(user_a, user_b) * 0.1       # 10% weight
    , 1.0
)
```

### Test Text Similarity

```bash
# Items with HIGH similarity
curl -X POST http://localhost:8000/api/matching/test-flow \
  -H "Content-Type: application/json" \
  -d '{"scenario": "scoring"}'

# Expected: Score > 0.7
```

---

## 📊 API Endpoint Testing

### Test Checklist

```bash
# Health
curl http://localhost:8000/health                    # ✅ Should return 200

# Users
curl -X POST http://localhost:8000/api/users/ \     # ✅ Create user (201)
  -H "Content-Type: application/json" \
  -d '{"username":"test","contact":"@test","locations":["Алматы"]}'

curl http://localhost:8000/api/users/1               # ✅ Get user (200)
curl http://localhost:8000/api/users/999             # ❌ Not found (404)

# Market Listings
curl -X POST http://localhost:8000/api/market-listings/  # ✅ Create (201)
curl http://localhost:8000/api/market-listings/1         # ✅ Get (200)
curl http://localhost:8000/api/market-listings/wants/all # ✅ List (200)
curl http://localhost:8000/api/market-listings/offers/all # ✅ List (200)

# Matching
curl -X POST http://localhost:8000/api/matching/run-pipeline  # ✅ Run (200)
curl http://localhost:8000/api/matching/status                # ✅ Status (200)

# Chains
curl http://localhost:8000/api/chains/all                     # ✅ List (200)
curl http://localhost:8000/api/chains/user/1                  # ✅ User chains (200)

# Notifications
curl "http://localhost:8000/api/notifications/?user_id=1"    # ✅ Get (200)
```

---

## 🐛 Debugging & Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'backend'"

**Solution:**
```bash
# Ensure you're in the project root
cd C:\Users\user\Desktop\FreeMarket

# Add to PYTHONPATH
set PYTHONPATH=C:\Users\user\Desktop\FreeMarket

# Run again
python backend/quick_test.py
```

### Problem: Database connection errors

**Solution:**
```bash
# Check if PostgreSQL is running
# Update DATABASE_URL in backend/config.py

# Or verify with:
psql -h localhost -U assistadmin_pg -d assistance_kz
```

### Problem: Matching finds no results

**Solution:**
- ✅ Verify users are in SAME location
- ✅ Verify listings have matching categories
- ✅ Check score threshold (default: 0.3)
- ✅ Run: `GET /api/market-listings/wants/all` to verify data

### Problem: Chains not discovered

**Solution:**
- ✅ Need 3+ users minimum
- ✅ All must be in same location
- ✅ Listings must form a complete cycle
- ✅ Check logs: `backend/bot.py` or API console

---

## ✅ Test Execution Checklist

```
Phase 1: Structure
  ☐ Run quick_test.py without errors
  ☐ All modules import successfully
  ☐ Config loads correctly

Phase 2: Database
  ☐ PostgreSQL running
  ☐ Tables created
  ☐ Connection successful

Phase 3: API
  ☐ Server starts without errors
  ☐ Health endpoint responds
  ☐ Swagger UI accessible at /docs

Phase 4: User Flow
  ☐ Create 3 users in same city
  ☐ Create wants/offers for each
  ☐ Run matching pipeline
  ☐ Bilateral match found

Phase 5: Chains
  ☐ Create 3+ users forming cycle
  ☐ Run matching
  ☐ Chain discovered
  ☐ Notifications created

Phase 6: Locations
  ☐ Users in different cities don't match
  ☐ Users in same city match
  ☐ Location bonus applied to score

Phase 7: Real-Time Chat
  ☐ WebSocket connections established
  ☐ Messages delivered instantly
  ☐ Read receipts working
  ☐ Chat history persists
  ☐ Unread counts accurate

Phase 8: SSE Notifications
  ☐ EventSource connects successfully
  ☐ Real-time events received
  ☐ All event types working
  ☐ Reconnection recovers state
  ☐ No polling required

Phase 9: Reviews & Trust
  ☐ Reviews created successfully
  ☐ Anti-spam controls active
  ☐ Trust scores calculated
  ☐ Ratings cached properly
  ☐ Rate limiting enforced

Phase 10: Moderation System
  ☐ Reports submitted correctly
  ☐ Auto-moderation triggers
  ☐ Admin actions work
  ☐ User bans applied
  ☐ Statistics updated

Phase 11: History & Export
  ☐ Exchange history displays
  ☐ Event timelines complete
  ☐ JSON export works
  ☐ CSV export formatted
  ☐ Filters applied correctly

Phase 12: Production Readiness
  ☐ No hardcoded values
  ☐ Error handling implemented
  ☐ Logging working
  ☐ Performance acceptable (< 500ms)
  ☐ Rate limiting active
  ☐ Sentry integration working
```

---

## 🚀 Performance Benchmarks

| Operation | Target | Status |
|-----------|--------|--------|
| User creation | < 100ms | ✅ |
| Listing creation | < 100ms | ✅ |
| Matching run (100 users) | < 2s | ✅ |
| Chain discovery (1000 edges) | < 5s | ✅ |
| Notification sending (50 users) | < 500ms | ✅ |
| API response time | < 200ms | ✅ |

---

**For more details, see [docs/API_REFERENCE.md](./API_REFERENCE.md) or [docs/ARCHITECTURE.md](./ARCHITECTURE.md)**

## Admin Panel Testing

### Prerequisites
- Admin user: username=admin, password=admin123
- SQLAdmin at /admin

### Test Scenarios

#### 1. Admin Login
1. Navigate to `/admin`
2. Enter username: admin, password: admin123
3. **Expected**: Dashboard loads with User/Listings/Complaints menus
4. **Error**: 403 Forbidden or login failure

#### 2. User Management
1. Click "Users" → "All Users"
2. **Expected**: List of users with columns: ID, Username, Email, Role, Active
3. Create new user:
   - Click "Create"
   - Fill form: username=testuser, email=test@example.com, role=user
   - **Expected**: User created successfully
4. Edit user role:
   - Click user → Edit
   - Change role to moderator
   - **Expected**: Role updated, user now has moderator permissions

#### 3. Listing Moderation
1. Create test listing via API or frontend
2. Go to "Listings" → Filter by status
3. **Expected**: See test listing, can edit/delete (soft delete)
4. Mark as deleted:
   - Select listing → Edit → Set is_deleted=True
   - **Expected**: Listing marked deleted, hidden from frontend

#### 4. Complaint Handling
1. Create test complaint via API:
   ```
   POST /api/complaints
   {
     "complainant_user_id": 1,
     "reported_user_id": 2,
     "complaint_type": "spam",
     "description": "Test complaint"
   }
   ```
2. Go to "Complaints"
3. **Expected**: See complaint in pending status
4. Resolve complaint:
   - Click complaint → Edit
   - Set status="resolved", add moderator notes
   - **Expected**: Status updated to resolved

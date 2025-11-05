# 🧪 FreeMarket Testing Guide

**Version:** 2.0 | **Last Updated:** Ноябрь 2025

---
### Test Scenario 8: Категории v6 миграции

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
### Test Scenario 9: Auth rotation & LK access

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


## 🎯 Testing Overview

This guide covers:
- ✅ Quick structural tests (no database needed)
- ✅ Full integration tests (with database)
- ✅ Test scenarios (all 7 core flows)
- ✅ Matching algorithm verification
- ✅ Location filtering validation
- ✅ Chain discovery testing
- ✅ API endpoint testing

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

Phase 7: Production Readiness
  ☐ No hardcoded values
  ☐ Error handling implemented
  ☐ Logging working
  ☐ Performance acceptable (< 500ms)
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

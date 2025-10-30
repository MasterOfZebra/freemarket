# 🚀 Quick Testing Commands - Copy & Paste Ready

**Use these commands to quickly test all functionality!**

---

## ⚡ PHASE 1: STRUCTURAL TEST (15 min)

```powershell
cd C:\Users\user\Desktop\FreeMarket
python backend/quick_test.py
```

**Expected:** ✅ All modules import successfully

---

## ⚡ PHASE 2: DATABASE SETUP (5 min)

```powershell
# Set environment variables
set DATABASE_URL=postgresql://assistadmin_pg:assistMurzAdmin@localhost:5432/assistance_kz
set TELEGRAM_BOT_TOKEN=test_token
set ENV=development

# Test connection
python -c "from backend.database import engine; engine.connect(); print('✅ DB Connected!')"

# Start API server (in separate terminal)
cd backend
python -m uvicorn main:app --reload --port 8000
```

---

## ⚡ PHASE 3: API HEALTH CHECK (2 min)

```bash
# Terminal 2: Test health
curl http://localhost:8000/health
curl http://localhost:8000/
```

**Expected:**
```json
{"status":"ok","message":"FreeMarket API is running"}
{"message":"FreeMarket API","version":"1.0.0"}
```

---

## ⚡ PHASE 4: USER REGISTRATION TEST (5 min)

```bash
# Create User 1 (Алматы)
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","contact":"@alice","locations":["Алматы"]}'

# Create User 2 (Алматы)
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"bob","contact":"@bob","locations":["Алматы"]}'

# Create User 3 (Астана)
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"charlie","contact":"@charlie","locations":["Астана"]}'

# Verify in database
psql -h localhost -U assistadmin_pg -d assistance_kz -c "SELECT id, username, locations FROM users;"
```

---

## ⚡ PHASE 5: CREATE LISTINGS (10 min)

### Alice creates WANT + OFFER

```bash
# Alice WANT: needs tools
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "title": "Нужен набор инструментов",
    "description": "Полный набор ручных инструментов",
    "category": "tools",
    "kind": 2,
    "active": true
  }'

# Alice OFFER: has bicycle parts
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "title": "Запчасти для велосипеда",
    "description": "Различные запчасти для ремонта",
    "category": "tools",
    "kind": 1,
    "active": true
  }'
```

### Bob creates OFFER + WANT

```bash
# Bob OFFER: has bicycle
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "title": "Велосипед детский",
    "description": "Детский велосипед 16 дюймов",
    "category": "tools",
    "kind": 1,
    "active": true
  }'

# Bob WANT: needs bicycle parts
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
```

### Charlie creates WANT

```bash
# Charlie WANT: needs bicycle (different location)
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
```

### Verify listings

```bash
# Get all wants
curl "http://localhost:8000/api/market-listings/wants/all"

# Get all offers
curl "http://localhost:8000/api/market-listings/offers/all"

# Get Alice's listings
curl "http://localhost:8000/api/market-listings/user/1"
```

---

## ⚡ PHASE 6: BILATERAL MATCHING (5 min)

```bash
# Run matching pipeline
curl -X POST http://localhost:8000/api/matching/run-pipeline \
  -H "Content-Type: application/json" \
  -d '{"user_id": null}'
```

**Expected Response:**
```json
{
  "bilateral_matches": 1,
  "exchange_chains": 0,
  "total_participants": 2,
  "errors": []
}
```

### Verify in database

```bash
psql -h localhost -U assistadmin_pg -d assistance_kz << EOF
-- Check matches
SELECT id, user_a_id, user_b_id, score FROM matches WHERE active = true;

-- Check notifications
SELECT id, user_id, payload FROM notifications ORDER BY created_at DESC LIMIT 5;
EOF
```

---

## ⚡ PHASE 7: LOCATION FILTERING (5 min)

```bash
# Update Alice to have multiple locations
curl -X PUT http://localhost:8000/api/users/1/locations \
  -H "Content-Type: application/json" \
  -d '{"locations": ["Алматы", "Астана"]}'

# Update Charlie
curl -X PUT http://localhost:8000/api/users/3/locations \
  -H "Content-Type: application/json" \
  -d '{"locations": ["Астана"]}'

# Create listing for Charlie (same category)
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 3,
    "title": "Старые инструменты",
    "description": "Есть старые инструменты",
    "category": "tools",
    "kind": 1,
    "active": true
  }'

# Run matching again - now Alice + Charlie should match (via Астана)
curl -X POST http://localhost:8000/api/matching/run-pipeline \
  -H "Content-Type: application/json" \
  -d '{"user_id": null}'
```

---

## ⚡ PHASE 8: 3-WAY CHAIN DISCOVERY (5 min)

```bash
# If you have the setup from above:
# Alice: WANT tools ← OFFER parts
# Bob: WANT parts ← OFFER bike
# Charlie: WANT bike ← OFFER tools

# Run matching to discover chains
curl -X POST http://localhost:8000/api/matching/run-pipeline \
  -H "Content-Type: application/json" \
  -d '{"user_id": null}'

# Check for chains
curl "http://localhost:8000/api/chains/all?status=pending"

# Get user chains
curl "http://localhost:8000/api/chains/user/1?status=pending"
```

**Expected:** 1 chain with 3 participants

---

## 🧪 DATABASE QUICK CHECKS

```bash
# Connect to database
psql -h localhost -U assistadmin_pg -d assistance_kz

# List all tables
\dt

# Check users
SELECT * FROM users;

# Check listings
SELECT id, user_id, title, kind FROM items;

# Check matches
SELECT * FROM matches WHERE active = true;

# Check chains
SELECT * FROM exchange_chains;

# Check notifications
SELECT * FROM notifications ORDER BY created_at DESC;

# Exit
\q
```

---

## 🧪 CLEAN START (Reset for testing)

```bash
# Delete all test data
psql -h localhost -U assistadmin_pg -d assistance_kz << EOF
TRUNCATE notifications CASCADE;
TRUNCATE exchange_chains CASCADE;
TRUNCATE edges CASCADE;
TRUNCATE matches CASCADE;
TRUNCATE items CASCADE;
TRUNCATE users CASCADE;
EOF

echo "✅ Database cleaned!"
```

---

## 📊 PERFORMANCE LOAD TEST

```bash
# Install apache-bench if needed
choco install apache-bench

# Test health endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8000/health

# Test user list endpoint
ab -n 50 -c 5 http://localhost:8000/api/users/list

# Expected: ~100+ requests/sec, <50ms avg response time
```

---

## 🔒 SECURITY TESTS

```bash
# Test SQL injection (should fail gracefully)
curl -X GET "http://localhost:8000/api/users/username/test'; DROP TABLE users; --"

# Test invalid JSON (should return 400)
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d 'invalid json'

# Test missing fields (should return validation error)
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test"}'

# Test duplicate username (should return 409)
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","contact":"@alice2","locations":["Алматы"]}'
```

---

## 🐳 DOCKER TESTING

```bash
# Build all images
docker-compose -f docker/docker-compose.prod.yml build

# Start services
docker-compose -f docker/docker-compose.prod.yml up -d

# Check status
docker-compose -f docker/docker-compose.prod.yml ps

# View logs
docker-compose -f docker/docker-compose.prod.yml logs backend
docker-compose -f docker/docker-compose.prod.yml logs bot

# Test API
curl http://localhost:8000/health

# Check resource usage
docker stats

# Stop services
docker-compose -f docker/docker-compose.prod.yml down

# Full cleanup
docker-compose -f docker/docker-compose.prod.yml down -v
```

---

## ✅ FULL TEST SEQUENCE (Copy & Paste)

```bash
# 1. Structural test
python backend/quick_test.py

# 2. Set env vars & start server
set DATABASE_URL=postgresql://assistadmin_pg:assistMurzAdmin@localhost:5432/assistance_kz
set TELEGRAM_BOT_TOKEN=test_token
cd backend
python -m uvicorn main:app --reload --port 8000

# 3. In another terminal - Run all tests
cd C:\Users\user\Desktop\FreeMarket

# Health check
curl http://localhost:8000/health

# Create users
curl -X POST http://localhost:8000/api/users/ -H "Content-Type: application/json" -d '{"username":"alice","contact":"@alice","locations":["Алматы"]}'
curl -X POST http://localhost:8000/api/users/ -H "Content-Type: application/json" -d '{"username":"bob","contact":"@bob","locations":["Алматы"]}'
curl -X POST http://localhost:8000/api/users/ -H "Content-Type: application/json" -d '{"username":"charlie","contact":"@charlie","locations":["Астана"]}'

# Create listings (see PHASE 5 above)

# Run matching
curl -X POST http://localhost:8000/api/matching/run-pipeline -H "Content-Type: application/json" -d '{"user_id": null}'

# Verify in database
psql -h localhost -U assistadmin_pg -d assistance_kz -c "SELECT * FROM matches WHERE active = true;"

# Check chains
curl "http://localhost:8000/api/chains/all?status=pending"

# ✅ All tests passed!
```

---

## 📝 TROUBLESHOOTING

```bash
# Port already in use?
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Database connection failed?
psql -h localhost -U assistadmin_pg -d assistance_kz

# API not responding?
docker logs freemarket_backend

# Check all services
docker ps
docker-compose -f docker/docker-compose.prod.yml ps

# Restart API
python -m uvicorn main:app --reload --port 8000
```

---

**Total Testing Time:** ~1.5 hours to run all phases ⏱️

**Status:** ✅ Ready to test! 🎯

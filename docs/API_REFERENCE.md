# 📡 FreeMarket API Reference

**Version:** 2.0 | **Last Updated:** January 2025

---

## 🚀 Quick Access

| Endpoint Group | Count | Status |
|---|---|---|
| **Health** | 2 | ✅ Active |
| **Users** | 5 | ✅ Active |
| **Market Listings** | 5 | ✅ Active |
| **Matching** | 3 | ✅ Active |
| **Exchange Chains** | 5 | ✅ Active |
| **Notifications** | 2 | ✅ Active |
| **TOTAL** | **22** | ✅ Ready |

---

## 🏥 Health Endpoints

### GET `/health`
Check if API is running.

**Response:**
```json
{
  "status": "ok",
  "message": "FreeMarket API is running"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### GET `/`
Root API information.

**Response:**
```json
{
  "message": "FreeMarket API",
  "version": "1.0.0"
}
```

---

## 👥 Users Endpoints

### POST `/api/users/`
Create a new user with registration data.

**Request Body:**
```json
{
  "username": "alice_123",
  "contact": "@alice_telegram",
  "locations": ["Алматы", "Астана"],
  "trust_score": 0.0
}
```

**Response:**
```json
{
  "id": 1,
  "username": "alice_123",
  "contact": "@alice_telegram",
  "locations": ["Алматы", "Астана"],
  "trust_score": 0.0,
  "created_at": "2025-01-15T10:30:00",
  "active": true
}
```

**Status Codes:**
- `201 Created` - User created successfully
- `400 Bad Request` - Validation error
- `409 Conflict` - Username already exists

**Example:**
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice_123",
    "contact": "@alice_telegram",
    "locations": ["Алматы"]
  }'
```

---

### GET `/api/users/{user_id}`
Get user details by ID.

**Response:**
```json
{
  "id": 1,
  "username": "alice_123",
  "contact": "@alice_telegram",
  "locations": ["Алматы", "Астана"],
  "trust_score": 0.85,
  "created_at": "2025-01-15T10:30:00",
  "active": true
}
```

**Status Codes:**
- `200 OK` - User found
- `404 Not Found` - User doesn't exist

**Example:**
```bash
curl http://localhost:8000/api/users/1
```

---

### GET `/api/users/username/{username}`
Get user by username.

**Response:** Same as above

**Status Codes:**
- `200 OK` - User found
- `404 Not Found` - Username doesn't exist

**Example:**
```bash
curl http://localhost:8000/api/users/username/alice_123
```

---

### PUT `/api/users/{user_id}/locations`
Update user's selected locations.

**Request Body:**
```json
{
  "locations": ["Алматы", "Шымкент"]
}
```

**Response:**
```json
{
  "id": 1,
  "locations": ["Алматы", "Шымкент"],
  "message": "Locations updated"
}
```

**Validation:**
- Valid locations: `["Алматы", "Астана", "Шымкент"]`
- Minimum 1 location required
- Maximum 3 locations

**Status Codes:**
- `200 OK` - Updated successfully
- `400 Bad Request` - Invalid location
- `404 Not Found` - User not found

**Example:**
```bash
curl -X PUT http://localhost:8000/api/users/1/locations \
  -H "Content-Type: application/json" \
  -d '{"locations": ["Алматы"]}'
```

---
## 🧭 Category & LK Endpoints (v6)

### GET `/v1/categories`
Получить список версий категорий и структуру формы для создания/редактирования объявлений.

**Response (пример):**
```json
{
  "version": 6,
  "categories": [
    {"id": 1, "name": "Транспорт", "slug": "transport"},
    {"id": 2, "name": "Инструменты", "slug": "tools"}
  ],
  "mappings": {
    "legacy_to_v6": {"old_slug": "transport_old"}
  }
}
```

### GET `/v1/categories/permanent`
Список категорий для постоянного обмена.

### GET `/v1/categories/temporary`
Список категорий для временного обмена.

### GET `/user/cabinet`
Личный кабинет пользователя (профиль, мои объявления, активные обмены).

### GET `/user/listings`
Список объявлений пользователя.

### GET `/user/exchanges`
Список активных обменов пользователя.

### PUT `/user/profile`
Обновление профиля пользователя.

### DELETE `/user/account`
Удаление аккаунта пользователя.

### POST `/auth/register`
Регистрация пользователя (с подтверждением email/телефона по мере реализации).

### POST `/auth/login`
Авторизация и выдача access/refresh токенов.

### POST `/auth/register`
Регистрация нового пользователя.

**Request Body:**
```json
{
  "username": "alice_123",
  "email": "alice@example.com",
  "phone": "+7-777-123-4567",
  "password": "secure_password_123",
  "full_name": "Alice Smith",
  "telegram_contact": "@alice_telegram",
  "city": "Алматы",
  "bio": "Люблю велосипеды и инструменты"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "username": "alice_123",
  "email": "alice@example.com",
  "full_name": "Alice Smith",
  "telegram_contact": "@alice_telegram",
  "city": "Алматы",
  "bio": "Люблю велосипеды и инструменты",
  "is_active": true,
  "created_at": "2025-11-05T10:00:00Z"
}
```

### POST `/auth/login`
Авторизация и получение JWT токенов.

**Request Body:**
```json
{
  "username": "alice_123",
  "password": "secure_password_123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": 1,
    "username": "alice_123",
    "email": "alice@example.com"
  }
}
```

**Cookies Set:**
- `refresh_token`: HttpOnly, Secure, SameSite=Lax, expires in 30 days
- `refresh_token_hash`: Server-side hash for validation

### POST `/auth/refresh`
Обновление access token (использует HttpOnly cookie).

**Request:** No body required (reads from cookie)

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Security Features:**
- Old refresh token marked as revoked
- New refresh token issued and stored
- Rate limited (5 requests per 5 minutes per IP)

### POST `/auth/logout`
Выход из системы и отзыв refresh токена.

**Request:** No body required

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

**Actions:**
- Refresh token cookie cleared (expires immediately)
- Refresh token hash removed from Redis
- Auth event logged

### POST `/auth/revoke-sessions`
Отзыв всех сессий пользователя.

**Request:** Requires valid access token

**Response (200 OK):**
```json
{
  "message": "All sessions revoked",
  "revoked_count": 3
}
```

**Actions:**
- All refresh tokens for user marked as revoked in Redis
- User must re-login on all devices

### GET `/auth/me`
Получение профиля текущего пользователя.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "alice_123",
  "email": "alice@example.com",
  "full_name": "Alice Smith",
  "telegram_contact": "@alice_telegram",
  "city": "Алматы",
  "bio": "Люблю велосипеды и инструменты",
  "trust_score": 0.95,
  "exchange_count": 5,
  "rating_avg": 4.8,
  "is_active": true,
  "is_verified": false,
  "last_login_at": "2025-11-05T10:00:00Z"
}
```

### Complete Authentication Flow

```javascript
// 1. Register
const registerResponse = await fetch('/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'alice_123',
    email: 'alice@example.com',
    password: 'secure_password'
  })
});

// 2. Login
const loginResponse = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'alice_123',
    password: 'secure_password'
  })
});
const { access_token } = await loginResponse.json();

// 3. Use API with access token
const profileResponse = await fetch('/api/auth/me', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});

// 4. Refresh token automatically (when expired)
const refreshResponse = await fetch('/api/auth/refresh', {
  method: 'POST'
  // Cookie is sent automatically
});
const { access_token: new_token } = await refreshResponse.json();

// 5. Logout
await fetch('/api/auth/logout', { method: 'POST' });
```

### GET `/api/users/list`
List all active users (paginated).

**Query Parameters:**
- `skip` (optional, default: 0) - Skip N users
- `limit` (optional, default: 20) - Return N users

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "username": "alice_123",
      "contact": "@alice_telegram",
      "locations": ["Алматы"],
      "trust_score": 0.85
    },
    {
      "id": 2,
      "username": "bob_456",
      "contact": "@bob_telegram",
      "locations": ["Астана"],
      "trust_score": 0.92
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

**Example:**
```bash
curl "http://localhost:8000/api/users/list?skip=0&limit=10"
```

---

## 📋 Market Listings Endpoints

### POST `/api/market-listings/`
Create a new want or offer listing.

**Request Body:**
```json
{
  "user_id": 1,
  "title": "Нужен велосипед",
  "description": "Ищу детский велосипед, 16-20 дюймов",
  "category": "tools",
  "kind": 2,
  "active": true
}
```

**Kind Values:**
- `1` = Offer (ДАРЮ)
- `2` = Want (ХОЧУ)

**Categories:**
- `food` - Food
- `clothes` - Clothing
- `tools` - Tools & Equipment
- `furniture` - Furniture
- `books` - Books & Media
- `services` - Services
- `other` - Other

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Нужен велосипед",
  "description": "Ищу детский велосипед, 16-20 дюймов",
  "category": "tools",
  "kind": 2,
  "active": true,
  "created_at": "2025-01-15T10:35:00"
}
```

**Status Codes:**
- `201 Created` - Listing created
- `400 Bad Request` - Validation error
- `404 Not Found` - User not found

**Example:**
```bash
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "title": "Нужен велосипед",
    "description": "Детский велосипед 16-20 дюймов",
    "category": "tools",
    "kind": 2
  }'
```

---

### GET `/api/market-listings/wants/all`
Get all want listings (what people need).

**Query Parameters:**
- `skip` (optional, default: 0)
- `limit` (optional, default: 20)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "title": "Нужен велосипед",
      "description": "Детский велосипед 16-20 дюймов",
      "category": "tools",
      "kind": 2,
      "active": true
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 20
}
```

**Example:**
```bash
curl "http://localhost:8000/api/market-listings/wants/all?limit=10"
```

---

### GET `/api/market-listings/offers/all`
Get all offer listings (what people have).

**Query Parameters:**
- `skip` (optional, default: 0)
- `limit` (optional, default: 20)

**Response:** Same structure as wants

**Example:**
```bash
curl "http://localhost:8000/api/market-listings/offers/all?limit=10"
```

---

### GET `/api/market-listings/{listing_id}`
Get specific listing details.

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Нужен велосипед",
  "description": "Детский велосипед 16-20 дюймов",
  "category": "tools",
  "kind": 2,
  "active": true,
  "created_at": "2025-01-15T10:35:00",
  "user": {
    "username": "alice_123",
    "contact": "@alice_telegram",
    "locations": ["Алматы"]
  }
}
```

**Status Codes:**
- `200 OK` - Found
- `404 Not Found` - Listing doesn't exist

**Example:**
```bash
curl http://localhost:8000/api/market-listings/1
```

---

### GET `/api/market-listings/user/{user_id}`
Get all listings for a specific user.

**Query Parameters:**
- `skip` (optional, default: 0)
- `limit` (optional, default: 20)

**Response:**
```json
{
  "items": [
    { "id": 1, "kind": 2, "title": "..." },
    { "id": 2, "kind": 1, "title": "..." }
  ],
  "total": 5,
  "skip": 0,
  "limit": 20
}
```

**Example:**
```bash
curl http://localhost:8000/api/market-listings/user/1
```

---

## 🔄 Matching Endpoints

### POST `/api/matching/run-pipeline`
Run the complete unified matching pipeline.

**Request Body:**
```json
{
  "user_id": null
}
```

**Parameters:**
- `user_id` (optional): If provided, only match this user. If null, match all active users.

**Response:**
```json
{
  "bilateral_matches": 3,
  "exchange_chains": 2,
  "total_participants": 8,
  "errors": []
}
```

**5-Phase Pipeline:**
1. **Location-aware filtering** - Find candidates in same cities
2. **Unified scoring** - Text similarity (0.7) + trust bonus (0.2) + location bonus (0.1)
3. **Bilateral matching** - Find mutual exchanges (Alice.want ⊆ Bob.offer AND Bob.want ⊆ Alice.offer)
4. **Chain discovery** - Find 3+ participant cycles
5. **Notifications** - Send notifications to all participants

**Status Codes:**
- `200 OK` - Pipeline completed
- `500 Internal Error` - Pipeline failed

**Example:**
```bash
curl -X POST http://localhost:8000/api/matching/run-pipeline \
  -H "Content-Type: application/json" \
  -d '{"user_id": null}'
```

---

### GET `/api/matching/status`
Get status of last matching run.

**Response:**
```json
{
  "last_run": "2025-01-15T12:00:00",
  "bilateral_matches": 15,
  "chains_discovered": 5,
  "participants_notified": 38,
  "status": "success"
}
```

**Example:**
```bash
curl http://localhost:8000/api/matching/status
```

---

### POST `/api/matching/test-flow`
Test the matching flow with sample data (for development).

**Request Body:**
```json
{
  "scenario": "bilateral"
}
```

**Scenario Options:**
- `bilateral` - Test 2-way matching
- `chains` - Test 3+ way chains
- `locations` - Test location filtering
- `scoring` - Test score calculation
- `full` - Run all tests

**Response:**
```json
{
  "test": "bilateral",
  "passed": true,
  "matches_found": 2,
  "details": "Alice + Bob match successful"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/matching/test-flow \
  -H "Content-Type: application/json" \
  -d '{"scenario": "bilateral"}'
```

---

## 🔗 Exchange Chains Endpoints

### POST `/api/chains/discover`
Manually trigger chain discovery.

**Request Body:**
```json
{
  "min_participants": 3,
  "max_participants": 10
}
```

**Response:**
```json
{
  "chains_created": 5,
  "total_participants": 18,
  "chains": [
    {
      "id": 1,
      "participants": 3,
      "items": [1, 5, 9],
      "score": 0.85
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/chains/discover \
  -H "Content-Type: application/json" \
  -d '{"min_participants": 3, "max_participants": 10}'
```

---

### GET `/api/chains/all`
Get all discovered exchange chains.

**Query Parameters:**
- `skip` (optional, default: 0)
- `limit` (optional, default: 20)
- `status` (optional): `pending`, `accepted`, `completed`

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "participants": ["alice_123", "bob_456", "charlie_789"],
      "items": [1, 5, 9],
      "status": "pending",
      "score": 0.85,
      "created_at": "2025-01-15T12:00:00"
    }
  ],
  "total": 12,
  "skip": 0,
  "limit": 20
}
```

**Example:**
```bash
curl "http://localhost:8000/api/chains/all?status=pending"
```

---

### GET `/api/chains/user/{user_id}`
Get all chains for a specific user.

**Query Parameters:**
- `status` (optional): Filter by status

**Response:** Same as above

**Example:**
```bash
curl http://localhost:8000/api/chains/user/1?status=pending
```

---

### POST `/api/chains/{chain_id}/accept`
User accepts a proposed chain.

**Request Body:**
```json
{
  "user_id": 1
}
```

**Response:**
```json
{
  "chain_id": 1,
  "user_id": 1,
  "status": "accepted",
  "message": "You've accepted this exchange chain"
}
```

**Status Codes:**
- `200 OK` - Accepted
- `400 Bad Request` - Invalid request
- `404 Not Found` - Chain not found

**Example:**
```bash
curl -X POST http://localhost:8000/api/chains/1/accept \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

---

### POST `/api/chains/{chain_id}/decline`
User declines a proposed chain.

**Request Body:**
```json
{
  "user_id": 1,
  "reason": "Не подходит по времени"
}
```

**Response:**
```json
{
  "chain_id": 1,
  "user_id": 1,
  "status": "declined",
  "message": "You've declined this exchange chain"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/chains/1/decline \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "reason": "Not available"}'
```

---

## 📲 Notifications Endpoints

### GET `/api/notifications/`
Get pending notifications for a user.

**Query Parameters:**
- `user_id` (required) - User ID
- `status` (optional): `pending`, `read`, `all`

**Response:**
```json
{
  "notifications": [
    {
      "id": 1,
      "user_id": 1,
      "type": "bilateral_match",
      "payload": {
        "partner": "bob_456",
        "partner_contact": "@bob_telegram",
        "partner_item": "Велосипед детский",
        "your_item": "Самокат",
        "score": 0.92,
        "message": "Найдено совпадение с bob_456!"
      },
      "read": false,
      "created_at": "2025-01-15T12:00:00"
    }
  ],
  "count": 1
}
```

**Example:**
```bash
curl "http://localhost:8000/api/notifications/?user_id=1&status=pending"
```

---

### POST `/api/notifications/{notification_id}/read`
Mark notification as read.

**Response:**
```json
{
  "notification_id": 1,
  "status": "read"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/notifications/1/read
```

---

## 🔍 Query Parameters & Pagination

All list endpoints support:

```
GET /api/[resource]/all
  ?skip=0          # Skip N items (default: 0)
  &limit=20        # Return N items (default: 20)
  &sort=created    # Sort field (optional)
  &order=desc      # asc or desc (default: desc)
```

**Example:**
```bash
curl "http://localhost:8000/api/market-listings/offers/all?skip=20&limit=10&sort=created&order=desc"
```

---

## ⚠️ Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message here",
  "status_code": 400,
  "error_type": "validation_error"
}
```

**Common Status Codes:**
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Validation error
- `404 Not Found` - Resource not found
- `409 Conflict` - Conflict (e.g., duplicate username)
- `500 Internal Server Error` - Server error

---

## 🚀 Testing Endpoints with curl

### Complete User Flow Example

```bash
# 1. Create user
USER_ID=$(curl -s -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","contact":"@alice","locations":["Алматы"]}' \
  | jq -r '.id')

# 2. Create listings
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER_ID,\"title\":\"Велосипед\",\"kind\":2,\"category\":\"tools\"}"

# 3. Run matching
curl -X POST http://localhost:8000/api/matching/run-pipeline \
  -H "Content-Type: application/json" \
  -d '{"user_id":null}'

# 4. Check chains
curl "http://localhost:8000/api/chains/all?status=pending"
```

---

## 📊 API Metrics

| Metric | Value |
|--------|-------|
| Total Endpoints | 22 |
| Response Time | < 200ms |
| Max Page Size | 100 |
| Default Page Size | 20 |
| Timeout | 30s |

---

**For more details, see [docs/ARCHITECTURE.md](./ARCHITECTURE.md) or [docs/TESTING.md](./TESTING.md)**

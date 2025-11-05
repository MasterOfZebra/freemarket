# 📡 FreeMarket API Reference

**Version:** 2.0 | **Last Updated:** November 2025

---

## 🚀 Quick Access

| Endpoint Group | Count | Status |
|---|---|---|
| **Health** | 2 | ✅ Active |
| **Users** | 5 | ✅ Active |
| **Authentication** | 7 | ✅ Active |
| **User Cabinet** | 5 | ✅ Active |
| **Categories (v6)** | 3 | ✅ Active |
| **Listings Exchange** | 5 | ✅ Active |
| **Matching** | 3 | ✅ Active |
| **Exchange Chains** | 5 | ✅ Active |
| **Notifications** | 2 | ✅ Active |
| **TOTAL** | **37** | ✅ Ready |

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
curl https://assistance-kz.ru/health
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
Create a new user. For full registration with password, use `/auth/register`.

**Request Body:**
```json
{
  "username": "test_user",
  "email": "test@example.com",
  "phone": "+77001234567",
  "full_name": "Test User",
  "telegram_contact": "@test_user_tg",
  "city": "Алматы",
  "bio": "Test bio"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "test_user",
  "email": "test@example.com",
  "full_name": "Test User",
  "telegram_contact": "@test_user_tg",
  "city": "Алматы",
  "bio": "Test bio",
  "is_active": true,
  "created_at": "2025-11-05T10:00:00Z"
}
```

**Status Codes:**
- `201 Created` - User created successfully
- `400 Bad Request` - Validation error
- `409 Conflict` - Username/email/phone already exists

**Example:**
```bash
curl -X POST https://assistance-kz.ru/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "email": "test@example.com",
    "phone": "+77001234567",
    "full_name": "Test User",
    "city": "Алматы"
  }'
```

---

### GET `/api/users/{user_id}`
Get user details by ID.

**Response:**
```json
{
  "id": 1,
  "username": "test_user",
  "email": "test@example.com",
  "full_name": "Test User",
  "telegram_contact": "@test_user_tg",
  "city": "Алматы",
  "bio": "Test bio",
  "trust_score": 0.0,
  "exchange_count": 0,
  "rating_avg": 0.0,
  "is_active": true,
  "is_verified": false,
  "email_verified": false,
  "phone_verified": false,
  "created_at": "2025-11-05T10:00:00Z",
  "updated_at": "2025-11-05T10:00:00Z",
  "last_login_at": null,
  "last_active_at": null,
  "telegram_id": null,
  "telegram_username": null,
  "telegram_first_name": null
}
```

**Status Codes:**
- `200 OK` - User found
- `404 Not Found` - User doesn't exist

**Example:**
```bash
curl https://assistance-kz.ru/api/users/1
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
curl https://assistance-kz.ru/api/users/username/test_user
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
curl -X PUT https://assistance-kz.ru/api/users/1/locations \
  -H "Content-Type: application/json" \
  -d '{"locations": ["Алматы"]}'
```

---

## 🔑 Authentication Endpoints

### POST `/auth/register`
Register a new user with email, password, and optional profile details.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "StrongPassword123!",
  "username": "newuser_freemarket",
  "full_name": "New User",
  "city": "Астана",
  "telegram_contact": "@newuser_telegram"
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "username": "newuser_freemarket",
  "email": "newuser@example.com",
  "full_name": "New User",
  "telegram_contact": "@newuser_telegram",
  "city": "Астана",
  "is_active": true,
  "is_verified": false,
  "email_verified": false,
  "phone_verified": false,
  "created_at": "2025-11-05T10:30:00Z"
}
```

---

### POST `/auth/login`
Authenticate a user and receive JWT access and refresh tokens. Refresh token is set as an HttpOnly cookie.

**Request Body:**
```json
{
  "username": "test_user",
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
    "username": "test_user",
    "email": "test@example.com"
  }
}
```

**Cookies Set:**
- `refresh_token`: HttpOnly, Secure, SameSite=Lax, expires in 7 days

---

### POST `/auth/refresh`
Refresh the access token using the HttpOnly refresh token cookie. Automatically revokes the old refresh token.

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
- Old refresh token marked as revoked in Redis
- New refresh token issued and stored in cookie
- Rate limited (5 requests per 5 minutes per IP)

---

### POST `/auth/logout`
Logout the current user, clear refresh token cookie, and revoke the refresh token in Redis.

**Request:** No body required

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

**Actions:**
- `refresh_token` cookie cleared
- Refresh token hash removed from Redis

---

### POST `/auth/change-password`
Change the password for the authenticated user.

**Request Body:**
```json
{
  "old_password": "CurrentPassword123!",
  "new_password": "NewStrongPassword123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password updated successfully"
}
```

**Status Codes:**
- `200 OK` - Password changed
- `400 Bad Request` - Invalid old password or validation error

---

### POST `/auth/revoke-sessions`
Revoke all active refresh tokens for the authenticated user, forcing re-login on all devices.

**Request:** Requires valid access token

**Response (200 OK):**
```json
{
  "message": "All sessions revoked",
  "revoked_count": 1
}
```

**Actions:**
- All refresh tokens for user marked as revoked in Redis
- User must re-login on all devices

---

### GET `/auth/me`
Get the profile of the currently authenticated user.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "test_user",
  "email": "test@example.com",
  "full_name": "Test User",
  "telegram_contact": "@test_user_tg",
  "city": "Алматы",
  "bio": "Test bio",
  "trust_score": 0.0,
  "exchange_count": 0,
  "rating_avg": 0.0,
  "is_active": true,
  "is_verified": false,
  "email_verified": false,
  "phone_verified": false,
  "created_at": "2025-11-05T10:00:00Z",
  "updated_at": "2025-11-05T10:00:00Z",
  "last_login_at": "2025-11-05T10:35:00Z",
  "last_active_at": "2025-11-05T10:35:00Z",
  "telegram_id": null,
  "telegram_username": null,
  "telegram_first_name": null
}
```

---

## 👤 User Cabinet Endpoints

### GET `/user/cabinet`
Get aggregated data for the authenticated user's personal cabinet, including profile, listings, and active exchanges.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "user_profile": {
    "id": 1,
    "username": "test_user",
    "full_name": "Test User"
  },
  "my_listings": [
    { "id": 101, "title": "Мой велосипед", "exchange_type": "PERMANENT" }
  ],
  "active_exchanges": [
    { "chain_id": 5, "partner_name": "Другой пользователь" }
  ]
}
```

---

### GET `/user/listings`
Get all listings created by the authenticated user.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
[
  {
    "id": 101,
    "title": "Мой велосипед",
    "description": "Старый, но рабочий велосипед",
    "user_id": 1,
    "exchange_type": "PERMANENT",
    "created_at": "2025-11-05T11:00:00Z"
  },
  {
    "id": 102,
    "title": "Нужна дрель",
    "description": "Ищу электрическую дрель на пару дней",
    "user_id": 1,
    "exchange_type": "TEMPORARY",
    "created_at": "2025-11-05T11:10:00Z"
  }
]
```

---

### GET `/user/exchanges`
Get active exchange chains or bilateral matches involving the authenticated user.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
[
  {
    "match_id": 201,
    "partner_username": "alice_other",
    "status": "pending",
    "matching_categories": ["tools"],
    "created_at": "2025-11-05T11:20:00Z"
  }
]
```

---

### PUT `/user/profile`
Update the profile details of the authenticated user.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "full_name": "Updated Name",
  "bio": "New interesting bio",
  "city": "Астана",
  "telegram_contact": "@updated_tg"
}
```

**Response (200 OK):**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "username": "test_user",
    "full_name": "Updated Name",
    "city": "Астана"
  }
}
```

---

### DELETE `/user/account`
Delete the authenticated user's account. This is a sensitive operation.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "message": "Account deleted successfully"
}
```

---

## 📋 Categories API (v6)

### GET `/v1/categories`
Get the current active category version and all categories, organized by exchange type.

**Query Parameters:**
- `version` (optional, default: `v6.0`): Category system version to retrieve.

**Response (200 OK):**
```json
{
  "version": "v6.0",
  "description": "Initial v6 category system with expanded temporary and permanent exchanges",
  "categories": {
    "permanent": [
      {
        "slug": "personal_transport",
        "name": "Личные и спецтранспортные средства",
        "group": "🚗 Транспорт и техника",
        "emoji": "🚗",
        "sort_order": 0,
        "form_schema": null
      }
    ],
    "temporary": [
      {
        "slug": "bicycles",
        "name": "Велосипеды, самокаты, гироскутеры",
        "group": "🚗 Транспорт и мобильность",
        "emoji": "🚗",
        "sort_order": 0,
        "form_schema": null
      }
    ]
  }
}
```

---

### GET `/v1/categories/{exchange_type}`
Get categories for a specific exchange type (`permanent` or `temporary`).

**Path Parameters:**
- `exchange_type` (required): `permanent` or `temporary`.

**Query Parameters:**
- `version` (optional, default: `v6.0`): Category system version to retrieve.

**Response (200 OK):**
```json
[
  {
    "slug": "personal_transport",
    "name": "Личные и спецтранспортные средства",
    "group": "🚗 Транспорт и техника",
    "emoji": "🚗",
    "sort_order": 0,
    "form_schema": null
  }
]
```

---

### GET `/v1/categories/groups/{exchange_type}`
Get unique category groups for a specific exchange type (`permanent` or `temporary`).

**Path Parameters:**
- `exchange_type` (required): `permanent` or `temporary`.

**Query Parameters:**
- `version` (optional, default: `v6.0`): Category system version to retrieve.

**Response (200 OK):**
```json
{
  "groups": [
    "🚗 Транспорт и техника",
    "🔧 Инструменты и оборудование"
  ]
}
```

---

## 📝 Listings Exchange Endpoints

### POST `/api/listings/create-by-categories`
Create a new listing by providing wants and offers organized by categories.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "wants": {
    "PERMANENT": [
      {
        "item_name": "Учебник по Python",
        "value_tenge": 15000,
        "description": "Ищу для изучения"
      }
    ],
    "TEMPORARY": [
      {
        "item_name": "Электросамокат",
        "value_tenge": 5000,
        "duration_days": 3,
        "description": "На выходные"
      }
    ]
  },
  "offers": {
    "PERMANENT": [
      {
        "item_name": "Книга по JS",
        "value_tenge": 12000,
        "description": "Могу отдать"
      }
    ]
  }
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "created_at": "2025-11-05T12:00:00Z",
  "listings": [
    {
      "id": 101,
      "item_type": "WANT",
      "exchange_type": "PERMANENT",
      "item_name": "Учебник по Python",
      "value_tenge": 15000,
      "duration_days": null
    },
    {
      "id": 102,
      "item_type": "WANT",
      "exchange_type": "TEMPORARY",
      "item_name": "Электросамокат",
      "value_tenge": 5000,
      "duration_days": 3
    }
  ]
}
```

---

### POST `/api/listings/create`
Create a single listing item (either want or offer).

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "item_type": "WANT",
  "exchange_type": "PERMANENT",
  "item_name": "Книга по Алгоритмам",
  "value_tenge": 20000,
  "description": "Новое издание"
}
```

**Response (201 Created):**
```json
{
  "id": 103,
  "item_type": "WANT",
  "exchange_type": "PERMANENT",
  "item_name": "Книга по Алгоритмам",
  "value_tenge": 20000,
  "description": "Новое издание",
  "user_id": 1,
  "created_at": "2025-11-05T12:05:00Z"
}
```

---

### GET `/api/listings/wants`
Get all want listings (what people need).

**Response:** Same structure as `/user/listings`

---

### GET `/api/listings/offers`
Get all offer listings (what people have).

**Response:** Same structure as `/user/listings`

---

### GET `/api/listings/user/{user_id}`
Get all listings for a specific user.

**Path Parameters:**
- `user_id` (required): ID of the user.

**Response:** Same structure as `/user/listings`

---

## 🔄 Matching Endpoints

### POST `/api/matching/run-pipeline`
Run the complete unified matching pipeline for a specific user or all active users.

**Headers:** `Authorization: Bearer <access_token>` (optional, if `user_id` is specified)

**Request Body:**
```json
{
  "user_id": null
}
```

**Parameters:**
- `user_id` (optional): If provided, only match this user. If null, match all active users.

**Response (200 OK):**
```json
{
  "bilateral_matches": 3,
  "exchange_chains": 2,
  "total_participants": 8,
  "errors": []
}
```

---

### GET `/api/matching/status`
Get status of the last matching run.

**Response (200 OK):**
```json
{
  "last_run": "2025-01-15T12:00:00",
  "bilateral_matches": 15,
  "chains_discovered": 5,
  "participants_notified": 38,
  "status": "success"
}
```

---

### POST `/api/matching/test-flow`
Test the matching flow with sample data (for development and debugging).

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

**Response (200 OK):**
```json
{
  "test": "bilateral",
  "passed": true,
  "matches_found": 2,
  "details": "Alice + Bob match successful"
}
```

---

## 🔗 Exchange Chains Endpoints

### POST `/api/chains/discover`
Manually trigger chain discovery.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "min_participants": 3,
  "max_participants": 10
}
```

**Response (200 OK):**
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

---

### GET `/api/chains/all`
Get all discovered exchange chains.

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

---

### GET `/api/chains/user/{user_id}`
Get all chains for a specific user.

**Response:** Same as above

---

### POST `/api/chains/{chain_id}/accept`
User accepts a proposed chain.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "user_id": 1
}
```

**Response (200 OK):**
```json
{
  "chain_id": 1,
  "user_id": 1,
  "status": "accepted",
  "message": "You've accepted this exchange chain"
}
```

---

### POST `/api/chains/{chain_id}/decline`
User declines a proposed chain.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "user_id": 1,
  "reason": "Не подходит по времени"
}
```

**Response (200 OK):**
```json
{
  "chain_id": 1,
  "user_id": 1,
  "status": "declined",
  "message": "You've declined this exchange chain"
}
```

---

## 📲 Notifications Endpoints

### GET `/api/notifications/`
Get pending notifications for a user.

**Query Parameters:**
- `user_id` (required) - User ID
- `status` (optional): `pending`, `read`, `all`

**Response (200 OK):**
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

---

### POST `/api/notifications/{notification_id}/read`
Mark notification as read.

**Response (200 OK):**
```json
{
  "notification_id": 1,
  "status": "read"
}
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
curl "https://assistance-kz.ru/api/listings/wants?skip=20&limit=10&sort=created&order=desc"
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
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Conflict (e.g., duplicate username)
- `500 Internal Server Error` - Server error

---

## 🚀 Testing Endpoints with curl

### Complete User Flow Example

```bash
# 1. Register user
REGISTER_RESPONSE=$(curl -s -X POST https://assistance-kz.ru/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser_auth@example.com",
    "password": "SecurePass123!",
    "username": "testuser_auth",
    "full_name": "Test User Auth",
    "city": "Алматы"
  }' \
  -c /tmp/cookies.txt \
  -b /tmp/cookies.txt)
USER_ID=$(echo $REGISTER_RESPONSE | jq -r '.id')
echo "Registered User ID: $USER_ID"

# 2. Login user
LOGIN_RESPONSE=$(curl -s -X POST https://assistance-kz.ru/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser_auth",
    "password": "SecurePass123!"
  }' \
  -c /tmp/cookies.txt \
  -b /tmp/cookies.txt)
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Access Token: $ACCESS_TOKEN"

# 3. Create listings with authenticated user
curl -X POST https://assistance-kz.ru/api/listings/create-by-categories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "wants": {
      "PERMANENT": [
        { "item_name": "Книга по JS", "value_tenge": 10000 }
      ]
    },
    "offers": {
      "TEMPORARY": [
        { "item_name": "Электросамокат", "value_tenge": 5000, "duration_days": 2 }
      ]
    }
  }'

# 4. Access user cabinet
curl -s https://assistance-kz.ru/user/cabinet \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 5. Logout
curl -X POST https://assistance-kz.ru/auth/logout \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -c /tmp/cookies.txt \
  -b /tmp/cookies.txt

rm /tmp/cookies.txt
```

---

## 📊 API Metrics

| Metric | Value |
|--------|-------|
| Total Endpoints | 37 |
| Response Time | < 200ms |
| Max Page Size | 100 |
| Default Page Size | 20 |
| Timeout | 30s |

---

**For more details, see [docs/ARCHITECTURE.md](./ARCHITECTURE.MD) or [docs/TESTING.md](./TESTING.MD)**

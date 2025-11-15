# 📡 FreeMarket API Reference

**Version:** 2.2 (Personal Cabinet, Communications & Moderation) | **Last Updated:** November 2025

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
| **Exchange Confirmation** | 2 | ✅ Active |
| **Notifications** | 2 | ✅ Active |
| **Chat (Real-Time)** | 3 | ✅ Active |
| **Reviews & Trust** | 3 | ✅ Active |
| **Moderation & Safety** | 4 | ✅ Active |
| **Server-Sent Events** | 1 | ✅ Active |
| **Exchange History** | 3 | ✅ Active |
| **TOTAL** | **44** | ✅ Ready |

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
Register a new user with email, password, and optional profile details. Returns JWT tokens for automatic login after registration.

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

**Response (200 OK):**
```json
{
  "user": {
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
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Note:** 
- The refresh token is automatically set as an HttpOnly cookie
- User is automatically logged in after registration
- Store the `access_token` in localStorage for subsequent requests

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
Get the profile of the currently authenticated user. Always returns 200 status code to avoid console errors.

**Headers:** `Authorization: Bearer <access_token>` (optional - if not provided, returns authenticated: false)

**Response (200 OK) - Authenticated:**
```json
{
  "user": {
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
  },
  "authenticated": true
}
```

**Response (200 OK) - Not Authenticated:**
```json
{
  "user": null,
  "authenticated": false
}
```

**Note:** This endpoint always returns 200 status code to prevent console errors. Check the `authenticated` field to determine authentication status.

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

## 🔄 **Incremental Updates & Exchange Management**

### **PATCH `/listings/{listing_id}` - Partial Listing Updates**

Partially update a user listing with incremental matching support. Supports adding/removing items without full replacement.

**Authorization:** Required (user_id query parameter)

**Request Body:**
```json
{
  "wants": {
    "electronics": [
      {
        "item_name": "iPad Pro",
        "value_tenge": 400000,
        "exchange_type": "PERMANENT",
        "description": "Хочу планшет для работы"
      }
    ],
    "transport": [
      {
        "item_name": "аренда велосипеда",
        "value_tenge": 25000,
        "exchange_type": "TEMPORARY",
        "duration_days": 14,
        "description": "Нужен на выходные"
      }
    ]
  },
  "offers": {
    "books": [
      {
        "item_name": "учебники по Python",
        "value_tenge": 15000,
        "exchange_type": "PERMANENT",
        "description": "Книги в хорошем состоянии"
      }
    ]
  },
  "remove_items": [456, 789]
}
```

**Response:**
```json
{
  "status": "success",
  "listing_id": 123,
  "user_id": 1,
  "items_added": 3,
  "items_removed": 2,
  "current_counts": {
    "wants": 5,
    "offers": 8
  },
  "message": "Listing updated successfully with incremental matching triggered"
}
```

**Features:**
- ✅ Atomic transactions
- ✅ Automatic match index updates
- ✅ Event-driven incremental matching
- ✅ Validation of all items
- ✅ Rate limiting (prevents spam)

**Example:**
```bash
curl -X PATCH "https://assistance-kz.ru/api/listings/123?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "wants": {"electronics": [{"item_name": "MacBook", "value_tenge": 600000}]},
    "remove_items": [456]
  }'
```

---

### **POST `/exchanges/{exchange_id}/confirm` - Confirm Exchange Completion**

Confirm successful exchange completion with automatic cleanup of exchanged items.

**Authorization:** Required (confirmer_user_id query parameter)

**URL Parameters:**
- `exchange_id`: Exchange identifier (format: `mutual_{user_a}_{user_b}_{item_a}_{item_b}`)

**Query Parameters:**
- `confirmer_user_id`: ID of user confirming the exchange

**Response:**
```json
{
  "status": "success",
  "exchange_id": "mutual_1_2_10_15",
  "confirmed_by": 1,
  "participants": [1, 2],
  "items_archived": [10, 15],
  "message": "Exchange confirmed and items automatically cleaned up from listings"
}
```

**Automatic Actions:**
- ✅ Validates exchange participants and items
- ✅ Soft-deletes exchanged items (`is_archived = true`)
- ✅ Emits profile change events for both users
- ✅ Triggers incremental match recalculation
- ✅ Sends completion notifications to both participants

**Security:**
- User must be a participant in the exchange
- Items must exist and not already archived
- Atomic transaction ensures consistency

**Example:**
```bash
curl -X POST "https://assistance-kz.ru/api/exchanges/mutual_1_2_10_15/confirm?confirmer_user_id=1"
```

---

## 💬 **Chat Endpoints**

### WebSocket `/ws/exchange/{exchange_id}`

Real-time chat for exchanges with message delivery guarantees.

**Authorization:** Required (JWT token in query parameter)

**Path Parameters:**
- `exchange_id` (required): Exchange identifier (format: `mutual_{user_a}_{user_b}_{item_a}_{item_b}`)

**Query Parameters:**
- `token`: JWT access token

**Protocol:**
```javascript
// Connect
const ws = new WebSocket('wss://assistance-kz.ru/ws/exchange/mutual_1_2_10_15?token=your_jwt_token');

// Send message
ws.send(JSON.stringify({
  type: 'message',
  text: 'Hello, let's meet tomorrow!',
  message_type: 'TEXT'
}));

// Receive messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New message:', data);
};
```

**Message Types:**
- `TEXT` - Text messages
- `IMAGE` - Image attachments
- `SYSTEM` - System notifications

---

### GET `/api/chat/exchange/{exchange_id}/history`

Get chat history for an exchange.

**Authorization:** Required

**Path Parameters:**
- `exchange_id` (required): Exchange identifier

**Query Parameters:**
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Number of messages (default: 50, max: 100)

**Response (200 OK):**
```json
{
  "messages": [
    {
      "id": 1,
      "exchange_id": "mutual_1_2_10_15",
      "sender_id": 1,
      "message_text": "Hello!",
      "message_type": "TEXT",
      "is_read": true,
      "delivered_at": "2025-11-07T10:00:00Z",
      "read_at": "2025-11-07T10:01:00Z",
      "created_at": "2025-11-07T10:00:00Z"
    }
  ],
  "total": 1,
  "unread_count": 0
}
```

---

### GET `/api/chat/unread-counts`

Get unread message counts for all user's exchanges.

**Authorization:** Required

**Response (200 OK):**
```json
{
  "total_unread": 3,
  "exchanges": {
    "mutual_1_2_10_15": 2,
    "mutual_3_4_20_25": 1
  }
}
```

---

### POST `/api/chat/exchange/{exchange_id}/mark-read`

Mark all messages in an exchange as read.

**Authorization:** Required

**Path Parameters:**
- `exchange_id` (required): Exchange identifier

**Response (200 OK):**
```json
{
  "marked_read": 2,
  "exchange_id": "mutual_1_2_10_15"
}
```

---

## 🔔 **Server-Sent Events**

### GET `/api/events/stream`

Real-time event stream for notifications and updates.

**Authorization:** Required (JWT token)

**Response:** Server-sent events stream

**Event Types:**
```javascript
// Connect
const eventSource = new EventSource('/api/events/stream', {
  headers: { 'Authorization': 'Bearer ' + token }
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data);
};

// Example events
{
  "type": "message_received",
  "exchange_id": "mutual_1_2_10_15",
  "sender_name": "John Doe",
  "preview": "Hi, let's meet..."
}

{
  "type": "notification_new",
  "notification_id": 123,
  "title": "New match found!",
  "message": "You have a new potential exchange"
}
```

---

## ⭐ **Reviews & Trust Endpoints**

### POST `/api/reviews`

Create a review for a completed exchange.

**Authorization:** Required

**Request Body:**
```json
{
  "exchange_id": "mutual_1_2_10_15",
  "target_user_id": 2,
  "rating": 5,
  "text": "Great exchange, very reliable partner!",
  "is_public": true
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "author_id": 1,
  "target_id": 2,
  "exchange_id": "mutual_1_2_10_15",
  "rating": 5,
  "text": "Great exchange, very reliable partner!",
  "is_public": true,
  "created_at": "2025-11-07T12:00:00Z"
}
```

**Anti-Spam Controls:**
- Maximum 1 review per exchange per user
- Rate limited: 5 reviews per hour per user
- Reviews only allowed after exchange confirmation

---

### GET `/api/reviews/users/{user_id}`

Get reviews for a specific user.

**Authorization:** Required

**Path Parameters:**
- `user_id` (required): User ID to get reviews for

**Query Parameters:**
- `skip` (optional): Pagination offset
- `limit` (optional): Number of reviews (default: 10, max: 50)

**Response (200 OK):**
```json
{
  "reviews": [
    {
      "id": 1,
      "author_name": "Anonymous",
      "rating": 5,
      "text": "Great exchange!",
      "created_at": "2025-11-07T12:00:00Z",
      "is_verified": true
    }
  ],
  "summary": {
    "average_rating": 4.8,
    "total_reviews": 25,
    "verified_reviews": 20
  }
}
```

---

### GET `/api/reviews/users/{user_id}/rating`

Get user's trust rating and analytics.

**Authorization:** Required

**Path Parameters:**
- `user_id` (required): User ID

**Response (200 OK):**
```json
{
  "user_id": 123,
  "average_rating": 4.7,
  "total_reviews": 15,
  "verified_reviews": 12,
  "trust_score": 85.5,
  "weighted_rating": 4.6,
  "exchanges_completed": 18,
  "last_calculated": "2025-11-07T12:00:00Z"
}
```

**Trust Score Calculation:**
- Base: Average rating (weighted by recency)
- Bonus: High completion rate (+10%)
- Penalty: Reports received (-5% per report)
- Account age bonus (+5% for accounts > 6 months)

---

## 🚨 **Moderation & Safety Endpoints**

### POST `/api/reports`

Submit a complaint about a listing or user.

**Authorization:** Required

**Request Body:**
```json
{
  "target_listing_id": 123,
  "target_user_id": null,
  "reason": "PRICE_MISMATCH",
  "description": "Item price doesn't match market value",
  "evidence_urls": ["https://example.com/photo.jpg"]
}
```

**Reason Options:**
- `PRICE_MISMATCH` - Price doesn't match value
- `UNAVAILABLE_ITEM` - Item not available
- `FAKE_LISTING` - Fake or misleading listing
- `INAPPROPRIATE_CONTENT` - Offensive content
- `SPAM` - Spam or harassment
- `FRAUD` - Suspected fraud
- `OTHER` - Other issues

**Response (201 Created):**
```json
{
  "id": 1,
  "reporter_id": 456,
  "target_listing_id": 123,
  "reason": "PRICE_MISMATCH",
  "status": "PENDING",
  "created_at": "2025-11-07T13:00:00Z",
  "estimated_resolution": "2025-11-10T13:00:00Z"
}
```

---

### GET `/api/admin/reports`

Admin endpoint to view reports (admin only).

**Authorization:** Required (admin role)

**Query Parameters:**
- `status` (optional): Filter by status (`PENDING`, `UNDER_REVIEW`, `RESOLVED`)
- `skip` (optional): Pagination offset
- `limit` (optional): Number of reports (default: 20)

**Response (200 OK):**
```json
{
  "reports": [
    {
      "id": 1,
      "reporter_name": "John Doe",
      "target_listing_title": "iPhone for exchange",
      "reason": "PRICE_MISMATCH",
      "status": "PENDING",
      "created_at": "2025-11-07T13:00:00Z",
      "priority": "MEDIUM"
    }
  ],
  "total": 1
}
```

---

### POST `/api/admin/reports/{report_id}/resolve`

Resolve a report (admin only).

**Authorization:** Required (admin role)

**Path Parameters:**
- `report_id` (required): Report ID

**Request Body:**
```json
{
  "resolution": "LISTING_REMOVED",
  "admin_notes": "Listing removed due to price mismatch",
  "actions_taken": ["hide_listing", "notify_user"]
}
```

**Resolution Options:**
- `LISTING_REMOVED` - Listing hidden/removed
- `USER_WARNED` - User received warning
- `USER_BANNED` - User account banned
- `DISMISSED` - Report dismissed as invalid

**Response (200 OK):**
```json
{
  "report_id": 1,
  "status": "RESOLVED",
  "resolution": "LISTING_REMOVED",
  "resolved_at": "2025-11-07T14:00:00Z"
}
```

---

### POST `/api/admin/users/{user_id}/ban`

Ban a user account (admin only).

**Authorization:** Required (admin role)

**Path Parameters:**
- `user_id` (required): User ID to ban

**Request Body:**
```json
{
  "reason": "MULTIPLE_REPORTS",
  "duration_days": 30,
  "admin_notes": "Banned due to multiple price mismatch reports"
}
```

**Response (200 OK):**
```json
{
  "user_id": 123,
  "status": "BANNED",
  "ban_until": "2025-12-07T14:00:00Z",
  "reason": "MULTIPLE_REPORTS"
}
```

---

### GET `/api/admin/dashboard`

Get moderation statistics (admin only).

**Authorization:** Required (admin role)

**Response (200 OK):**
```json
{
  "stats": {
    "pending_reports": 12,
    "resolved_today": 8,
    "active_bans": 3,
    "hidden_listings": 15,
    "reports_by_reason": {
      "PRICE_MISMATCH": 5,
      "SPAM": 3,
      "FRAUD": 2
    }
  },
  "recent_activity": [
    {
      "type": "report_resolved",
      "report_id": 123,
      "timestamp": "2025-11-07T14:00:00Z"
    }
  ]
}
```

---

## 📜 **Exchange History Endpoints**

### GET `/api/history/my-exchanges`

Get user's exchange history with filters.

**Authorization:** Required

**Query Parameters:**
- `status` (optional): `COMPLETED`, `ACTIVE`, `CANCELLED`
- `skip` (optional): Pagination offset
- `limit` (optional): Number of exchanges (default: 20)

**Response (200 OK):**
```json
{
  "exchanges": [
    {
      "id": "mutual_1_2_10_15",
      "partner_name": "Jane Smith",
      "partner_rating": 4.8,
      "status": "COMPLETED",
      "items": ["iPad Pro", "MacBook lessons"],
      "completed_at": "2025-11-05T10:00:00Z",
      "rating_given": 5,
      "review_text": "Great exchange!"
    }
  ],
  "total": 1,
  "filters_applied": ["status:COMPLETED"]
}
```

---

### GET `/api/history/exchanges/{exchange_id}`

Get detailed history for a specific exchange (participants only).

**Authorization:** Required (must be participant)

**Path Parameters:**
- `exchange_id` (required): Exchange identifier

**Response (200 OK):**
```json
{
  "exchange_id": "mutual_1_2_10_15",
  "participants": [
    {"user_id": 1, "name": "John Doe", "role": "initiator"},
    {"user_id": 2, "name": "Jane Smith", "role": "partner"}
  ],
  "timeline": [
    {
      "event_type": "CREATED",
      "timestamp": "2025-11-01T10:00:00Z",
      "details": "Exchange created via matching"
    },
    {
      "event_type": "MESSAGE_SENT",
      "timestamp": "2025-11-01T10:30:00Z",
      "details": "First contact message"
    },
    {
      "event_type": "CONFIRMED",
      "timestamp": "2025-11-03T14:00:00Z",
      "details": "Exchange confirmed by both parties"
    },
    {
      "event_type": "COMPLETED",
      "timestamp": "2025-11-05T10:00:00Z",
      "details": "Items exchanged successfully"
    }
  ],
  "final_rating": 5,
  "review_count": 2
}
```

---

### GET `/api/history/my-exchanges/export`

Export user's exchange history in various formats.

**Authorization:** Required

**Query Parameters:**
- `format` (optional): `JSON`, `CSV` (default: `JSON`)
- `start_date` (optional): Filter from date (ISO format)
- `end_date` (optional): Filter to date (ISO format)

**Response:** File download

**CSV Format:**
```csv
exchange_id,partner_name,status,completed_at,rating_given,items
mutual_1_2_10_15,Jane Smith,COMPLETED,2025-11-05T10:00:00Z,5,"iPad Pro, MacBook lessons"
```

---

## 📊 **API Statistics**

| Metric | Value |
|--------|-------|
| Total Endpoints | 44 |
| Response Time | < 200ms |
| Max Page Size | 100 |
| Default Page Size | 20 |
| Timeout | 30s |

---

**For more details, see [docs/ARCHITECTURE.md](./ARCHITECTURE.MD) or [docs/TESTING.md](./TESTING.MD)**

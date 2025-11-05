# 🏛️ FreeMarket System Architecture

**Version:** 2.0 - Категории v6, JWT-аутентификация, Nginx
**Last Updated:** Ноябрь 2025
**Status:** ✅ Production Ready

---

## 📖 **Table of Contents**

1. [Project Overview](#project-overview)
2. [Категории v6, JWT-аутентификация и Nginx](#categories-v6-jwt-nginx)
3. [User Journey](#user-journey)
4. [System Architecture (7 Layers)](#system-architecture-7-layers)
5. [Data Model](#data-model)
6. [Category Matching Engine](#category-matching-engine)
7. [API Endpoints](#api-endpoints)
8. [Telegram Integration](#telegram-integration)
9. [Database Schema](#database-schema)

---

## 🎯 **Project Overview**

**FreeMarket** - платформа для эквивалентного обмена ресурсами между пользователями.

### **Core Features:**
- ✅ **Category-based listings** - хочу/могу по 6 категориям
- ✅ **Smart matching** - находит пары по пересечению категорий и стоимости
- ✅ **Telegram notifications** - уведомления о совпадениях
- ✅ **Personal cabinet** - просмотр совпадений на сайте
- ✅ **Location filtering** - фильтр по городам (Алматы, Астана, Шымкент)
- ✅ **Chain matching** - поиск многосторонних обменов (3+ участников)
- ✅ **Категории v6** - новая, версионированная система категорий (Permanent/Temporary)
- ✅ **JWT-аутентификация** - безопасная аутентификация с refresh-токенами и Redis-ревокацией

---

## 🔄 **Категории v6, JWT-аутентификация и Nginx** {#categories-v6-jwt-nginx}

- **Система Категорий v6:** Введена новая, версионированная система категорий с таблицами `category_versions`, `categories_v6` и `category_mappings`. Это позволяет управлять эволюцией таксономии и обеспечивает корректную миграцию старых объявлений. Поддерживаются два основных типа обмена: `PERMANENT` (постоянный) и `TEMPORARY` (временный).
- **API Категорий:** Публичные эндпоинты `GET /v1/categories`, `GET /v1/categories/{exchange_type}` и `GET /v1/categories/groups/{exchange_type}` предоставляют доступ к категориям с учетом версии и типа обмена. Это используется для динамической генерации форм и валидации на фронтенде.
- **JWT Аутентификация:** Реализована безопасная JWT-аутентификация с использованием короткоживущих access-токенов и долгоживущих refresh-токенов. Refresh-токены хранятся в HttpOnly, Secure cookie и автоматически ротируются при каждом использовании. Система ревокации токенов через Redis обеспечивает возможность принудительного выхода из всех сессий пользователя.
- **Nginx Прокси:** Nginx настроен как обратный прокси-сервер, который корректно обрабатывает и перенаправляет запросы к бэкенд-сервисам FastAPI. Важно, что Nginx теперь правильно сохраняет префиксы URL (например, `/v1/`), обеспечивая корректную маршрутизацию API-запросов.

---

## 🔄 **User Journey**

```
STEP 1: Регистрация
  ├─ Ввести ФИО
  ├─ Ввести @telegram контакт
  ├─ Выбрать города (множественный выбор)
  └─ Сохранить telegram_id для уведомлений

STEP 2: Добавить объявления
  ├─ Левая колонка: ХОЧ У (Wants)
  │  ├─ 🏭 Техника (Электроника)
  │  ├─ 💰 Деньги (Услуги, аренда)
  │  ├─ 🛋️ Мебель
  │  ├─ 🚗 Транспорт
  │  ├─ 🔧 Услуги
  │  └─ 📦 Прочее
  │
  ├─ Правая колонка: МОГУ (Offers)
  │  └─ Те же категории
  │
  └─ Для каждого предмета: название, цена (₸), описание (опционально)

STEP 3: Система ищет совпадения
  ├─ Находит ПЕРЕСЕЧЕНИЯ категорий (категории, где одновременно есть want и offer)
  ├─ Проверяет эквивалентность по стоимости (±15%)
  ├─ Оценивает совпадение в каждой категории
  └─ Создаёт ФИЛЬТРОВАННЫЙ профиль партнёра (ТОЛЬКО пересекающиеся категории!)

STEP 4: Юзер получает уведомление
  ├─ Telegram-сообщение: "🎉 Совпадение найдено!"
  ├─ Детали совпадения по категориям
  ├─ Контакт партнера (@username)
  └─ Ссылка на кабинет на сайте

STEP 5: Кабинет на сайте
  ├─ Показывает все совпадения
  ├─ Для каждого совпадения:
  │  ├─ Список категорий с совпадениями
  │  ├─ Рейтинг совпадения (%)
  │  ├─ Кнопка "Написать в Telegram"
  │  └─ Кнопки "Принять" / "Отклонить"
  └─ Юзеры договариваются в Telegram

STEP 6: Договоренность & обмен
  └─ Юзеры связываются и договариваются о встрече/обмене
```

---

## 🏗️ **System Architecture (7 Layers)**

```
┌─────────────────────────────────────────────────────────┐
│ LAYER 1: UI/UX (React Two-Column Layout)               │
├─────────────────────────────────────────────────────────┤
│ Two-column form:                                        │
│ ├─ LEFT: Wants (ХОЧ У)                                 │
│ └─ RIGHT: Offers (МОГУ)                                │
│ Each with 6 categories + auto-calculated totals         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 2: Frontend Components (React)                    │
├─────────────────────────────────────────────────────────┤
│ ├─ CategoryListingsForm.jsx (main form)                │
│ ├─ CategoryTable.jsx (per-category tables)             │
│ ├─ CabinetPage.jsx (match display)                     │
│ └─ State management (wants/offers by category)          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 3: Validation (Pydantic Schemas)                 │
├─────────────────────────────────────────────────────────┤
│ ├─ ListingItemCreate (single item)                     │
│ │  ├─ item_name: str                                   │
│ │  ├─ value_tenge: int (>= 0)                          │
│ │  └─ description: Optional[str]                       │
│ │                                                       │
│ └─ ListingByCategories (full listing)                  │
│    ├─ wants: Dict[str, List[ListingItemCreate]]       │
│    ├─ offers: Dict[str, List[ListingItemCreate]]      │
│    └─ locations: Optional[List[str]]                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 4: API Endpoints (FastAPI)                       │
├─────────────────────────────────────────────────────────┤
│ POST /api/listings/by-categories                       │
│   ├─ Save listing with categorized items              │
│   └─ Return: id, totals, wants_by_category, etc.      │
│                                                        │
│ POST /api/matching/find-matches                        │
│   ├─ Find matches by category intersection            │
│   └─ Return: filtered listings (ONLY matches!)        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 5: Database Models (SQLAlchemy)                  │
├─────────────────────────────────────────────────────────┤
│ Listing (1:many)                                       │
│   └─ items: List[ListingItem]                          │
│                                                        │
│ ListingItem (normalized)                               │
│   ├─ item_type: Enum (want, offer)                    │
│   ├─ category: str (electronics, money, etc.)         │
│   ├─ item_name: str(100)                              │
│   ├─ value_tenge: int                                 │
│   └─ description: str(500)                            │
│                                                        │
│ Indexes:                                               │
│   ├─ (listing_id, category)                           │
│   └─ (category, value_tenge)                          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 6: Matching Engine (KEY!)                        │
├─────────────────────────────────────────────────────────┤
│ CategoryMatchingEngine:                                 │
│                                                        │
│ 1. Find MY categories                                  │
│    └─ Categories where I have wants OR offers         │
│                                                        │
│ 2. For each other user:                               │
│    ├─ Find INTERSECTING categories                    │
│    └─ Skip if no intersection                         │
│                                                        │
│ 3. For each intersecting category:                    │
│    ├─ Check value equivalence (±15%)                  │
│    ├─ Calculate score (0.0-1.0)                       │
│    └─ If score >= 0.70 → add to matches               │
│                                                        │
│ 4. Create FILTERED listing:                           │
│    ├─ ONLY include intersecting categories            │
│    ├─ ONLY include matching items                     │
│    └─ Mark reasons (i see this, you want that)        │
│                                                        │
│ 5. Return sorted matches (highest score first)        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 7: Notifications (Telegram Bot)                  │
├─────────────────────────────────────────────────────────┤
│ Send beautiful Telegram message:                        │
│ ├─ Overall match score (%)                            │
│ ├─ Per-category breakdown                             │
│ ├─ Partner's intersecting categories only             │
│ ├─ Contact info + cabinet link                        │
│ └─ Buttons: Message, Accept, Decline                  │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 **Data Model**

### **Normalized Schema:**

```
users
  ├─ id (PK)
  ├─ username (unique)
  ├─ contact (@telegram username)
  ├─ telegram_id (for Bot API)
  ├─ locations (ARRAY: Алматы, Астана, Шымкент)
  └─ created_at

listings
  ├─ id (PK)
  ├─ user_id (FK → users)
  ├─ created_at
  └─ updated_at

listing_items (normalized!)
  ├─ id (PK)
  ├─ listing_id (FK → listings)
  ├─ item_type (want | offer)
  ├─ category (electronics | money | furniture | transport | services | other)
  ├─ item_name (VARCHAR 100)
  ├─ value_tenge (INTEGER)
  ├─ description (TEXT, optional)
  └─ created_at

matches
  ├─ id (PK)
  ├─ user_a_id (FK → users)
  ├─ user_b_id (FK → users)
  ├─ overall_score (FLOAT: 0.0-1.0)
  ├─ matching_categories (JSON: ["electronics", "money"])
  ├─ category_scores (JSON: {electronics: 0.92, money: 1.0})
  ├─ filtered_partner_listing (JSON: ONLY intersecting items!)
  ├─ created_at
  └─ status (proposed | accepted_a | accepted_b | matched | rejected)

notifications
  ├─ id (PK)
  ├─ user_id (FK → users)
  ├─ payload (JSON: match details + telegram details)
  ├─ is_sent (BOOLEAN)
  └─ created_at
```

---

## 🧠 **Category Matching Engine**

### **Algorithm (CategoryMatchingEngine class):**

```python
def find_matches_for_user(user_id):
    # STEP 1: Get my categories
    my_listing = get_latest_listing(user_id)
    my_categories = {all categories where I have wants OR offers}

    # STEP 2: For each other user
    for other_user in all_users:
        other_listing = get_latest_listing(other_user.id)
        other_categories = {their categories}

        # STEP 3: Find INTERSECTING categories
        intersecting_cats = my_categories ∩ other_categories
        if not intersecting_cats:
            continue  # Skip - no matches possible

        # STEP 4: Score each intersecting category
        category_scores = {}
        category_matches = {}

        for category in intersecting_cats:
            score = score_category_match(my_listing, other_listing, category)

            if score >= 0.70:  # Min threshold
                category_scores[category] = score
                category_matches[category] = {
                    my_wants: [...],
                    my_offers: [...],
                    their_wants: [...],
                    their_offers: [...]
                }

        if category_matches:
            # STEP 5: Create filtered listing
            overall_score = average(category_scores.values())
            filtered_listing = create_filtered_listing(
                other_listing,
                category_matches  # ONLY these categories!
            )

            matches.append({
                user_id: other_user.id,
                overall_score: overall_score,
                matching_categories: list(category_matches.keys()),
                category_scores: category_scores,
                filtered_partner_listing: filtered_listing
            })

    # Sort by overall_score (highest first)
    return sorted(matches, key=lambda x: x['overall_score'], reverse=True)
```

### **Category Scoring:**

```
For each category:
  my_wants_value = sum(wants in this category)
  my_offers_value = sum(offers in this category)

  their_wants_value = sum(their wants in this category)
  their_offers_value = sum(their offers in this category)

  Check equivalence:
    my_wants (e.g., 120k) ≈ their_offers (e.g., 150k)? → within ±15%? ✓
    my_offers (e.g., 150k) ≈ their_wants (e.g., 120k)? → within ±15%? ✓

  Calculate score:
    wants_diff = |my_wants - their_offers| / max(my_wants, their_offers)
    offers_diff = |my_offers - their_wants| / max(my_offers, their_wants)
    category_score = 1.0 - average(wants_diff, offers_diff)

  If category_score >= 0.70 → MATCH!
```

---

## 📡 **API Endpoints (22 Total)**

### **Category-Based Listings:**

```
POST /api/listings/by-categories
  Body: {
    user_id: 1,
    wants: {
      electronics: [{item_name, value_tenge, description}],
      money: [...],
      furniture: [...]
    },
    offers: { ... },
    locations: ["Алматы", "Астана"]
  }

  Response: {
    id: 1,
    user_id: 1,
    wants_by_category: { electronics: [...], ... },
    offers_by_category: { ... },
    total_wants_value: { electronics: 120000, money: 100000, ... },
    total_offers_value: { ... },
    created_at: "2025-01-15T12:00:00Z"
  }
```

### **Matching:**

```
POST /api/matching/find-matches?user_id=1

  Response: {
    user_id: 1,
    matches_found: 3,
    matches: [
      {
        user_id: 2,
        username: "bob",
        contact: "@bob",
        overall_score: 0.93,
        matching_categories: ["electronics", "money"],
        category_scores: {
          electronics: 0.92,
          money: 1.00
        },
        filtered_partner_listing: {
          electronics: {
            their_wants: [...],
            their_offers: [...]
          },
          money: { ... }
        }
      }
    ]
  }
```

### **Complete API (22 endpoints):**

See [API_REFERENCE.md](./API_REFERENCE.md) for full list and examples.

---

## 🤖 **Telegram Integration**

### **When Match is Found:**

1. **MatchingEngine** finds match
2. **Calls** `send_match_notification(user_telegram_id, match_info)`
3. **Bot** sends beautiful Telegram message:

```
🎉 СОВПАДЕНИЕ НАЙДЕНО!

👤 Партнер: @bob
📊 Общая оценка: 93%

✅ СОВПАДЕНИЯ ПО КАТЕГОРИЯМ:

🏭 ТЕХНИКА (Оценка: 92%)
   Партнер ищет:
   • Смартфон - 50,000 ₸  ← Вы можете дать!

   Партнер предлагает:
   • Велосипед - 50,000 ₸  ← Вы это ищете!

💰 ДЕНЬГИ (Оценка: 100% PERFECT!)
   Партнер ищет:
   • Депозит - 100,000 ₸  ← Вы можете!

   Партнер предлагает:
   • Аренда - 100,000 ₸  ← Вам нужна!

❌ КАТЕГОРИИ БЕЗ СОВПАДЕНИЙ:
   • 🛋️ Мебель (у партнёра нет нужных)
   • 🚗 Транспорт (у вас нет нужных)

💬 [Написать в Telegram] [✓ Принять] [✕ Отклонить]
```

### **Key Telegram Features:**
- ✅ **Formatted message** - HTML with emojis
- ✅ **Filtered info** - ONLY matching categories shown!
- ✅ **Interactive** - buttons for actions
- ✅ **Cabinet link** - redirect to website
- ✅ **Dual notification** - both users get message

---

## 🗄️ **Database Schema**

```sql
-- Users with Telegram integration
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR UNIQUE NOT NULL,
  contact VARCHAR,
  telegram_id INTEGER UNIQUE,
  telegram_username VARCHAR,
  locations ARRAY VARCHAR,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Listings by category
CREATE TABLE listings (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP
);

-- Normalized items (per category)
CREATE TABLE listing_items (
  id SERIAL PRIMARY KEY,
  listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  item_type VARCHAR NOT NULL,  -- 'want' | 'offer'
  category VARCHAR NOT NULL,  -- 'electronics', 'money', etc.
  item_name VARCHAR(100) NOT NULL,
  value_tenge INTEGER NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),

  INDEX (listing_id, category),
  INDEX (category, value_tenge)
);

-- Matches with filtered listings
CREATE TABLE matches (
  id SERIAL PRIMARY KEY,
  user_a_id INTEGER NOT NULL REFERENCES users(id),
  user_b_id INTEGER NOT NULL REFERENCES users(id),
  overall_score FLOAT NOT NULL,
  matching_categories JSON,  -- ["electronics", "money"]
  category_scores JSON,  -- {electronics: 0.92, money: 1.0}
  filtered_partner_listing JSON,  -- ONLY intersecting items!
  created_at TIMESTAMP DEFAULT NOW(),
  status VARCHAR DEFAULT 'proposed'
);
```

---

## 🔗 **Complete Flow Diagram**

```
USER REGISTRATION
  └─ ФИО + @telegram + города → Save telegram_id

STEP 1: ADD LISTINGS
  ├─ Left column: Wants by categories
  └─ Right column: Offers by categories

        ↓ POST /api/listings/by-categories

STEP 2: SAVE TO DB (Normalized)
  ├─ listings table (1 record per user)
  └─ listing_items table (many records)
      └─ Each item: type + category + value

        ↓ POST /api/matching/find-matches

STEP 3: CATEGORY MATCHING ENGINE
  ├─ Get my categories
  ├─ For each user: find intersecting categories
  ├─ Score each intersection
  └─ Create filtered listings

        ↓

STEP 4: SEND TELEGRAM
  ├─ Format beautiful message
  ├─ ONLY show intersecting categories
  └─ Send to user's telegram_id

        ↓

STEP 5: CABINET
  ├─ GET /api/notifications?user_id=X
  ├─ Display all matches
  ├─ Show filtered partner info
  └─ Buttons: Message, Accept, Decline

        ↓

STEP 6: CONNECT
  └─ Users message in Telegram & exchange
```

---

## ✨ **Key Innovations**

1. **Category Intersection** - Only match on shared categories
2. **Filtered Listings** - Show only what matters to user
3. **Normalized Data** - Easy to query & extend
4. **Dual Notifications** - Telegram + Cabinet
5. **Value Equivalence** - Fair exchanges within ±15%
6. **Telegram Integration** - Contact info immediately available

---

**For detailed information, see:**
- [API_REFERENCE.md](./API_REFERENCE.md) - All 22 endpoints
- [TESTING.md](./TESTING.md) - 7 test scenarios
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Production setup


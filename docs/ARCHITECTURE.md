# 🏛️ FreeMarket System Architecture

**Version:** 2.2 - Personal Cabinet, Real-Time Communications & Moderation
**Last Updated:** Ноябрь 2025
**Status:** ✅ Production Ready with Full User Experience

---

## 📖 **Table of Contents**

1. [Project Overview](#project-overview)
2. [Категории v6, JWT-аутентификация и Nginx](#categories-v6-jwt-nginx)
3. [User Journey](#user-journey)
4. [System Architecture (7 Layers)](#system-architecture-7-layers)
5. [Real-Time Layer](#real-time-layer)
6. [Notification & Review Stream](#notification--review-stream)
7. [Complaint & Moderation Subsystem](#complaint--moderation-subsystem)
8. [Incremental Matching System](#incremental-matching-system)
9. [Data Model](#data-model)
10. [Category Matching Engine](#category-matching-engine)
11. [API Endpoints](#api-endpoints)
12. [Telegram Integration](#telegram-integration)
13. [Database Schema](#database-schema)

---

## 🎯 **Project Overview**

**FreeMarket** - платформа для эквивалентного обмена ресурсами между пользователями.

### **Core Features:**
- ✅ **Category-based listings** - хочу/могу по 6 категориям
- ✅ **Smart matching** - находит пары по пересечению категорий и стоимости
- ✅ **Telegram notifications** - уведомления о совпадениях
- ✅ **Personal cabinet** - полный дашборд пользователя с историей
- ✅ **Location filtering** - фильтр по городам (Алматы, Астана, Шымкент)
- ✅ **Chain matching** - поиск многосторонних обменов (3+ участников)
- ✅ **Категории v6** - новая, версионированная система категорий (Permanent/Temporary)
- ✅ **JWT-аутентификация** - безопасная аутентификация с refresh-токенами и Redis-ревокацией
- ✅ **Real-Time Chat** - WebSocket чат с гарантией доставки сообщений
- ✅ **Live Notifications** - SSE стримы для мгновенных обновлений
- ✅ **Review & Trust System** - система отзывов с анти-спам контролем
- ✅ **Moderation & Safety** - автоматическая модерация жалоб с эскалацией
- ✅ **Incremental Matching** - событийно-ориентированные обновления матчинга

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

## 💬 **Real-Time Layer**

### **WebSocket Chat System**

**Architecture:**
- **Separate Gateway Container** (`freemarket-ws`) - изолированный WebSocket сервер для лучшей масштабируемости
- **Connection Management** - JWT аутентификация при подключении, автоматическое отключение неактивных соединений
- **Message Delivery Guarantees** - Redis TTL-кэш для сообщений, повторная доставка при сбое WebSocket
- **Pub/Sub Broadcasting** - Redis Pub/Sub для широковещательной рассылки сообщений всем участникам обмена

**Protocol:**
```javascript
// Client connects with JWT token
const ws = new WebSocket('wss://api.freemarket.kz/ws/exchange/mutual_1_2_10_15?token=jwt_token');

// Server validates token and exchange participation
// Messages are delivered with timestamps and read receipts
```

**Features:**
- **Delivery Tracking** - `delivered_at`, `read_at` timestamps для гарантии доставки
- **Redis TTL Cache** - последние сообщения кэшируются для восстановления после переподключения
- **Rate Limiting** - ограничение частоты отправки сообщений (Redis-based)
- **Connection Pooling** - эффективное управление множественными соединениями

### **Server-Sent Events (SSE)**

**Architecture:**
- **Event Stream Endpoint** (`/api/events/stream`) - односторонний поток событий от сервера
- **Redis Streams** - journaling и replay для надежности
- **Consumer Groups** - масштабируемая обработка событий
- **Last Events Cache** - Redis JSON кэш последних событий для быстрой инициализации клиента

**Event Types:**
```json
{
  "type": "message_received",
  "exchange_id": "mutual_1_2_10_15",
  "sender_name": "John Doe",
  "preview": "Hi, let's meet...",
  "timestamp": "2025-11-07T10:00:00Z"
}

{
  "type": "notification_new",
  "notification_id": 123,
  "title": "New match found!",
  "message": "You have a new potential exchange",
  "priority": "high"
}
```

---

## 🔔 **Notification & Review Stream**

### **Notification System**

**Architecture:**
- **UserEvent Model** - структурированные события для каждого пользователя
- **SSE Stream** - реальное время без постоянного polling
- **Event Types** - стандартизированные типы событий (MESSAGE_RECEIVED, OFFER_MATCHED, EXCHANGE_COMPLETED, etc.)
- **Push Notifications** - интеграция с Firebase Cloud Messaging для мобильных устройств

**Event Flow:**
```
User Action → Event Creation → Redis Stream → SSE Broadcast → UI Update
```

### **Review & Trust Analytics**

**Trust Score Calculation:**
```
Base Score = Average Rating (weighted by recency)
Completion Bonus = +10% for high completion rate
Account Age Bonus = +5% for accounts > 6 months
Report Penalty = -5% per received report

Final Trust Score = Base + Bonuses - Penalties
```

**Anti-Spam Controls:**
- Rate limiting: 5 reviews per hour per user
- One review per exchange per user
- Reviews only after exchange confirmation
- Suspicious patterns detection

**Redis Caching:**
- User ratings cached for 1 hour
- Trust scores recalculated daily
- Recent reviews cached for fast retrieval

---

## 🚨 **Complaint & Moderation Subsystem**

### **Auto-Moderation Pipeline**

**Report Processing:**
```
User Report → Redis Stream → Background Worker → Auto-Analysis → Admin Queue
```

**Auto-Escalation Rules:**
- 3+ reports on listing → auto-hide
- 5+ reports on user → auto-ban (7 days)
- Fraud reports → immediate admin review
- Spam patterns → account suspension

**Admin Dashboard:**
- Real-time report queue
- Moderation statistics
- Bulk actions support
- Audit trail logging

### **Safety Features**

**Content Moderation:**
- Automated spam detection
- Image analysis for inappropriate content
- Pattern matching for fraud indicators
- User behavior analytics

**Account Protection:**
- Progressive penalties (warning → ban)
- Appeal mechanisms
- Account recovery procedures
- Data export on account deletion

---

## 🤖 **Incremental Matching System**

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

user_events (NEW!)
  ├─ id (PK)
  ├─ user_id (FK → users)
  ├─ event_type (MESSAGE_RECEIVED, OFFER_MATCHED, EXCHANGE_COMPLETED, etc.)
  ├─ related_id (INTEGER, optional)
  ├─ payload (JSONB)
  ├─ is_read (BOOLEAN)
  ├─ created_at
  └─ read_at

exchange_messages (NEW!)
  ├─ id (PK)
  ├─ exchange_id (VARCHAR)
  ├─ sender_id (FK → users)
  ├─ message_text (TEXT)
  ├─ message_type (TEXT, IMAGE, SYSTEM)
  ├─ is_read (BOOLEAN)
  ├─ delivered_at (TIMESTAMP)
  ├─ read_at (TIMESTAMP)
  └─ created_at

user_reviews (NEW!)
  ├─ id (PK)
  ├─ author_id (FK → users)
  ├─ target_id (FK → users)
  ├─ exchange_id (VARCHAR)
  ├─ rating (INTEGER: 1-5)
  ├─ text (TEXT)
  ├─ is_public (BOOLEAN)
  └─ created_at

exchange_history (NEW!)
  ├─ id (PK)
  ├─ exchange_id (VARCHAR)
  ├─ event_type (CREATED, CONFIRMED, COMPLETED, CANCELLED, REVIEWED)
  ├─ user_id (FK → users, NULLABLE)
  ├─ details (JSONB)
  └─ created_at

reports (NEW!)
  ├─ id (PK)
  ├─ reporter_id (FK → users)
  ├─ target_listing_id (FK → listing_items, NULLABLE)
  ├─ target_user_id (FK → users, NULLABLE)
  ├─ reason (PRICE_MISMATCH, SPAM, FRAUD, etc.)
  ├─ description (TEXT)
  ├─ status (PENDING, UNDER_REVIEW, RESOLVED, DISMISSED)
  ├─ admin_id (FK → users, NULLABLE)
  ├─ admin_notes (TEXT)
  ├─ resolution (LISTING_REMOVED, USER_WARNED, etc.)
  ├─ created_at
  ├─ resolved_at
  └─ updated_at

user_trust_index (NEW!)
  ├─ id (PK)
  ├─ user_id (FK → users, UNIQUE)
  ├─ trust_score (FLOAT)
  ├─ weighted_rating (FLOAT)
  ├─ exchanges_completed (INTEGER)
  ├─ reviews_received (INTEGER)
  ├─ reports_filed (INTEGER)
  ├─ reports_received (INTEGER)
  ├─ account_age_days (INTEGER)
  ├─ last_activity_days (INTEGER)
  ├─ last_calculated (TIMESTAMP)
  └─ created_at

user_action_log (NEW!)
  ├─ id (PK)
  ├─ user_id (FK → users)
  ├─ action_type (LOGIN, LISTING_CREATE, MESSAGE_SEND, etc.)
  ├─ target_id (INTEGER, NULLABLE)
  ├─ metadata (JSONB)
  ├─ ip_address (VARCHAR)
  ├─ user_agent (TEXT)
  └─ created_at

match_index (NEW!)
  ├─ id (PK)
  ├─ user_id (FK → users)
  ├─ item_type (want, offer)
  ├─ exchange_type (PERMANENT, TEMPORARY)
  ├─ category (VARCHAR)
  ├─ tags (JSONB)
  ├─ updated_at
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

## 🧮 **Language Normalization & Scoring Engine**

### **LanguageNormalizer Module (`backend/language_normalization.py`)**

Модуль для многоязыковой нормализации текста и семантического сравнения. Обеспечивает точное сопоставление текстов с учетом морфологии, синонимов и семантической близости.

#### **Основные компоненты:**

1. **Текстовые трансформации:**
   - Кириллица ↔ Латиница (транслитерация)
   - Нормализация регистра и пунктуации
   - Удаление стоп-слов (из `data/stopwords.txt`)

2. **Морфологический анализ:**
   - Поддержка русской морфологии через pymorphy3
   - Лемматизация и стемминг через NLTK/Spacy

3. **Семантическое сравнение:**
   - **Векторная близость:** SentenceTransformers модель (`paraphrase-multilingual-MiniLM-L12-v2`)
   - **Лексическое перекрытие:** Jaccard similarity по словам
   - **Fuzzy matching:** RapidFuzz для опечаток и вариаций
   - **Синонимы:** Расширенная база в `data/synonyms.json`

4. **Композитный скоринг:**
   ```
   final_score = (semantic_vector * 0.4) + (word_overlap * 0.6)
   ```

#### **API:**
```python
normalizer = LanguageNormalizer()
score = normalizer.similarity_score("гитара", "уроки музыки")  # → 0.75
vector_sim = normalizer.vector_similarity("iPhone", "айфон")   # → 0.92
```

### **MatchingScorer Module (`backend/scoring.py`)**

Комплексный модуль для расчета итогового скоринга мэтчинга. Комбинирует текстовую схожесть, стоимость и временные параметры.

#### **Компоненты скоринга:**

1. **ScoreComponent Enum:**
   - `SEMANTIC_VECTOR`: Векторная семантическая близость (0.4 вес)
   - `WORD_OVERLAP`: Перекрытие слов (0.6 вес)
   - `FUZZY_MATCH`: Fuzzy matching для опечаток
   - `COST_PRIORITY`: Приоритет по стоимости
   - `DURATION_PENALTY`: Штраф за несовпадение duration

2. **Стоимостный приоритет:**
   ```
   cost_priority = 1.0 / (1.0 + price_diff_ratio)
   ```

3. **Duration penalty:**
   - Точное совпадение: `1.1` (бонус)
   - Несовпадение: `0.9` (штраф)

4. **Итоговый score:**
   ```
   final_score = (semantic*0.4 + overlap*0.6 + cost_priority) * duration_penalty
   ```

#### **API:**
```python
scorer = MatchingScorer()
result = scorer.calculate_score(
    "гитара", "уроки музыки",
    price_a=25000, price_b=15000,
    duration_a="7 дней", duration_b="7 дней",
    is_cross_category=True
)
# → MatchingScore(total_score=0.85, is_match=True, ...)
```

### **EquivalenceEngine с Adaptive Tolerance**

Расширенная система эквивалентности с адаптивной толерантностью для межкатегорийных обменов.

#### **Конфигурация:**
```python
class ExchangeEquivalenceConfig:
    VALUE_TOLERANCE = 0.15          # ±15% для same-category
    CROSS_CATEGORY_TOLERANCE = 0.50  # ±50% для cross-category
    MIN_MATCH_SCORE = 0.70           # Минимальный скор для мэтча
```

#### **Адаптивная логика:**
```python
tolerance = CROSS_CATEGORY_TOLERANCE if is_cross_category else VALUE_TOLERANCE
# Позволяет более гибкое сопоставление для разных категорий
```

---

## 🤖 **Incremental Matching System**

### **Архитектура инкрементального мэтчинга**

Система инкрементального мэтчинга предотвращает полную пересчет всех комбинаций при каждом изменении профиля пользователя. Вместо O(N×N) используется O(K) сложность, где K - количество затронутых категорий.

#### **Ключевые компоненты:**

1. **MatchIndex Table** - индекс пользовательских предпочтений
2. **Event System** - асинхронные события изменения профиля
3. **MatchUpdater Worker** - фоновый пересчет матчей
4. **Partial Updates API** - PATCH endpoints для частичных изменений

#### **MatchIndex Table Schema:**
```sql
CREATE TABLE match_index (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    item_type VARCHAR(10) NOT NULL, -- 'want' | 'offer'
    exchange_type VARCHAR(20) NOT NULL, -- 'PERMANENT' | 'TEMPORARY'
    category VARCHAR(50) NOT NULL,
    tags JSONB, -- Array of tags for advanced filtering
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint prevents duplicates
    UNIQUE(user_id, category, item_type, exchange_type),

    -- GIN index for tag-based queries
    INDEX GIN (tags),

    -- Composite indexes for performance
    INDEX (category, user_id),
    INDEX (user_id),
    INDEX (exchange_type),
    INDEX (item_type),
    INDEX (updated_at)
);
```

#### **Event-Driven Flow:**

```
1. PATCH /listings/{id} → 2. ProfileChangeEvent → 3. MatchIndex Update → 4. MatchUpdateEvent → 5. MatchUpdater Worker → 6. Incremental Recalculation
```

#### **Partial Update API:**

```http
PATCH /listings/{listing_id}?user_id=123
Content-Type: application/json

{
  "wants": {
    "electronics": [
      {"item_name": "iPad", "value_tenge": 300000, "exchange_type": "PERMANENT"}
    ]
  },
  "offers": {
    "transport": [
      {"item_name": "велосипед", "value_tenge": 50000, "exchange_type": "TEMPORARY", "duration_days": 30}
    ]
  },
  "remove_items": [456, 789]
}
```

#### **Exchange Confirmation & Auto-Cleanup:**

```http
POST /exchanges/mutual_1_2_10_15/confirm?confirmer_user_id=1
```

**Автоматические действия:**
- Валидация участников обмена
- Soft-delete обмененных items (`is_archived = true`)
- Генерация ProfileChangeEvent для обоих пользователей
- Отправка уведомлений о завершении обмена
- Триггер инкрементального пересчета матчей

#### **Performance Benefits:**

- **Before:** Полный пересчет всех матчей при любом изменении (~N×N операций)
- **After:** Инкрементальный пересчет только затронутых категорий (~K×M операций, где M << N)

- **Index Size:** O(U×C) вместо O(U×I), где U=users, C=categories, I=items
- **Update Latency:** <1 сек вместо 10-30 сек при большом количестве пользователей
- **Background Processing:** Не блокирует UI при изменениях профиля

#### **Error Handling & Resilience:**

- **Event Replay:** События сохраняются в очереди для повторной обработки при сбоях
- **Partial Failures:** Отдельные неудачи не ломают всю систему
- **Rate Limiting:** Ограничение частоты обновлений от одного пользователя
- **Monitoring:** Метрики производительности и количества обработанных задач

---

## 📡 **API Endpoints (44 Total)**

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

**Total Tables:** 30+ (all migrations applied successfully)

### **Core Tables**

```sql
-- Users with JWT authentication and Telegram integration
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE,
  email VARCHAR(100) UNIQUE,
  phone VARCHAR(20) UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(100),
  telegram_contact VARCHAR(100),
  city VARCHAR(50) DEFAULT 'Алматы' NOT NULL,
  bio TEXT,
  trust_score FLOAT DEFAULT 0.0,
  exchange_count INTEGER DEFAULT 0,
  rating_avg FLOAT DEFAULT 0.0,
  rating_count INTEGER DEFAULT 0,
  last_rating_update TIMESTAMP WITH TIME ZONE,
  is_active BOOLEAN DEFAULT true,
  is_verified BOOLEAN DEFAULT false,
  email_verified BOOLEAN DEFAULT false,
  phone_verified BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE,
  last_login_at TIMESTAMP WITH TIME ZONE,
  last_active_at TIMESTAMP WITH TIME ZONE,
  contact JSON,
  locations VARCHAR[] DEFAULT '{"Алматы"}',
  telegram_id INTEGER UNIQUE,
  telegram_username VARCHAR(50),
  telegram_first_name VARCHAR(50)
);

-- Refresh tokens for JWT authentication
CREATE TABLE refresh_tokens (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  token_hash VARCHAR(128) UNIQUE NOT NULL,
  device_id VARCHAR(64) NOT NULL,
  user_agent VARCHAR(255),
  issued_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  is_revoked BOOLEAN DEFAULT false,
  ip_address VARCHAR(45),
  revoked_at TIMESTAMP WITH TIME ZONE,
  revoked_reason VARCHAR(100)
);

-- Authentication events for logging
CREATE TABLE auth_events (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  event_type VARCHAR(50) NOT NULL,
  ip_address VARCHAR(45),
  user_agent VARCHAR(255),
  device_id VARCHAR(64),
  success BOOLEAN DEFAULT true,
  details JSON,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
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

### **Additional Tables (Phase 2.2+)**

- `exchange_messages` - WebSocket chat messages with delivery tracking
- `user_events` - Notification events system
- `user_reviews` - Trust rating system
- `exchange_history` - Complete exchange timelines
- `reports` - Moderation complaint system
- `user_trust_index` - Trust score analytics
- `user_action_log` - Audit trail
- `match_index` - Incremental matching optimization
- `categories_v6` - Versioned category system
- `category_versions` - Category versioning metadata
- `category_mappings` - Category migration mappings
- `notifications` - User notifications
- `exchange_chains` - Multi-party exchange chains
- `mutual_matches` - Bilateral match records

**All tables include proper indexes, foreign keys, and constraints for optimal performance.**

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
- [API_REFERENCE.md](./API_REFERENCE.md) - All 44 endpoints
- [TESTING.md](./TESTING.md) - 15+ test scenarios
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Production setup
- [MIGRATIONS.md](./MIGRATIONS.md) - Database migration guide


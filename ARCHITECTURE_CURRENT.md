# FreeMarket - Текущая архитектура системы

## 📊 ОБЗОР

Система двухтипного обмена ресурсами (постоянный + временный) с категоризацией, матчингом и поиском эквивалентов.

---

## 🗂️ ОСНОВНЫЕ КОМПОНЕНТЫ

### ФРОНТЕНД

**Реакт-компоненты:**
- `ExchangeTabs.jsx` - основной компонент (выбор типа обмена + форма)
- `PermanentTab.jsx` - форма для постоянного обмена
- `TemporaryTab.jsx` - форма для временного обмена (с duration_days)

**Структура данных формы (byCategory):**
```javascript
{
  wants: {
    "cars": {
      enabled: true,
      items: [
        { name: "Toyota", price: "1000000" },
        { name: "BMW", price: "1500000" }
      ]
    },
    "electronics": {
      enabled: false,
      items: []
    }
  },
  offers: {
    "real_estate": {
      enabled: true,
      items: [
        { name: "Квартира 2-комн", price: "15000000" }
      ]
    }
  }
}
```

**API сервис (frontend/services/api.js):**
- `getWants()` → GET `/api/listings/wants`
- `getOffers()` → GET `/api/listings/offers`
- `createListing(data)` → POST `/api/listings/create?user_id=X`
- `findMatches(user_id, type)` → POST `/api/listings/find-matches`

---

### БЭКЕНД - ОСНОВНЫЕ СЛОИ

#### 1. **МОДЕЛИ (backend/models.py)**

**ListingItem** - универсальная модель для всех предметов:
```python
class ListingItem(Base):
    id: int
    listing_id: int (FK → Listing)
    
    # Классификация
    item_type: ListingItemType (WANT | OFFER)
    category: str (50 chars)
    exchange_type: ExchangeType (PERMANENT | TEMPORARY)
    
    # Данные предмета
    item_name: str (100 chars)
    value_tenge: int
    duration_days: int (nullable - только для TEMPORARY)
    description: str
    
    # Audit
    created_at, updated_at
    
    # Properties
    @property daily_rate → value_tenge / duration_days (для TEMPORARY)
    @property is_valid → проверка валидности данных
    @property equivalence_key → уникальный ключ для матчинга
```

**Enum'ы:**
- `ExchangeType.PERMANENT` - постоянный обмен
- `ExchangeType.TEMPORARY` - временный обмен (с аренде)
- `ListingItemType.WANT` - что нужно
- `ListingItemType.OFFER` - что есть

---

#### 2. **API ENDPOINTS (backend/api/endpoints/listings_exchange.py)**

**GET endpoints (для фронтенда):**
- `GET /api/listings/wants` - получить все WANTS
- `GET /api/listings/offers` - получить все OFFERS

**POST endpoints (создание):**
- `POST /api/listings/create?user_id=X` - создать листинг с категориями

**POST endpoints (поиск):**
- `POST /api/listings/find-matches?user_id=X&exchange_type=permanent|temporary` - найти совпадения

---

#### 3. **ВАЛИДАЦИЯ КАТЕГОРИЙ (backend/schemas.py)**

`VALID_CATEGORIES` - множество всех валидных категорий:
```python
VALID_CATEGORIES = {
    # Permanent categories
    "cars", "real_estate", "electronics", "entertainment_tech",
    "everyday_clothes", "accessories", "kitchen_furniture", "collectibles",
    "animals_plants", "money_crypto", "securities",
    
    # Temporary categories
    "bicycle", "electric_transport", "sports_transport", "hand_tools",
    "power_tools", "industrial_equipment", "photo_video", "audio_equipment",
    "sports_gear", "tourism_camping", "games_vr", "music_instruments",
    "costumes", "event_accessories", "subscriptions", "temporary_loan",
    "consulting"
}
```

---

#### 4. **МАТЧИНГ-ЛОГИКА (backend/api/endpoints/listings_exchange.py)**

**_find_matches_internal()** - основная функция поиска совпадений:

**Для PERMANENT обмена:**
- Ищет wants user_A в offers user_B
- Сравнивает `value_tenge` (±15% допуска)
- Скор: пропорция эквивалентности

**Для TEMPORARY обмена:**
- Ищет wants user_A в offers user_B
- Сравнивает `daily_rate = value_tenge / duration_days`
- Скор: пропорция эквивалентности дневных ставок

**Оба типа:**
- Проверяют совпадение категорий
- Находят location overlap
- Сохраняют Notification'ы в БД
- Отправляют Telegram-сообщения через bot

---

### БАЗА ДАННЫХ

**Главные таблицы:**

| Таблица | Назначение |
|---------|-----------|
| `users` | Пользователи, контакты, Telegram ID |
| `listings` | Основной листинг (один на пользователя per exchange_type) |
| `listing_items` | Предметы в листинге (WANT/OFFER, с категориями) |
| `notifications` | Уведомления о совпадениях |

**Индексы (для оптимизации):**
```sql
ix_listing_exchange_type (listing_id, exchange_type)
ix_category_exchange_type (category, exchange_type)
ix_item_type_category (item_type, category)
ix_created_at_exchange (created_at, exchange_type)
ix_category_value_exchange (category, value_tenge, exchange_type)
```

---

## 🔄 FLOW: ОТ ФОРМЫ К МАТЧИНГУ

### 1️⃣ Пользователь заполняет форму
```
├─ Выбирает тип: Permanent или Temporary
├─ Заполняет данные: Name, Telegram, City
├─ Для каждой категории:
│  ├─ Чекбокс (enable/disable)
│  └─ Добавляет items: name + price (+ duration_days для Temporary)
└─ Кликает "Начать поиск"
```

### 2️⃣ Трансформация данных (ExchangeTabs.jsx)
```javascript
transformFormDataToApiFormat({
  wants: {
    "cars": [
      { name: "Toyota", price: 1000000, duration_days: null },
      { name: "BMW", price: 1500000, duration_days: null }
    ]
  },
  offers: { ... },
  locations: ["Алматы"],
  user_data: { name, telegram, city }
})
```

### 3️⃣ Запрос на бэкенд
```
POST /api/listings/create?user_id=1
{
  "wants": { ... },
  "offers": { ... },
  "locations": ["Алматы"],
  "user_data": { ... }
}
```

### 4️⃣ Создание листинга в БД
```
1. Verify user exists
2. Update user.username, user.telegram_username, user.locations
3. Create Listing (main record)
4. For each category → For each item → Create ListingItem
   ├─ Validate item (is_valid property)
   └─ Store with item_type, exchange_type, category
5. Commit to DB
```

### 5️⃣ Автоматический матчинг
```
_find_matches_internal(user_id, exchange_type):
  1. Get user's listings (wants)
  2. Find all other users' listings (offers) in same category
  3. For each want-offer pair:
     ├─ Calculate score (based on exchange_type logic)
     ├─ If score > threshold:
     │  ├─ Save Match record
     │  └─ Send Notification to both users
     └─ Optionally send Telegram message
```

### 6️⃣ Фронтенд отображает результаты
```
├─ GET /api/listings/wants → показать в "НУЖНО" секции
├─ GET /api/listings/offers → показать в "ПРЕДЛАГАЮ" секции
└─ Обновить счётчик совпадений
```

---

## 🎯 КЛЮЧЕВЫЕ РАЗЛИЧИЯ: PERMANENT vs TEMPORARY

| Аспект | PERMANENT | TEMPORARY |
|--------|-----------|-----------|
| **Стоимость** | Полная цена (Тенге) | Дневная ставка базовая |
| **Duration** | NULL | 1-365 дней |
| **Матчинг** | value_a ≈ value_b | daily_rate_a ≈ daily_rate_b |
| **Толерантность** | ±15% | ±15% (от daily_rate) |
| **Примеры** | Авто, недвижимость, техника | Велосипед, камера, инструменты |

---

## 🚀 РАЗВЁРТЫВАНИЕ

**Основные изменения в docker-compose.prod.yml:**
- Backend слушает на `:8000`
- Nginx проксирует `/api/` к backend
- Nginx проксирует `/` к frontend (статические файлы + SPA routing)

**Frontend build (Dockerfile.nginx):**
1. Build React приложение (Vite)
2. Copy dist → Nginx /usr/share/nginx/html
3. Serve с Cache-Control заголовками

---

## 📝 УСТАРЕВШИЕ КОМПОНЕНТЫ (УДАЛЕНЫ)

❌ `backend/api/endpoints/market_listings.py` - старая модель MarketListing
❌ `Listing.py`, `ListingOffer.py`, `ListingWant.py` - старые модели (не используются)
❌ `RegistrationForm.jsx` - заменена на ExchangeTabs

---

## ✅ ТЕКУЩАЯ АРХИТЕКТУРА - ЧИСТАЯ И ОПТИМАЛЬНАЯ

- ✅ Единая модель `ListingItem` для всех типов
- ✅ Разделение логики по `exchange_type` + `item_type`
- ✅ Категоризация встроена в модель
- ✅ Матчинг работает отдельно для каждого типа
- ✅ Frontend полностью синхронизирован с бэкенд структурой
- ✅ Все индексы оптимизированы для частых queries

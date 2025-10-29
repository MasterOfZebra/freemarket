# 🚀 FreeMarket Development Guide

**Для локальной разработки и проверки логики функционала**

---

## 📋 Логика системы

### Главный функционал (цепочка операций):

```
1. USER REGISTRATION
   ├─ Пользователь регистрируется с Telegram контактом
   └─ БД: создана запись в таблице users

2. CREATE LISTING
   ├─ Пользователь создает объявление
   ├─ Выбирает: ДАРЮ (offers) или ХОЧУ (wants)
   ├─ Заполняет: название, описание, категорию, место
   └─ БД: запись в таблице market_listings

3. MATCHING (автоматический подбор пар)
   ├─ Система сравнивает объявления
   ├─ Ищет ДВУСТОРОННИЕ совпадения:
   │  ├─ want Alice совпадает с offer Bob
   │  ├─ AND want Bob совпадает с offer Alice
   │  └─ Только такие пары создают Match!
   ├─ Проверяет: категория, место, описание совпадают?
   ├─ Рассчитывает score (0.0-1.0)
   └─ БД: создается Match с оценкой совпадения

4. NOTIFICATIONS (уведомления)
   ├─ Оба пользователя получают уведомление
   ├─ Содержит: контакт партнера, описание
   └─ БД: запись в таблице notifications

5. ACCEPTANCE (принятие/отклонение)
   ├─ Alice принимает → Match.status = "accepted_a"
   ├─ Bob принимает → Match.status = "matched"
   └─ Оба могут оставить рейтинг друг другу
```

---

## 🛠️ Запуск локально

### Требования:
- Python 3.10+
- PostgreSQL 12+ (или SQLite для тестов)
- Node.js 18+ (для Frontend, опционально)

### Шаг 1: Backend - Быстрая проверка (БЕЗ БД)

```bash
# Проверить что всё работает на уровне кода
cd FreeMarket
python backend/quick_test.py

# Результат:
# ✅ All structure tests passed!
# - Backend structure: ✅ OK
# - API routes: ✅ OK (10 total)
# - Modules: ✅ OK
```

### Шаг 2: Backend - С PostgreSQL

```bash
# Убедиться что PostgreSQL запущена:
psql -U postgres -c "SELECT version();"

# Перейти в backend
cd backend

# Установить зависимости (если не установлены)
pip install -r requirements.txt

# Запустить API
python -m uvicorn main:app --reload --port 8000

# Результат:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

### Шаг 3: Frontend (опционально)

```bash
# В новом терминале
cd src
npm install
npm run dev

# Результат:
# VITE v7.1.12 ready in 245 ms
# ➜ Local: http://localhost:5173/
```

### Шаг 4: Тестирование API (curl)

```bash
# 1️⃣ Создать пользователя Alice
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "contact": {"telegram": "@alice_kz"}}'

# 2️⃣ Создать объявление ДАРЮ (велосипед)
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "offers",
    "title": "Отдаю велосипед",
    "description": "В хорошем состоянии",
    "category_id": 1,
    "location": "Алматы",
    "contact": "@alice_kz",
    "user_id": 1
  }'

# 3️⃣ Создать пользователя Bob
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "contact": {"telegram": "@bob_kz"}}'

# 4️⃣ Создать объявление ХОЧУ (велосипед)
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "wants",
    "title": "Ищу велосипед",
    "description": "Ищу велосипед",
    "category_id": 1,
    "location": "Алматы",
    "contact": "@bob_kz",
    "user_id": 2
  }'

# 5️⃣ Получить все ДАРЮ
curl http://localhost:8000/api/market-listings/offers/all

# 6️⃣ Получить все ХОЧУ
curl http://localhost:8000/api/market-listings/wants/all

# 7️⃣ Проверить здоровье API
curl http://localhost:8000/health
```

---

## 🔗 API Маршруты (10 всего)

### Users
```
POST   /users/                    # Создать пользователя
GET    /users/{username}          # Получить пользователя
```

### Market Listings (Главные)
```
POST   /api/market-listings/                # Создать объявление
GET    /api/market-listings/offers/all      # Все ДАРЮ
GET    /api/market-listings/wants/all       # Все ХОЧУ
GET    /api/market-listings/{id}            # Конкретное объявление
```

### Notifications
```
GET    /api/notifications?user_id=X         # Получить уведомления
```

### Health
```
GET    /health                              # Проверка здоровья
```

---

## 📊 Структура Данных

### Users table
```sql
id (PK)
username (UNIQUE)
contact (JSON: {telegram: "@username"})
trust_score (float, default 0.0)
created_at (timestamp)
```

### Market_listings table
```sql
id (PK)
type (ENUM: offers, wants)
title (string)
description (text)
category_id (FK → categories)
location (string)
contact (string)
user_id (FK → users)
status (ENUM: active, archived)
created_at (timestamp)
```

### Matches table
```sql
id (PK)
item_a (FK → market_listings)
item_b (FK → market_listings)
score (float: 0.0-1.0)
status (ENUM: new, accepted_a, accepted_b, matched)
matched_at (timestamp)
created_at (timestamp)
```

### Notifications table
```sql
id (PK)
user_id (FK → users)
payload (JSON: {type, from_user, contact, ...})
is_sent (boolean)
created_at (timestamp)
```

---

## 🔗 Алгоритм двустороннего совпадения (Bidirectional Matching)

### Математическое определение:

**Match создается ТОЛЬКО если выполнены ОБА условия:**

```
Condition 1: Alice.want ⊆ Bob.offer  (Alice хочет что имеет Bob)
Condition 2: Bob.want ⊆ Alice.offer  (Bob хочет что имеет Alice)

Если оба условия TRUE → Match создается
Если любое FALSE → Match НЕ создается
```

### Пример 1: ✅ Match создается

```
Alice:
  offer: велосипед
  want: книга

Bob:
  offer: книга
  want: велосипед

Check:
1. Alice.want (книга) ∈ Bob.offer? ДА ✅
2. Bob.want (велосипед) ∈ Alice.offer? ДА ✅
Result: MATCH CREATED!
```

### Пример 2: ❌ Match НЕ создается

```
Alice:
  offer: велосипед
  want: книга

Bob:
  offer: ноутбук (НЕ книга!)
  want: велосипед

Check:
1. Alice.want (книга) ∈ Bob.offer? НЕТ ❌
2. Bob.want (велосипед) ∈ Alice.offer? ДА ✅
Result: NO MATCH (первое условие не выполнено)
```

### Score рассчитывается как:

```
score = base_score × category_match × location_match × text_similarity

где:
- base_score = 1.0 (начальная оценка)
- category_match = 1.0 если категории совпадают, 0.8 если близки
- location_match = 1.0 если места совпадают, 0.5-0.8 если рядом
- text_similarity = косинусное сходство описаний (0.0-1.0)

Результат: score ∈ [0.0, 1.0]
```

---

## 🧪 Тестирование Логики

### Сценарий 1: Идеальное совпадение (Happy Path)

```
Alice: offer "велосипед" (категория: транспорт, место: Алматы)
Alice: want "книга" (категория: образование, место: Алматы)

Bob: offer "книга" (категория: образование, место: Алматы)
Bob: want "велосипед" (категория: транспорт, место: Алматы)

ПРОВЕРКА:
✅ Alice want ("книга") совпадает с Bob offer ("книга")? ДА
✅ Bob want ("велосипед") совпадает с Alice offer ("велосипед")? ДА
✅ ДВУСТОРОННИЙ Match создается!
✅ Score: 1.0 (100% совпадение)
✅ Оба получают уведомление
```

### Сценарий 2: Одностороннее совпадение (НЕТ Match)

```
Alice: offer "велосипед"
Alice: want "книга"

Bob: offer "велосипед"
Bob: want "автомобиль" (НЕ совпадает!)

ПРОВЕРКА:
✅ Alice want ("книга") совпадает с Bob offer ("велосипед")? НЕТ
❌ Условие не выполнено - Match НЕ создается!
```

### Сценарий 3: Частичное совпадение

```
Alice: offer "велосипед" (Алматы)
Alice: want "книга" (Алматы)

Bob: offer "книга" (Алматы)
Bob: want "велосипед" (Астана - другой город!)

ПРОВЕРКА:
✅ Alice want совпадает с Bob offer? ДА
✅ Bob want совпадает с Alice offer? ДА (но города разные)
✅ Match создается, но score < 1.0 (штраф за расстояние)
⚠️  Score: 0.7 (из-за разных мест)
```

### Сценарий 4: Принятие/Отклонение

```
1. Match создан (status: new, двусторонний)
2. Alice принимает → status: accepted_a
3. Bob отклоняет → status: rejected
4. Транзакция не завершена

ОЖИДАНИЕ:
✅ Status переходит правильно
✅ Уведомления отправляются верно
✅ Рейтинг НЕ выставляется при отклонении
```

---

## 🔍 Проверка логики (без Frontend)

### Используйте Swagger UI

```
http://localhost:8000/docs

Там можно:
- Тестировать все эндпоинты
- Видеть схемы данных
- Проверять ответы
```

### Или используйте PostMan/Insomnia

Импортируйте коллекцию с примерами выше.

---

## 📁 Структура проекта (для локальной разработки)

```
backend/
├── api/
│   ├── endpoints/
│   │   ├── health.py       ← Проверка живости
│   │   ├── market_listings.py ← Главные эндпоинты
│   │   └── notifications.py    ← Уведомления
│   └── router.py           ← Комбинирует все
├── config.py               ← Все настройки тут
├── main.py                 ← Точка входа (50 строк)
├── models.py               ← БД модели
├── schemas.py              ← Pydantic валидация
├── crud.py                 ← CRUD операции
├── matching.py             ← Логика подбора
├── database.py             ← БД подключение
└── quick_test.py           ← Проверка структуры

src/
├── components/             ← React компоненты
├── pages/                  ← React страницы
├── services/               ← API запросы
├── styles/                 ← CSS
└── App.jsx                 ← Главный компонент
```

---

## ✅ Чек-лист проверки логики

- [ ] **User Registration**
  - [ ] Пользователь создается с уникальным username
  - [ ] Сохраняется контакт (телеграм)
  - [ ] Возвращается user_id

- [ ] **Listing Creation**
  - [ ] offer объявление создается (type: offers)
  - [ ] want объявление создается (type: wants)
  - [ ] Заполняются все поля (title, description, category, location)
  - [ ] Связывается с user_id

- [ ] **Matching Logic (ДВУСТОРОННИЙ)**
  - [ ] ✅ Match создается ТОЛЬКО если:
    - [ ] want от Alice совпадает с offer Bob
    - [ ] AND want от Bob совпадает с offer Alice
  - [ ] ❌ Match НЕ создается если только одна сторона совпадает
  - [ ] Score рассчитывается правильно (0.0-1.0)
  - [ ] Учитываются: категория, место, описание
  - [ ] Штраф применяется за разные места

- [ ] **Notifications**
  - [ ] Оба пользователя получают уведомление
  - [ ] Уведомление содержит контакт партнера
  - [ ] Уведомление описывает что получат оба

- [ ] **Status Transitions**
  - [ ] new → accepted_a (один принял)
  - [ ] accepted_a → matched (оба приняли)
  - [ ] Отклонение отменяет процесс
  - [ ] При отклонении рейтинг НЕ выставляется

---

## 📝 Кодовые файлы для изучения (логика)

1. **matching.py** - Как рассчитывается score
2. **crud.py** - Создание записей в БД
3. **models.py** - Структура таблиц
4. **api/endpoints/market_listings.py** - API логика

---

## 🐛 Дебаг-советы

### Посмотреть логи Backend:
```bash
# С флагом --reload видны все ошибки
python -m uvicorn main:app --reload --port 8000
```

### Посмотреть что в БД:
```bash
# Подключиться к PostgreSQL
psql -U assistadmin_pg -d assistance_kz

# SQL запросы:
SELECT * FROM users;
SELECT * FROM market_listings;
SELECT * FROM matches;
SELECT * FROM notifications;
```

### Сбросить БД:
```bash
# ВНИМАНИЕ: это удалит все данные!
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS market_listings CASCADE;
DROP TABLE IF EXISTS users CASCADE;

# Потом перезапустить API
```

---

## 🎯 Финальный Workflow для проверки логики

```bash
# 1. Структурная проверка
python backend/quick_test.py

# 2. Запустить Backend
python -m uvicorn backend.main:app --reload --port 8000

# 3. В новом терминале - запустить Frontend (опционально)
cd src && npm run dev

# 4. Тестировать через Swagger UI
# Открыть http://localhost:8000/docs

# 5. Или через curl (примеры выше)
```

---

**Все готово к локальной разработке и проверке логики! 🚀**

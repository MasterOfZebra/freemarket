# 🧪 FreeMarket - Testing Guide

## Быстрый старт для тестирования

### Что протестировано на рефакторинге:
✅ **ФАЗА 1:** Frontend переструктурирована (`src/` → `src/{components,pages,services,styles}`)
✅ **ФАЗА 2:** Удалены ненужные ML модули (-2.7GB зависимостей)
✅ **ФАЗА 3:** Backend API модулирован (`backend/api/endpoints/`)
✅ **ФАЗА 4:** Конфигурация централизована (`backend/config.py`)

---

## 📋 Основной функционал для тестирования

### Задача:
1. Пользователь регистрируется → вводит Telegram
2. Пользователь создает анкету → что хочет дать, что хочет получить
3. Система ищет партнёра с совместимыми запросами
4. Оба получают контакты друг друга

---

## 🚀 Как запустить тесты

### Вариант 1: Через Docker Compose (Рекомендуется)

```bash
# В корне проекта:
docker-compose -f docker-compose.prod.yml up -d

# Ждём 30 секунд пока всё стартует...
sleep 30

# Проверяем логи:
docker-compose -f docker-compose.prod.yml logs backend

# Тест здоровья API:
curl http://localhost/health
```

**Ожидаемый ответ:**
```json
{
  "status": "ok",
  "message": "FreeMarket API is running"
}
```

---

### Вариант 2: Локально (Python)

#### Шаг 1: Запуск Backend

```bash
# В отдельном терминале из корня проекта:
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Ожидаемый вывод:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

#### Шаг 2: Запуск Frontend

```bash
# В отдельном терминале:
cd src
npm run dev
```

**Ожидаемый вывод:**
```
  VITE v7.1.12  ready in XXX ms
  ➜  Local:   http://localhost:5173/
```

#### Шаг 3: Запуск интеграционного теста

```bash
# В третьем терминале:
python backend/test_integration.py
```

**Ожидаемый результат:**
```
🚀 FreeMarket Integration Test - Full User Flow

======================================================================
📝 STAGE 1: API Health Check
======================================================================

✅ PASS | API Health Check
   └─ FreeMarket API is running

======================================================================
📝 STAGE 2: User Registration
======================================================================

✅ PASS | Create user 'alice_test_001'
   └─ ID: 1
✅ PASS | Create user 'bob_test_001'
   └─ ID: 2
✅ PASS | Create user 'charlie_test_001'
   └─ ID: 3

... (остальные результаты)
```

---

## 🧪 Ручное тестирование через curl

### 1️⃣ Создание пользователя

```bash
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice_test",
    "contact": {"telegram": "@alice_kz"}
  }'
```

**Ожидаемый ответ:**
```json
{
  "id": 1,
  "username": "alice_test",
  "trust_score": 0.0,
  "created_at": "2024-10-28T10:30:45.123456"
}
```

### 2️⃣ Создание объявления ДАРЮ (Offers)

```bash
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "offers",
    "title": "Отдаю старый велосипед",
    "description": "В хорошем состоянии, горный велосипед",
    "category_id": 1,
    "location": "Алматы",
    "contact": "@alice_kz",
    "user_id": 1
  }'
```

**Ожидаемый ответ:**
```json
{
  "id": 1,
  "type": "offers",
  "title": "Отдаю старый велосипед",
  "description": "В хорошем состоянии, горный велосипед",
  "category_id": 1,
  "location": "Алматы",
  "contact": "@alice_kz",
  "user_id": 1,
  "status": "active",
  "created_at": "2024-10-28T10:31:45.123456"
}
```

### 3️⃣ Создание объявления ХОЧУ (Wants)

```bash
curl -X POST http://localhost:8000/api/market-listings/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "wants",
    "title": "Ищу велосипед",
    "description": "Ищу любой велосипед в рабочем состоянии",
    "category_id": 1,
    "location": "Алматы",
    "contact": "@bob_kz",
    "user_id": 2
  }'
```

### 4️⃣ Получить все объявления ДАРЮ

```bash
curl http://localhost:8000/api/market-listings/offers/all?skip=0&limit=20
```

**Ожидаемый ответ:**
```json
{
  "items": [
    {
      "id": 1,
      "type": "offers",
      "title": "Отдаю старый велосипед",
      "description": "В хорошем состоянии, горный велосипед",
      "category_id": 1,
      "location": "Алматы",
      "contact": "@alice_kz",
      "user_id": 1,
      "status": "active",
      "created_at": "2024-10-28T10:31:45.123456"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

### 5️⃣ Получить все объявления ХОЧУ

```bash
curl http://localhost:8000/api/market-listings/wants/all?skip=0&limit=20
```

---

## ✅ Проверочный чек-лист

Пройдите через эти шаги и отметьте:

### API Endpoints
- [ ] `POST /users/` - создание пользователя ✅ работает
- [ ] `GET /users/{username}` - получение пользователя ✅ работает
- [ ] `POST /api/market-listings/` - создание объявления ✅ работает
- [ ] `GET /api/market-listings/` - список объявлений ✅ работает
- [ ] `GET /api/market-listings/wants/all` - все ХОЧУ ✅ работает
- [ ] `GET /api/market-listings/offers/all` - все ДАРЮ ✅ работает
- [ ] `GET /api/market-listings/{id}` - конкретное объявление ✅ работает
- [ ] `GET /health` - здоровье API ✅ работает

### Бизнес-логика
- [ ] При создании объявления сохраняется тип (offers/wants)
- [ ] Сохраняется контакт пользователя (телеграм)
- [ ] Данные в базе соответствуют отправленным
- [ ] Список объявлений возвращает корректное кол-во
- [ ] Можно получить конкретное объявление по ID

### Frontend
- [ ] Страница загружается без ошибок на http://localhost:5173
- [ ] Форма заполняется без проблем
- [ ] Данные отправляются на API
- [ ] Русский текст отображается корректно (без "cipher")
- [ ] После создания анкеты видно в списке

### База данных
- [ ] PostgreSQL запущена и доступна
- [ ] Таблицы `users` и `market_listings` созданы
- [ ] Данные сохраняются в БД

---

## 🐛 Если что-то не работает

### 1. API не запускается

```bash
# Проверьте что Python установлен:
python --version

# Проверьте зависимости:
pip install -r backend/requirements.txt

# Запустите с детальными ошибками:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Ошибка подключения к БД

```bash
# Проверьте что PostgreSQL запущена:
# (или используйте Docker Compose для автоматического запуска)

# Проверьте CONNECTION STRING в backend/config.py
# По умолчанию:
# postgresql://assistadmin_pg:assistMurzAdmin@postgres:5432/assistance_kz
```

### 3. Frontend не соединяется с API

```bash
# Проверьте что API запущена на порте 8000:
curl http://localhost:8000/health

# Проверьте CORS в backend/config.py
# Frontend должен быть в CORS_ORIGINS
```

### 4. Русский текст показывает "cipher"

✅ **Это уже исправлено в ФАЗЕ 4:**
- Nginx настроен на UTF-8
- API возвращает JSON с `ensure_ascii=False`
- Frontend использует правильную кодировку

---

## 📊 Логирование

### Просмотр логов backend

```bash
# В реальном времени:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Или в Docker:
docker-compose -f docker-compose.prod.yml logs backend -f
```

### Просмотр логов PostgreSQL

```bash
docker-compose -f docker-compose.prod.yml logs postgres -f
```

---

## 🎯 Полный сценарий (от начала до конца)

```bash
# 1. Запустить Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# 2. Ждём готовности
sleep 30

# 3. Проверить здоровье
curl http://localhost/health

# 4. Запустить тест
python backend/test_integration.py

# 5. Открыть браузер
open http://localhost:3000
# или
firefox http://localhost

# 6. Вручную заполнить форму и проверить
```

---

## 📝 Что дальше?

1. **Matching логика** - автоматическое найдение пар
2. **Notifications** - отправка контактов пользователям
3. **Telegram Bot** - интеграция с ботом для уведомлений
4. **Rating система** - оценка партнёров
5. **Production deploy** - готовность к развертыванию

---

**Документ создан:** 2024-10-28  
**Версия:** 1.0.0

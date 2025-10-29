# 🎁 FreeMarket - Free Marketplace for Mutual Aid

[![GitHub](https://img.shields.io/badge/GitHub-FreeMarket-blue)](https://github.com/MasterOfZebra/freemarket)
[![License](https://img.shields.io/badge/License-MIT-green)]()
[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://www.python.org/)

---

## 📋 Что это?

**FreeMarket** — платформа для коммунального обмена ресурсами между людьми.

### Функционал:
- 👥 Регистрация через Telegram
- 📝 Создание объявлений (ДАРЮ/ХОЧУ)
- 🔄 Автоматический подбор пар
- 📲 Уведомления о совпадениях
- ⭐ Система рейтинга

---

## 🚀 Быстрый старт

```bash
# 1. Структурная проверка (без БД)
python backend/quick_test.py

# 2. Запустить API (нужна PostgreSQL)
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# 3. Тестировать через Swagger UI
# http://localhost:8000/docs
```

---

## 📚 Документация

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Полное руководство локальной разработки
- **[README.md](README.md)** - Этот файл (обзор)

### В DEVELOPMENT.md найдёте:
- ✅ Логика системы и цепочка операций
- ✅ Как запустить локально
- ✅ API маршруты и примеры (curl)
- ✅ Структура данных (таблицы)
- ✅ Сценарии тестирования
- ✅ Чек-лист проверки логики

---

## 🏗️ Архитектура

### Стек:
- **Backend:** FastAPI + Python 3.10
- **Frontend:** React 18 + Vite (опционально)
- **Database:** PostgreSQL 15
- **Cache:** Redis
- **Bot:** Telegram (Aiogram)

### Структура:
```
FreeMarket/
├── backend/
│   ├── api/endpoints/     # API модули
│   ├── config.py          # Конфигурация
│   ├── main.py            # Точка входа (50 строк)
│   ├── models.py          # БД модели
│   ├── matching.py        # Логика подбора
│   └── quick_test.py      # Структурная проверка
├── src/                   # React frontend
├── docker/                # Docker образы
└── DEVELOPMENT.md         # Подробное руководство
```

---

## 🔗 API (10 маршрутов)

```
POST   /users/                      # Создать пользователя
GET    /users/{username}            # Получить пользователя

POST   /api/market-listings/        # Создать объявление
GET    /api/market-listings/offers/all  # Все ДАРЮ
GET    /api/market-listings/wants/all   # Все ХОЧУ
GET    /api/market-listings/{id}        # Конкретное

GET    /api/notifications?user_id=X    # Уведомления

GET    /health                      # Проверка API
```

Полные примеры в **[DEVELOPMENT.md](DEVELOPMENT.md)**

---

## 💻 Локальная разработка

### Требования:
- Python 3.10+
- PostgreSQL 12+ 
- Node.js 18+ (опционально, для frontend)

### Запуск:

**1. Без БД (структурная проверка):**
```bash
python backend/quick_test.py
# ✅ All structure tests passed!
```

**2. С БД (полный функционал):**
```bash
# Терминал 1
cd backend
python -m uvicorn main:app --reload --port 8000

# Терминал 2 (опционально)
cd src
npm run dev
```

Подробнее: см. **[DEVELOPMENT.md](DEVELOPMENT.md)**

---

## ✅ Рефакторинг завершён

✅ **ФАЗА 1:** Frontend структурирована  
✅ **ФАЗА 2:** ML модули удалены (-2.7GB)  
✅ **ФАЗА 3:** Backend API модулирован  
✅ **ФАЗА 4:** Конфигурация централизована  
✅ **ФАЗА 5:** Документация унифицирована  

---

## 📝 Лицензия

MIT License

---

**Для полной информации и примеров см. [DEVELOPMENT.md](DEVELOPMENT.md) 📖**

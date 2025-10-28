# 🎁 FreeMarket - Free Marketplace for Mutual Aid

[![GitHub](https://img.shields.io/badge/GitHub-FreeMarket-blue)](https://github.com/MasterOfZebra/freemarket)
[![License](https://img.shields.io/badge/License-MIT-green)]()
[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react)](https://react.dev)

---

## 📋 Описание проекта

**FreeMarket** — это платформа для коммунального обмена ресурсами между людьми.

### Ключевые возможности:
- 👥 **Регистрация пользователей** - быстрая регистрация через Telegram
- 📝 **Создание анкет** - опубликуйте что вы хотите дать или получить
- 🔄 **Автоматический подбор пар** - система находит партнёров с совместимыми запросами
- 📲 **Уведомления** - получайте контакты партнёров в Telegram
- ⭐ **Рейтинг** - оценивайте надёжность пользователей
- 🌍 **Поддержка казахского языка** - интерфейс на русском и казахском

---

## 🏗️ Архитектура

### Стек технологий:
- **Backend:** FastAPI, Python 3.9+
- **Frontend:** React 18, Vite
- **Database:** PostgreSQL 15
- **Cache:** Redis
- **Deployment:** Docker Compose, Nginx
- **Bot:** Telegram Bot API (Aiogram)

### Структура проекта:
```
FreeMarket/
├── backend/                  # 🔧 Python FastAPI приложение
│   ├── api/
│   │   ├── endpoints/       # Отдельные API модули
│   │   │   ├── health.py
│   │   │   ├── market_listings.py
│   │   │   └── notifications.py
│   │   └── router.py
│   ├── utils/               # Вспомогательные функции
│   ├── config.py           # Централизованная конфигурация
│   ├── main.py             # Точка входа (50 строк!)
│   ├── models.py           # SQLAlchemy модели
│   ├── schemas.py          # Pydantic схемы
│   ├── crud.py             # CRUD операции
│   ├── matching.py         # Алгоритм подбора пар
│   ├── bot.py              # Telegram бот
│   └── requirements.txt     # Зависимости
│
├── src/                    # 🎨 React приложение
│   ├── components/         # Переиспользуемые компоненты
│   ├── pages/             # Страницы приложения
│   ├── services/          # API сервисы
│   ├── styles/            # CSS файлы
│   └── App.jsx            # Главный компонент
│
├── docker/                 # 🐳 Docker конфигурации
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── Dockerfile.bot
│
├── config/                 # ⚙️ Конфигурационные файлы
│   └── freemarket.nginx
│
├── docker-compose.prod.yml # 🚀 Production deployment
├── TEST_SCENARIOS.md       # 📋 Полные сценарии тестирования
├── TESTING_GUIDE.md        # 🧪 Инструкция по тестированию
└── README.md              # Этот файл
```

---

## 🚀 Быстрый старт

### Требования:
- Docker & Docker Compose ИЛИ Python 3.9+ + PostgreSQL + Redis
- Node.js 16+ (для локальной разработки Frontend)

### Вариант 1: Docker Compose (Рекомендуется)

```bash
# Клонировать репозиторий
git clone https://github.com/MasterOfZebra/freemarket.git
cd freemarket

# Запустить все сервисы
docker-compose -f docker-compose.prod.yml up -d

# Ждать 30 секунд пока всё стартует...
sleep 30

# Проверить здоровье API
curl http://localhost/health

# Открыть в браузере
open http://localhost:3000
```

### Вариант 2: Локальная разработка

```bash
# Установить зависимости
pip install -r backend/requirements.txt
npm install  # в src/

# Запустить Backend (терминал 1)
cd backend
python -m uvicorn main:app --reload

# Запустить Frontend (терминал 2)
cd src
npm run dev

# Запустить тесты (терминал 3)
python backend/test_integration.py
```

---

## 📱 Основной сценарий использования

### Для конечного пользователя:

1. **Регистрация**
   ```
   Пользователь вводит свой Telegram @username
   → Создается профиль
   ```

2. **Создание анкеты**
   ```
   Пользователь заполняет:
   - Категория (Транспорт, Мебель, Электроника, etc.)
   - Что может дать (ДАРЮ)
   - Что нужно получить (ХОЧУ)
   - Местоположение
   ```

3. **Автоматический подбор пары**
   ```
   Система ищет пользователей с совместимыми запросами:
   - Alice: "ДАРЮ велосипед"
   - Bob: "ХОЧУ велосипед"
   → Найдена пара! ✅
   ```

4. **Получение контактов**
   ```
   Alice и Bob получают уведомление в Telegram с:
   - Контактом партнёра
   - Описанием что тот хочет обменять
   - Кнопками для принятия/отклонения
   ```

5. **Завершение обмена**
   ```
   После взаимного согласия оба получают финальный контакт
   Могут оставить друг другу отзыв/рейтинг
   ```

---

## 🔧 API Эндпоинты

### Пользователи
```
POST   /users/                    # Создать пользователя
GET    /users/{username}          # Получить данные пользователя
```

### Рыночные объявления
```
POST   /api/market-listings/                    # Создать объявление
GET    /api/market-listings/                    # Все объявления
GET    /api/market-listings/offers/all          # Все ДАРЮ
GET    /api/market-listings/wants/all           # Все ХОЧУ
GET    /api/market-listings/{id}                # Конкретное объявление
POST   /api/market-listings/{id}/archive        # Архивировать
```

### Матчинг (Подбор пар)
```
GET    /api/matches/{item_id}                   # Найти пары для объявления
POST   /api/matches/{match_id}/accept           # Принять пару
POST   /api/matches/{match_id}/reject           # Отклонить пару
```

### Уведомления
```
GET    /api/notifications?user_id={id}          # Получить уведомления
```

### Здоровье
```
GET    /health                     # Проверка здоровья API
```

---

## 📊 Улучшения от рефакторинга (ФАЗЫ 1-4)

### ✅ ФАЗА 1: Frontend Reorganization
- **Было:** Все файлы в `src/` в кучу
- **Стало:** Структурирована в `src/{components,pages,services,styles}/`
- **Результат:** Легче навигировать и масштабировать

### ✅ ФАЗА 2: Remove ML Modules
- **Было:** Ненужные ML модели (ab_testing, embeddings, profile_learning)
- **Удалено:** torch, torchvision, sentence-transformers, lightgbm
- **Результат:** -2.7GB размер Docker image!

### ✅ ФАЗА 3: Backend API Modularization
- **Было:** 1100+ строк в одном `main.py`
- **Стало:** Модульная архитектура `backend/api/endpoints/`
- **Результат:** ~50 строк в `main.py`, легче поддерживать

### ✅ ФАЗА 4: Centralized Configuration
- **Было:** Конфиги разбросаны по разным файлам
- **Стало:** Единый `backend/config.py`
- **Результат:** Всё в одном месте, просто менять настройки

---

## 🧪 Тестирование

### Запуск полного интеграционного теста:
```bash
python backend/test_integration.py
```

**Что тестируется:**
- ✅ Health check API
- ✅ Создание пользователей
- ✅ Создание объявлений (ДАРЮ/ХОЧУ)
- ✅ Получение списков
- ✅ Логирование результатов

### Ручное тестирование через curl:
См. [TESTING_GUIDE.md](TESTING_GUIDE.md) для примеров curl запросов.

### Полные сценарии:
См. [TEST_SCENARIOS.md](TEST_SCENARIOS.md) для деталей всех 9 сценариев.

---

## 📦 Развертывание

### На сервер (Docker):
```bash
# Клонировать на сервер
git clone https://github.com/MasterOfZebra/freemarket.git
cd freemarket

# Создать .env с конфигурацией
cp .env.example .env

# Запустить Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Проверить логи
docker-compose -f docker-compose.prod.yml logs -f backend
```

###환경 변수 (.env):
```bash
DATABASE_URL=postgresql://user:password@postgres:5432/dbname
REDIS_URL=redis://redis:6379/0
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ENV=production
```

---

## 📝 Документация

- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Полное руководство по тестированию
- [TEST_SCENARIOS.md](TEST_SCENARIOS.md) - 9 детальных сценариев тестирования
- [ARCHITECTURE.md](backend/ARCHITECTURE.md) - Архитектура backend

---

## 🐛 Решённые проблемы

- ✅ 500 Internal Server Error (DB connection)
- ✅ `ModuleNotFoundError: psycopg2` 
- ✅ `ModuleNotFoundError: fastapi`
- ✅ Русский текст показывает "cipher"
- ✅ SPA routing в Nginx
- ✅ CRLF/LF line ending issues
- ✅ Недостаток дискового пространства

---

## 🔮 Что дальше?

### Приоритет 1 (Критично):
- [ ] Протестировать matching алгоритм на реальных данных
- [ ] Интегрировать Telegram бот уведомления
- [ ] Добавить rate limiting

### Приоритет 2 (Важно):
- [ ] Rating/Review система
- [ ] User profile страница
- [ ] Search и фильтрация по категориям
- [ ] Таблица истории обменов

### Приоритет 3 (Улучшения):
- [ ] Поддержка изображений в объявлениях
- [ ] Maps интеграция
- [ ] AI-powered рекомендации
- [ ] Мобильное приложение

---

## 👥 Контрибьютинг

Приветствуются pull requests! Для больших изменений сначала откройте issue.

```bash
# 1. Fork репозиторий
# 2. Создайте feature branch (git checkout -b feature/AmazingFeature)
# 3. Commit changes (git commit -m 'Add some AmazingFeature')
# 4. Push to branch (git push origin feature/AmazingFeature)
# 5. Open a Pull Request
```

---

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) файл для деталей.

---

## 📞 Контакты

- **GitHub:** [@MasterOfZebra](https://github.com/MasterOfZebra)
- **Issues:** [GitHub Issues](https://github.com/MasterOfZebra/freemarket/issues)

---

## 🙏 Благодарности

- FastAPI для отличной документации
- React сообществу за инструменты
- Docker за контейнеризацию
- PostgreSQL команде за надёжную БД

---

**Проект создан:** 2024  
**Последнее обновление:** 2024-10-28  
**Версия:** 1.0.0

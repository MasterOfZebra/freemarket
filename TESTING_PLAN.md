# План тестирования системы личных кабинетов

## ✅ Выполненные компоненты

### 1. Backend (API)
- [x] JWT аутентификация с refresh tokens в HttpOnly cookies
- [x] User модель с безопасным хранением паролей (Argon2id/bcrypt)
- [x] Token rotation и revocation
- [x] Rate limiting на auth endpoints (5 запросов/5 минут)
- [x] API личного кабинета (/user/cabinet, /user/listings, /user/exchanges)
- [x] Категории v6 с версионированием и API (/v1/categories)

### 2. Frontend (UI)
- [x] Кнопки входа/регистрации в header
- [x] Модальные окна входа и личного кабинета
- [x] Личный кабинет с вкладками: Профиль, Объявления, Обмены
- [x] Исправления UI (удаление дублирования, ненужных вкладок)

### 3. Database & Migrations
- [x] Модели для пользователей, refresh tokens, категорий v6
- [x] Category mappings для миграции legacy данных
- [x] Скрипты миграции и отката

## 🧪 План тестирования

### Phase 1: Unit Tests (Backend)
```bash
# Запуск тестов
cd backend
pytest tests/test_category_migration.py -v

# Проверка API endpoints
python -c "
import requests
# Test categories API
resp = requests.get('http://localhost:8000/v1/categories')
print('Categories API:', resp.status_code)
"
```

### Phase 2: Integration Tests (Frontend + Backend)
```bash
# 1. Запуск backend
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 2. Запуск frontend (в другом терминале)
cd frontend && npm start

# 3. Ручное тестирование в браузере
# - Регистрация нового пользователя
# - Вход в систему
# - Создание объявления
# - Просмотр личного кабинета
```

### Phase 3: Security Testing
```bash
# Test rate limiting
for i in {1..6}; do
  curl -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"identifier":"test","password":"test"}'
done

# Test token expiration (access token 15 min)
# Test refresh token rotation
# Test password security (Argon2id hashing)
```

### Phase 4: Category Migration Testing
```bash
# Initialize v6 categories
cd backend && python scripts/init_categories_v6.py

# Test migration
python scripts/migrate_legacy_categories.py

# Test rollback
python scripts/migrate_legacy_categories.py rollback

# Test rollback plan
python scripts/migration_rollback_plan.py status
```

## 🚀 Быстрый запуск для тестирования

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Initialize database (if needed)
python scripts/init_categories_v6.py

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm start
```

### 3. Test URLs
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Categories API: http://localhost:8000/v1/categories
- Auth API: http://localhost:8000/auth/

## 🔍 Тест-кейсы для ручного тестирования

### Регистрация и аутентификация
1. ✅ Регистрация нового пользователя (email + пароль)
2. ✅ Вход в систему
3. ✅ Автоматический редирект после входа
4. ✅ Просмотр профиля в личном кабинете
5. ✅ Выход из системы

### Личный кабинет
1. ✅ Просмотр профиля
2. ✅ Просмотр моих объявлений
3. ✅ Просмотр активных обменов (пока пусто)
4. ✅ Смена пароля (с отзывами всех сессий)

### Категории и формы
1. ✅ Загрузка категорий v6 через API
2. ✅ Создание объявления с новыми категориями
3. ✅ Валидация форм

### Безопасность
1. ✅ Rate limiting на auth endpoints
2. ✅ HttpOnly cookies для refresh tokens
3. ✅ Token rotation при refresh
4. ✅ Отзыв всех сессий при смене пароля

## 📊 Ожидаемые результаты

- [ ] Все API endpoints возвращают 200 OK
- [ ] JWT tokens работают корректно
- [ ] Rate limiting блокирует спам
- [ ] Категории v6 загружаются правильно
- [ ] Личный кабинет отображает данные пользователя
- [ ] Миграция категорий работает без ошибок

## 🚨 Troubleshooting

### Если API не работает:
```bash
# Check backend logs
cd backend && python -c "from backend.database import engine; print('DB OK')"

# Check API health
curl http://localhost:8000/health
```

### Если frontend не работает:
```bash
cd frontend
npm install
npm start
# Check console for CORS errors
```

### Если категории не загружаются:
```bash
# Reinitialize categories
cd backend && python scripts/init_categories_v6.py
```

## 🎯 Следующие шаги после тестирования

1. **Опциональные улучшения:**
   - Email/phone верификация
   - Telegram OAuth
   - Redis для rate limiting
   - Более подробные тесты безопасности

2. **Production deployment:**
   - Настройка HTTPS
   - Конфигурация Redis
   - Мониторинг и логирование

---

**Статус:** ✅ Готово к тестированию

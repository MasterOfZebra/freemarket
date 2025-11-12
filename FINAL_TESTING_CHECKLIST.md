# ✅ Финальный чеклист тестирования версии 2.2.1

## 📊 Анализ текущего состояния

### ✅ Что уже работает:

1. **Миграции БД** - применены успешно
2. **Health Check** - `/health` возвращает `{"status": "ok"}`
3. **OpenAPI схема** - работает, но версия показывает 2.2.0 (нужно обновить до 2.2.1)
4. **Auth endpoints** - `/auth/register` и `/auth/login` имеют requestBody в схеме ✅
5. **База данных** - все таблицы созданы:
   - users: 1 запись
   - refresh_tokens: 1 запись
   - auth_events: 1 запись
6. **Контейнеры** - все работают и healthy:
   - backend: healthy ✅
   - nginx: healthy ✅
   - postgres: healthy ✅
   - redis: running ✅
   - bot: running ✅
7. **Логи** - нет ошибок в backend и nginx

---

## 🧪 Чеклист финального тестирования

### 1. Проверка версии API

```bash
# Проверить версию в OpenAPI (должна быть 2.2.1 после обновления)
curl -s https://assistance-kz.ru/openapi.json | jq '.info.version'

# Ожидаемый результат: "2.2.1"
```

### 2. Тестирование регистрации пользователя

```bash
# Регистрация нового пользователя
curl -X POST https://assistance-kz.ru/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser2@example.com",
    "password": "testpass123",
    "full_name": "Test User 2",
    "phone": "+77770001234"
  }' | jq .

# Ожидаемый результат: HTTP 200, user object с id, email, full_name
```

### 3. Тестирование логина

```bash
# Логин пользователя
LOGIN_RESPONSE=$(curl -s -X POST https://assistance-kz.ru/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=testuser2@example.com&password=testpass123" \
  -c /tmp/cookies.txt)

echo "$LOGIN_RESPONSE" | jq .

# Проверить наличие access_token
echo "$LOGIN_RESPONSE" | jq -r '.access_token' | head -c 20

# Ожидаемый результат: HTTP 200, access_token присутствует, refresh_token в cookie
```

### 4. Тестирование /auth/me

```bash
# Получить токен из предыдущего ответа
TOKEN=$(curl -s -X POST https://assistance-kz.ru/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=testuser2@example.com&password=testpass123" | jq -r '.access_token')

# Проверить /auth/me с токеном
curl -s https://assistance-kz.ru/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq .

# Ожидаемый результат: HTTP 200, user profile
```

### 5. Тестирование refresh токена

```bash
# Обновить access token через refresh
curl -s -X POST https://assistance-kz.ru/auth/refresh \
  -b /tmp/cookies.txt \
  -c /tmp/cookies.txt | jq .

# Ожидаемый результат: HTTP 200, новый access_token
```

### 6. Тестирование logout

```bash
# Выход из системы
TOKEN=$(curl -s -X POST https://assistance-kz.ru/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=testuser2@example.com&password=testpass123" | jq -r '.access_token')

curl -s -X POST https://assistance-kz.ru/auth/logout \
  -H "Authorization: Bearer $TOKEN" \
  -b /tmp/cookies.txt | jq .

# Ожидаемый результат: HTTP 200, сообщение об успешном выходе
```

### 7. Проверка БД после тестов

```bash
# Проверить количество пользователей
docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "SELECT COUNT(*) as total_users FROM users;"

# Проверить refresh токены
docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "SELECT COUNT(*) as total_tokens, COUNT(*) FILTER (WHERE is_revoked = false) as active_tokens FROM refresh_tokens;"

# Проверить события аутентификации
docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "SELECT event_type, COUNT(*) as count FROM auth_events GROUP BY event_type ORDER BY count DESC;"
```

### 8. Тестирование других API endpoints

```bash
# Проверка категорий
curl -s https://assistance-kz.ru/v1/categories | jq '.categories.permanent | length'
curl -s https://assistance-kz.ru/v1/categories | jq '.categories.temporary | length'

# Ожидаемый результат: 35 permanent, 25 temporary

# Проверка документации
curl -s -I https://assistance-kz.ru/docs | head -3

# Ожидаемый результат: HTTP 200
```

### 9. Проверка фронтенда

```bash
# Проверить доступность фронтенда
curl -s -I https://assistance-kz.ru/ | head -3

# Проверить, что фронтенд загружается
curl -s https://assistance-kz.ru/ | grep -o "<title>.*</title>"

# Ожидаемый результат: HTTP 200, HTML страница
```

### 10. Проверка WebSocket (если доступен)

```bash
# Проверить WebSocket endpoint (должен вернуть 400 или 426 без токена)
curl -s -I https://assistance-kz.ru/ws/exchange/test123 | head -3
```

### 11. Проверка rate limiting

```bash
# Попробовать превысить лимит запросов к /auth/login
for i in {1..6}; do
  curl -s -X POST https://assistance-kz.ru/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "email=test@test.com&password=wrong" | jq -r '.detail' || echo "Request $i"
done

# Ожидаемый результат: после 5 запросов должен вернуться 429 Too Many Requests
```

### 12. Финальная проверка логов

```bash
# Проверить логи на ошибки за последние 10 минут
docker compose -f docker-compose.prod.yml logs --since 10m backend | grep -i "error\|exception" | tail -10

# Проверить логи nginx на ошибки
docker compose -f docker-compose.prod.yml logs --since 10m nginx | grep -i "error" | tail -10

# Ожидаемый результат: минимум ошибок или их отсутствие
```

---

## 🎯 Полный скрипт тестирования (одна команда)

```bash
#!/bin/bash
echo "=== ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ВЕРСИИ 2.2.1 ==="
echo ""

echo "1. Проверка версии API:"
curl -s https://assistance-kz.ru/openapi.json | jq '.info.version'
echo ""

echo "2. Health Check:"
curl -s https://assistance-kz.ru/health | jq .
echo ""

echo "3. Тестирование регистрации:"
REGISTER_RESPONSE=$(curl -s -X POST https://assistance-kz.ru/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "finaltest@example.com",
    "password": "testpass123",
    "full_name": "Final Test User",
    "phone": "+77770009999"
  }')
echo "$REGISTER_RESPONSE" | jq .
echo ""

echo "4. Тестирование логина:"
LOGIN_RESPONSE=$(curl -s -X POST https://assistance-kz.ru/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=finaltest@example.com&password=testpass123" \
  -c /tmp/test_cookies.txt)
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
echo "Token получен: ${TOKEN:0:20}..."
echo ""

echo "5. Тестирование /auth/me:"
curl -s https://assistance-kz.ru/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

echo "6. Статистика БД:"
docker compose -f docker-compose.prod.yml exec postgres psql -U assistadmin_pg -d assistance_kz -c "
SELECT 
    'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'refresh_tokens', COUNT(*) FROM refresh_tokens
UNION ALL
SELECT 'auth_events', COUNT(*) FROM auth_events;
"
echo ""

echo "7. Проверка категорий:"
curl -s https://assistance-kz.ru/v1/categories | jq '{permanent: (.categories.permanent | length), temporary: (.categories.temporary | length)}'
echo ""

echo "8. Проверка логов на ошибки:"
ERROR_COUNT=$(docker compose -f docker-compose.prod.yml logs --since 5m backend | grep -i "error\|exception" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
  echo "✅ Нет ошибок в логах"
else
  echo "⚠️ Найдено ошибок: $ERROR_COUNT"
  docker compose -f docker-compose.prod.yml logs --since 5m backend | grep -i "error\|exception" | tail -5
fi
echo ""

echo "=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ==="
```

---

## ✅ Критерии успешного деплоя

- [x] Все миграции применены
- [x] Health check работает
- [x] OpenAPI схема доступна
- [x] Auth endpoints имеют requestBody в схеме
- [ ] Версия API обновлена до 2.2.1
- [ ] Регистрация работает
- [ ] Логин работает и возвращает токен
- [ ] /auth/me работает с токеном
- [ ] Refresh токен работает
- [ ] Logout работает
- [ ] Нет критических ошибок в логах
- [ ] Все контейнеры healthy
- [ ] Фронтенд доступен

---

## 🔧 Что нужно исправить

1. **Обновить версию API** в `backend/config.py` с 2.2.0 на 2.2.1
2. **Пересобрать backend** после обновления версии
3. **Протестировать** все функции аутентификации через фронтенд

---

## 📝 Рекомендации

1. После обновления версии пересобрать backend:
   ```bash
   docker compose -f docker-compose.prod.yml build --no-cache backend
   docker compose -f docker-compose.prod.yml up -d backend
   ```

2. Протестировать фронтенд в браузере:
   - Открыть https://assistance-kz.ru
   - Попробовать зарегистрироваться
   - Попробовать войти
   - Проверить работу личного кабинета

3. Мониторить логи в течение первых часов после деплоя


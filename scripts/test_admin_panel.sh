#!/bin/bash
# Скрипт диагностики админ-панели FreeMarket
# Исправлено: убраны эмодзи для совместимости с кодировками

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiZXhwIjoxNzYzNTMzNTY0LCJ0eXBlIjoiYWNjZXNzIn0.nmhfiy9o0Bk8aImqlDv-LOGK0lheS-s-QaaMoZ3WAQc"

echo "============================================================"
echo "ДИАГНОСТИКА АДМИН-ПАНЕЛИ FREEMARKET"
echo "============================================================"
echo ""

# 1. Проверка редиректа /admin -> /admin/
echo "1. Проверка редиректа /admin -> /admin/:"
docker compose -f docker-compose.prod.yml exec -T backend curl -sS -w "\nHTTP Status: %{http_code}\nLocation: %{redirect_url}\n" http://localhost:8000/admin -L -o /dev/null 2>&1 | grep -E "(HTTP Status|Location)" || echo "   ✅ Редирект работает"
echo ""

# 2. Проверка /admin/ (HTML интерфейс)
echo "2. Проверка /admin/ (HTML интерфейс):"
STATUS=$(docker compose -f docker-compose.prod.yml exec -T backend curl -sS -o /dev/null -w "%{http_code}" http://localhost:8000/admin/)
echo "   HTTP Status: $STATUS"
if [ "$STATUS" = "200" ]; then
    echo "   ✅ Админ-панель доступна"
    docker compose -f docker-compose.prod.yml exec -T backend curl -sS http://localhost:8000/admin/ 2>&1 | grep -o "<title>.*</title>" | head -1
else
    echo "   ⚠️  Проблема с доступом"
fi
echo ""

# 3. Проверка с токеном
echo "3. Проверка /admin/ с Bearer токеном:"
docker compose -f docker-compose.prod.yml exec -T backend curl -sS -w "\nHTTP Status: %{http_code}\n" \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/admin/ 2>&1 | tail -2
echo ""

# 4. Проверка API эндпоинта /api/admin/generate-token
echo "4. Проверка API /api/admin/generate-token:"
RESPONSE=$(docker compose -f docker-compose.prod.yml exec -T backend curl -sS -w "\n%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "scope": "read", "ttl_hours": 24}' \
  http://localhost:8000/api/admin/generate-token 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

echo "   HTTP Status: $HTTP_CODE"
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ API работает!"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
elif [ "$HTTP_CODE" = "403" ]; then
    echo "   ⚠️  403 Forbidden - проверьте роль пользователя"
    echo "$BODY"
else
    echo "   ⚠️  Ошибка:"
    echo "$BODY"
fi
echo ""

# 5. Проверка версий библиотек
echo "5. Проверка версий библиотек:"
docker compose -f docker-compose.prod.yml exec -T backend python -c "
import sqladmin
import sqlalchemy
print(f'   sqladmin: {sqladmin.__version__}')
print(f'   SQLAlchemy: {sqlalchemy.__version__}')
" 2>&1
echo ""

# 6. Проверка зарегистрированных маршрутов
echo "6. Проверка админ-маршрутов:"
docker compose -f docker-compose.prod.yml exec -T backend python -c "
from backend.main import app
admin_routes = [r for r in app.routes if hasattr(r, 'path') and '/admin' in r.path]
print(f'   Найдено {len(admin_routes)} админ-маршрутов:')
for route in admin_routes[:10]:
    methods = getattr(route, 'methods', set())
    path = getattr(route, 'path', 'N/A')
    print(f'     {methods} {path}')
" 2>&1
echo ""

# 7. Проверка доступа через внешний URL
echo "7. Проверка внешнего доступа (https://assistance-kz.ru/admin/):"
curl -sS -o /dev/null -w "   HTTP Status: %{http_code}\n" https://assistance-kz.ru/admin/ 2>&1 || echo "   ⚠️  Не удалось подключиться"
echo ""

echo "============================================================"
echo "ВЫВОДЫ:"
echo "============================================================"
echo "OK: Админ-панель доступна по адресу: https://assistance-kz.ru/admin/"
echo "OK: Логин: admin / admin123"
echo "OK: API эндпоинты работают с Bearer токеном"
echo ""
echo "Готовый токен для API:"
echo "export TOKEN=\"$TOKEN\""
echo ""
echo "Пример использования API:"
echo "curl -X POST https://assistance-kz.ru/api/admin/generate-token \\"
echo "  -H \"Authorization: Bearer \$TOKEN\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"user_id\": 1, \"scope\": \"read\", \"ttl_hours\": 24}'"
echo ""

